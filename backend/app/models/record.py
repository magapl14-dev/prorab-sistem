import uuid
from sqlalchemy import (
    Column, String, Boolean, Date, DateTime, Numeric, ForeignKey, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..core.database import Base


class Record(Base):
    __tablename__ = "records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    kind = Column(String(20), nullable=False)
    operation_date = Column(Date, nullable=False)
    name = Column(String(500), nullable=True)
    type = Column(String(100), nullable=True)
    category = Column(String(200), nullable=True)
    comment = Column(Text, nullable=True)
    qty = Column(Numeric(10, 3), default=1)
    price = Column(Numeric(12, 2), nullable=True)
    sum_buy = Column(Numeric(14, 2), nullable=True)
    markup_pct_snapshot = Column(Numeric(5, 2), nullable=True)
    sum_sell = Column(Numeric(14, 2), nullable=True)
    commission = Column(Numeric(12, 2), default=0)
    rentier_gross = Column(Numeric(12, 2), default=0)
    rentier_share_snapshot = Column(Numeric(5, 2), nullable=True)
    kassa = Column(String(200), nullable=True)
    client_rep_name = Column(String(200), nullable=True)
    payment_amount = Column(Numeric(12, 2), nullable=True)
    payment_date = Column(Date, nullable=True)
    is_advance = Column(Boolean, default=False, nullable=False)
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id"), nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="records")
    author = relationship("User", back_populates="records", foreign_keys=[author_id])
    photos = relationship("Photo", back_populates="record", cascade="all, delete-orphan")
