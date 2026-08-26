import uuid
from sqlalchemy import (
    Column, String, Boolean, Date, DateTime, Numeric, ForeignKey, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(300), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    deadline = Column(Date, nullable=True)
    markup_pct = Column(Numeric(5, 2), default=15)
    foreman_rate_pct = Column(Numeric(5, 2), default=2.5)
    foreman_efficiency = Column(Numeric(5, 2), default=100)
    foreman_fixed = Column(Numeric(12, 2), default=0)
    rentier_foreman_share = Column(Numeric(5, 2), default=100)
    plan_total = Column(Numeric(14, 2), default=0)
    plan_monthly = Column(Numeric(14, 2), default=0)
    whatsapp_url = Column(Text, nullable=True)
    telegram_url = Column(Text, nullable=True)
    gsheet_id = Column(String(100), nullable=True)
    bitrix_group_id = Column(String(20), nullable=True)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user_links = relationship("UserProject", back_populates="project")
    records = relationship("Record", back_populates="project")


class UserProject(Base):
    __tablename__ = "user_projects"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True)
    role = Column(String(20), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="project_links", foreign_keys=[user_id])
    project = relationship("Project", back_populates="user_links")
    granter = relationship("User", foreign_keys=[granted_by])
