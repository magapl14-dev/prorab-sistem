from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: UUID
    s3_key: str
    thumb_key: Optional[str] = None
    url: str
    thumb_url: Optional[str] = None
    mime_type: str
    size_bytes: int
    kind: str
    media_type: str = "image"
    duration_sec: Optional[int] = None
    uploaded_at: datetime
    model_config = {"from_attributes": True}


class UploadUrlRequest(BaseModel):
    filename: str
    size: int
    mime_type: str
    kind: str = "receipt"
    media_type: str = "image"  # image | audio


class UploadUrlResponse(BaseModel):
    photo_id: UUID
    upload_url: str
    expires_in: int


class ConfirmUploadRequest(BaseModel):
    photo_id: UUID
    record_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    duration_sec: Optional[int] = None
