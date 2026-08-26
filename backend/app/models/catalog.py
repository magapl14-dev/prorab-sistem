import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, DateTime, ForeignKey, Text,
    func, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Dictionary(Base):
    __tablename__ = "dictionaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind = Column(String(30), nullable=False)
    value = Column(String(200), nullable=False)
    display_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    __table_args__ = (UniqueConstraint("kind", "value", name="uq_dictionary_kind_value"),)


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    app_name = Column(String(100), nullable=False, default="WELL DOM")
    logo_url = Column(Text, nullable=True)
    favicon_url = Column(Text, nullable=True)
    photo_camera_only = Column(Boolean, nullable=False, default=False, server_default="false")
    primary_color = Column(String(20), nullable=True)
    bitrix_enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    bitrix_domain = Column(String(200), nullable=True)
    bitrix_user_id = Column(String(20), nullable=True)
    bitrix_webhook_key = Column(String(200), nullable=True)
    bitrix_default_responsible_id = Column(String(20), nullable=True)
    bitrix_default_group_id = Column(String(20), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
