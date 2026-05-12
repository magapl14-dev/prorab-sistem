from datetime import datetime, timezone, date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.deps import current_user
from ...models.models import User, Project, Record, UserProject, Photo, Dictionary
from ...schemas.schemas import (
    RecordCreate, RecordUpdate, RecordOut, RecordListResponse, PhotoOut, DictionaryOut,
)
from ...services.earnings import calc_record_financials
from ...services.s3 import public_url

router = APIRouter(tags=["records"])


async def _get_project(code: str, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.code == code, Project.active == True, Project.deleted_at.is_(None))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    if user.role != "admin":
        up = await db.execute(
            select(UserProject).where(
                UserProject.user_id == user.id,
                UserProject.project_id == project.id,
                UserProject.revoked_at.is_(None),
            )
        )
        if not up.scalar_one_or_none():
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No access to this project")

    return project


def _photo_out(photo: Photo) -> PhotoOut:
    return PhotoOut(
        id=photo.id,
        s3_key=photo.s3_key,
        thumb_key=photo.thumb_key,
        url=public_url(photo.s3_key),
        thumb_url=public_url(photo.thumb_key) if photo.thumb_key else None,
        mime_type=photo.mime_type,
        size_bytes=photo.size_bytes,
        kind=photo.kind,
        uploaded_at=photo.uploaded_at,
    )


def _record_out(r: Record) -> RecordOut:
    photos = [_photo_out(p) for p in (r.photos or []) if not p.deleted_at]
    return RecordOut(
        id=r.id, kind=r.kind, operation_date=r.operation_date,
        name=r.name, type=r.type, category=r.category, kassa=r.kassa, comment=r.comment,
        qty=r.qty, price=r.price, sum_buy=r.sum_buy,
        markup_pct_snapshot=r.markup_pct_snapshot, sum_sell=r.sum_sell,
        commission=r.commission, rentier_gross=r.rentier_gross,
        client_rep_name=r.client_rep_name, payment_amount=r.payment_amount,
        payment_date=r.payment_date, is_advance=bool(r.is_advance),
        author=r.author, photos=photos, created_at=r.created_at,
    )


@router.get("/projects/{code}/records", response_model=RecordListResponse)
async def list_records(
    code: str,
    kind: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    author_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project(code, user, db)
    filters = [Record.project_id == project.id, Record.deleted_at.is_(None)]

    if user.role == "client":
        filters.append(Record.kind == "client_payment")
    elif kind:
        filters.append(Record.kind == kind)

    if type:
        filters.append(Record.type == type)
    if category:
        filters.append(Record.category == category)
    if author_id:
        filters.append(Record.author_id == author_id)
    if date_from:
        filters.append(Record.operation_date >= date_from)
    if date_to:
        filters.append(Record.operation_date <= date_to)
    if search:
        filters.append(or_(Record.name.ilike(f"%{search}%"), Record.comment.ilike(f"%{search}%")))

    total = (await db.execute(select(func.count()).select_from(Record).where(and_(*filters)))).scalar()
    rows = (await db.execute(
        select(Record)
        .options(selectinload(Record.author), selectinload(Record.photos))
        .where(and_(*filters))
        .order_by(Record.operation_date.desc(), Record.created_at.desc())
        .limit(limit).offset(offset)
    )).scalars().all()

    return RecordListResponse(items=[_record_out(r) for r in rows], total=total)


@router.post("/projects/{code}/records", response_model=RecordOut, status_code=201)
async def create_record(
    code: str,
    data: RecordCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Clients cannot create records")

    project = await _get_project(code, user, db)
    rec_dict = data.model_dump(exclude={"photo_ids"})
    rec_dict = calc_record_financials(rec_dict, project)

    record = Record(**rec_dict, project_id=project.id, author_id=user.id)
    db.add(record)
    await db.flush()

    if data.photo_ids:
        photos = (await db.execute(
            select(Photo).where(
                Photo.id.in_(data.photo_ids),
                Photo.uploaded_by == user.id,
                Photo.is_confirmed == True,
                Photo.record_id.is_(None),
                Photo.deleted_at.is_(None),
            )
        )).scalars().all()
        for p in photos:
            p.record_id = record.id

    await db.commit()
    result = await db.execute(
        select(Record)
        .options(selectinload(Record.author), selectinload(Record.photos))
        .where(Record.id == record.id)
    )
    return _record_out(result.scalar_one())


@router.get("/projects/{code}/records/{record_id}", response_model=RecordOut)
async def get_record(
    code: str, record_id: UUID,
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db),
):
    project = await _get_project(code, user, db)
    result = await db.execute(
        select(Record)
        .options(selectinload(Record.author), selectinload(Record.photos))
        .where(Record.id == record_id, Record.project_id == project.id, Record.deleted_at.is_(None))
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found")
    return _record_out(record)


@router.patch("/projects/{code}/records/{record_id}", response_model=RecordOut)
async def update_record(
    code: str, record_id: UUID, data: RecordUpdate,
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db),
):
    if user.role == "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    project = await _get_project(code, user, db)
    result = await db.execute(
        select(Record).where(Record.id == record_id, Record.project_id == project.id, Record.deleted_at.is_(None))
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role == "foreman" and record.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Can only edit your own records")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(record, field, value)

    if data.price is not None or data.qty is not None:
        updated = calc_record_financials(
            {"kind": record.kind, "qty": record.qty, "price": record.price}, project
        )
        for k in ("sum_buy", "sum_sell", "commission", "rentier_gross", "markup_pct_snapshot"):
            if k in updated:
                setattr(record, k, updated[k])

    await db.commit()
    result = await db.execute(
        select(Record)
        .options(selectinload(Record.author), selectinload(Record.photos))
        .where(Record.id == record.id)
    )
    return _record_out(result.scalar_one())


@router.delete("/projects/{code}/records/{record_id}", status_code=204)
async def delete_record(
    code: str, record_id: UUID,
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db),
):
    if user.role == "client":
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    project = await _get_project(code, user, db)
    result = await db.execute(
        select(Record).where(Record.id == record_id, Record.project_id == project.id, Record.deleted_at.is_(None))
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if user.role == "foreman" and record.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    record.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.get("/projects/{code}/dictionaries", response_model=list[DictionaryOut])
async def get_dictionaries(
    code: str,
    kind: Optional[str] = None,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(code, user, db)
    filters = [Dictionary.active == True]
    if kind:
        filters.append(Dictionary.kind == kind)
    rows = (await db.execute(
        select(Dictionary).where(and_(*filters)).order_by(Dictionary.kind, Dictionary.display_order, Dictionary.value)
    )).scalars().all()
    return rows
