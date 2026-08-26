import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Numeric, ForeignKey, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from ..core.database import Base


class Master(Base):
    __tablename__ = "masters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=True)
    specialty = Column(String(100), nullable=True)
    default_rate = Column(Numeric(12, 2), nullable=True)
    rate_unit = Column(String(20), nullable=True)
    color = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class MasterRate(Base):
    __tablename__ = "master_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(20), nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MasterProjectVisibility(Base):
    __tablename__ = "master_project_visibility"

    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    mode = Column(String(10), nullable=False)
    set_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    set_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
