import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db, AsyncSessionLocal
from ...core.deps import current_user
from ...core.permissions import has_permission, require_permission
from ...core.config import settings
from ...models.models import User, Photo
from ...schemas.schemas import UploadUrlRequest, UploadUrlResponse, ConfirmUploadRequest, PhotoOut
from ...services.s3 import generate_presigned_put, create_thumbnail, public_url, delete_object, save_local

router = APIRouter(tags=["photos"])
_executor = ThreadPoolExecutor(max_workers=4)


async def _make_thumbnail(photo_id: UUID, s3_key: str):
    loop = asyncio.get_event_loop()
    thumb_key = await loop.run_in_executor(_executor, create_thumbnail, s3_key)
    if thumb_key:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Photo).where(Photo.id == photo_id))
            photo = res.scalar_one_or_none()
            if photo:
                photo.thumb_key = thumb_key
                await db.commit()


@router.post("/photos/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    data: UploadUrlRequest,
    user: User = Depends(require_permission("photos", "create")),
    db: AsyncSession = Depends(get_db),
):
    image_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    audio_types = {"audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/aac", "audio/wav"}
    media_type = data.media_type if data.media_type in ("image", "audio") else "image"
    allowed = image_types if media_type == "image" else audio_types
    if data.mime_type not in allowed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported {media_type} type: {data.mime_type}")
    max_bytes = 20 * 1024 * 1024 if media_type == "image" else 30 * 1024 * 1024
    if data.size > max_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Max file size {max_bytes // (1024*1024)} MB")

    s3_key, upload_url = generate_presigned_put(data.filename, data.mime_type, data.size)

    photo = Photo(
        s3_bucket=settings.s3_bucket if settings.storage_type == "s3" else "local",
        s3_key=s3_key,
        mime_type=data.mime_type,
        size_bytes=data.size,
        kind=data.kind,
        media_type=media_type,
        is_confirmed=False,
        uploaded_by=user.id,
    )
    db.add(photo)
    await db.commit()

    return UploadUrlResponse(photo_id=photo.id, upload_url=upload_url, expires_in=300)


@router.put("/photos/local-upload/{path:path}")
async def local_upload(path: str, request: Request):
    """Receive file upload for local storage (replaces S3 presigned PUT)."""
    if settings.storage_type != "local":
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    data = await request.body()
    save_local(path, data)
    return Response(status_code=200)


@router.post("/photos/confirm", response_model=PhotoOut)
async def confirm_upload(
    data: ConfirmUploadRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_permission("photos", "create")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Photo).where(Photo.id == data.photo_id, Photo.uploaded_by == user.id, Photo.deleted_at.is_(None))
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")

    photo.is_confirmed = True
    if data.record_id:
        photo.record_id = data.record_id
    if data.task_id:
        photo.task_id = data.task_id
    if data.comment_id:
        photo.comment_id = data.comment_id
    if data.duration_sec is not None:
        photo.duration_sec = data.duration_sec
    await db.commit()

    # генерим миниатюру только для изображений
    if photo.media_type == "image":
        background_tasks.add_task(asyncio.ensure_future, _make_thumbnail(photo.id, photo.s3_key))

    return PhotoOut(
        id=photo.id, s3_key=photo.s3_key, thumb_key=photo.thumb_key,
        url=public_url(photo.s3_key),
        thumb_url=public_url(photo.thumb_key) if photo.thumb_key else None,
        mime_type=photo.mime_type, size_bytes=photo.size_bytes,
        kind=photo.kind, media_type=photo.media_type,
        duration_sec=photo.duration_sec,
        uploaded_at=photo.uploaded_at,
    )


@router.delete("/photos/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Photo).where(Photo.id == photo_id, Photo.deleted_at.is_(None)))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # Своё всегда можно (если может загружать), чужое — нужен delete
    is_own = photo.uploaded_by == user.id
    if is_own:
        if not await has_permission(db, user.role, "photos", "create"):
            raise HTTPException(status.HTTP_403_FORBIDDEN)
    else:
        if not await has_permission(db, user.role, "photos", "delete"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot delete others' photos")

    photo.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    delete_object(photo.s3_key)
    if photo.thumb_key:
        delete_object(photo.thumb_key)
