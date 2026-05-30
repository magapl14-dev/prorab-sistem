import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger,
    Date, DateTime, Numeric, ForeignKey, Text,
    func, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    pin_hash = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # admin | foreman | client
    email = Column(String(200), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    bitrix_user_id = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project_links = relationship("UserProject", back_populates="user", foreign_keys="UserProject.user_id")
    records = relationship("Record", back_populates="author", foreign_keys="Record.author_id")
    photos = relationship("Photo", back_populates="uploader")


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


class Record(Base):
    __tablename__ = "records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    kind = Column(String(20), nullable=False)  # expense | master_payment | client_payment
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
    is_advance = Column(Boolean, default=False, nullable=False)  # only for client_payment
    master_id = Column(UUID(as_uuid=True), ForeignKey("masters.id"), nullable=True)  # для master_payment
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="records")
    author = relationship("User", back_populates="records", foreign_keys=[author_id])
    photos = relationship("Photo", back_populates="record", cascade="all, delete-orphan")


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
    kind = Column(String(20), nullable=False, default="receipt")  # receipt|photo|audio
    media_type = Column(String(20), nullable=False, default="image", server_default="image")  # image|audio
    is_confirmed = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    record = relationship("Record", back_populates="photos")
    task = relationship("Task", back_populates="attachments", foreign_keys=[task_id])
    comment = relationship("TaskComment", foreign_keys=[comment_id])
    uploader = relationship("User", back_populates="photos")


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
    kind = Column(String(30), nullable=False)  # type | category | master_payment_type
    value = Column(String(200), nullable=False)
    display_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("kind", "value", name="uq_dictionary_kind_value"),
    )


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    app_name = Column(String(100), nullable=False, default="WELL DOM")
    logo_url = Column(Text, nullable=True)
    favicon_url = Column(Text, nullable=True)
    photo_camera_only = Column(Boolean, nullable=False, default=False, server_default="false")
    primary_color = Column(String(20), nullable=True)
    # ── Bitrix24 integration ──
    bitrix_enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    bitrix_domain = Column(String(200), nullable=True)        # https://company.bitrix24.ru
    bitrix_user_id = Column(String(20), nullable=True)        # user_id для вебхука
    bitrix_webhook_key = Column(String(200), nullable=True)   # секретный ключ
    bitrix_default_responsible_id = Column(String(20), nullable=True)  # дефолтный исполнитель в Б24
    bitrix_default_group_id = Column(String(20), nullable=True)        # дефолтная группа
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    allowed = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("role", "resource", "action", name="uq_role_perm"),
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    label = Column(String(100), nullable=False)
    is_system = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="open", server_default="open")  # open|in_progress|done|cancelled
    priority = Column(String(20), nullable=True)  # low|normal|high
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    bitrix_task_id = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", foreign_keys=[project_id])
    creator = relationship("User", foreign_keys=[created_by])
    assignees_link = relationship("TaskAssignee", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("Photo", back_populates="task", foreign_keys="Photo.task_id")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


class Master(Base):
    __tablename__ = "masters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=True)
    specialty = Column(String(100), nullable=True)  # "сантехник", "электрик"...
    default_rate = Column(Numeric(12, 2), nullable=True)
    color = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("Task", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    attachments = relationship("Photo", foreign_keys="Photo.comment_id")


class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="assignees_link")
    user = relationship("User")
