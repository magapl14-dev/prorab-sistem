import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id", ondelete="CASCADE"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("task_comments.id", ondelete="CASCADE"), nullable=True)
    s3_bucket = Column(String(200), nullable=False)
    s3_key = Column(String(500), nullable=False)
    thumb_key = Column(String(500), nullable=True)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_sec = Column(Integer, nullable=True)
    kind = Column(String(20), nullable=False, default="receipt")
    media_type = Column(String(20), nullable=False, default="image", server_default="image")
    is_confirmed = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    record = relationship("Record", back_populates="photos")
    task = relationship("Task", back_populates="attachments", foreign_keys=[task_id])
    comment = relationship("TaskComment", foreign_keys=[comment_id], overlaps="attachments")
    uploader = relationship("User", back_populates="photos")
