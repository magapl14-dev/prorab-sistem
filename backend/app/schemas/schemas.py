from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


# ── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    phone: str
    pin: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePinRequest(BaseModel):
    old_pin: str
    new_pin: str


class ProjectBrief(BaseModel):
    id: UUID
    code: str
    name: str
    role: str
    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    id: UUID
    name: str
    role: str
    projects: List[ProjectBrief] = []
    permissions: dict = {}  # {resource: [action, ...]}
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserBrief


# ── Users ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    phone: str
    name: str
    pin: str
    role: str
    email: Optional[str] = None
    bitrix_user_id: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    phone: str
    name: str
    role: str
    email: Optional[str] = None
    active: bool
    bitrix_user_id: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Projects ─────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    code: str
    name: str
    markup_pct: Decimal = Decimal("15")
    foreman_rate_pct: Decimal = Decimal("2.5")
    foreman_efficiency: Decimal = Decimal("100")
    foreman_fixed: Decimal = Decimal("0")
    rentier_foreman_share: Decimal = Decimal("100")
    plan_total: Decimal = Decimal("0")
    plan_monthly: Decimal = Decimal("0")
    deadline: Optional[date] = None
    whatsapp_url: Optional[str] = None
    telegram_url: Optional[str] = None
    bitrix_group_id: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    markup_pct: Optional[Decimal] = None
    foreman_rate_pct: Optional[Decimal] = None
    foreman_efficiency: Optional[Decimal] = None
    foreman_fixed: Optional[Decimal] = None
    rentier_foreman_share: Optional[Decimal] = None
    plan_total: Optional[Decimal] = None
    plan_monthly: Optional[Decimal] = None
    deadline: Optional[date] = None
    whatsapp_url: Optional[str] = None
    telegram_url: Optional[str] = None
    gsheet_id: Optional[str] = None
    bitrix_group_id: Optional[str] = None
    active: Optional[bool] = None


class ProjectOut(BaseModel):
    id: UUID
    code: str
    name: str
    active: bool
    deadline: Optional[date] = None
    markup_pct: Decimal
    foreman_rate_pct: Decimal
    foreman_efficiency: Decimal
    foreman_fixed: Decimal
    rentier_foreman_share: Decimal
    plan_total: Decimal
    plan_monthly: Decimal
    whatsapp_url: Optional[str] = None
    telegram_url: Optional[str] = None
    gsheet_id: Optional[str] = None
    bitrix_group_id: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class AssignUserRequest(BaseModel):
    user_id: UUID
    role: str


# ── Records ──────────────────────────────────────────────────────────────────

class RecordCreate(BaseModel):
    kind: str
    operation_date: date
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    kassa: Optional[str] = None
    comment: Optional[str] = None
    qty: Decimal = Decimal("1")
    price: Optional[Decimal] = None
    client_rep_name: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    is_advance: bool = False
    rentier_gross: Optional[Decimal] = None
    photo_ids: List[UUID] = []


class RecordUpdate(BaseModel):
    operation_date: Optional[date] = None
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    kassa: Optional[str] = None
    comment: Optional[str] = None
    qty: Optional[Decimal] = None
    price: Optional[Decimal] = None
    client_rep_name: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    is_advance: Optional[bool] = None
    rentier_gross: Optional[Decimal] = None


class AuthorBrief(BaseModel):
    id: UUID
    name: str
    model_config = {"from_attributes": True}


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


class RecordOut(BaseModel):
    id: UUID
    kind: str
    operation_date: date
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    kassa: Optional[str] = None
    comment: Optional[str] = None
    qty: Optional[Decimal] = None
    price: Optional[Decimal] = None
    sum_buy: Optional[Decimal] = None
    markup_pct_snapshot: Optional[Decimal] = None
    sum_sell: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    rentier_gross: Optional[Decimal] = None
    client_rep_name: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    is_advance: bool = False
    author: Optional[AuthorBrief] = None
    photos: List[PhotoOut] = []
    created_at: datetime
    model_config = {"from_attributes": True}


class RecordListResponse(BaseModel):
    items: List[RecordOut]
    total: int


# ── Photos ───────────────────────────────────────────────────────────────────

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


# ── Earnings / Plan ───────────────────────────────────────────────────────────

class EarningsOut(BaseModel):
    project_code: str
    project_name: str
    total_expenses: Decimal
    commission: Decimal
    rentier_gross: Decimal
    rentier_foreman: Decimal
    fixed_monthly: Decimal
    total: Decimal


class PlanOut(BaseModel):
    project_code: str
    project_name: str
    plan_total: Decimal
    plan_monthly: Decimal
    spent_total: Decimal
    spent_monthly: Decimal
    progress_total_pct: Decimal
    progress_monthly_pct: Decimal


# ── Dictionaries ─────────────────────────────────────────────────────────────

class DictionaryOut(BaseModel):
    id: UUID
    kind: str
    value: str
    display_order: int
    model_config = {"from_attributes": True}


class DictionaryCreate(BaseModel):
    kind: str
    value: str
    display_order: int = 0


class DictionaryUpdate(BaseModel):
    value: Optional[str] = None
    display_order: Optional[int] = None


# ── App settings ─────────────────────────────────────────────────────────────

class AppSettingOut(BaseModel):
    app_name: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    photo_camera_only: bool = False
    primary_color: Optional[str] = None
    model_config = {"from_attributes": True}


class AppSettingUpdate(BaseModel):
    app_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    photo_camera_only: Optional[bool] = None
    primary_color: Optional[str] = None


# ── Bitrix24 integration settings ─────────────────────────────────────────────

class BitrixSettingsOut(BaseModel):
    enabled: bool
    domain: Optional[str] = None
    user_id: Optional[str] = None
    has_webhook_key: bool = False  # реальный ключ наружу не отдаём
    default_responsible_id: Optional[str] = None
    default_group_id: Optional[str] = None


class BitrixSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    domain: Optional[str] = None
    user_id: Optional[str] = None
    webhook_key: Optional[str] = None  # передавать только при обновлении
    default_responsible_id: Optional[str] = None
    default_group_id: Optional[str] = None


class BitrixTestResult(BaseModel):
    ok: bool
    user_name: Optional[str] = None
    error: Optional[str] = None


# ── Permissions ───────────────────────────────────────────────────────────────

class PermissionItem(BaseModel):
    role: str
    resource: str
    action: str
    allowed: bool


class PermissionsMatrix(BaseModel):
    roles: List[str]
    resources: List[str]
    actions: List[str]
    matrix: dict  # {role: {resource: {action: bool}}}


class PermissionsBulkUpdate(BaseModel):
    items: List[PermissionItem]


class RoleOut(BaseModel):
    name: str
    label: str
    is_system: bool
    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str
    label: str


# ── Tasks ─────────────────────────────────────────────────────────────────────

class TaskAssigneeBrief(BaseModel):
    id: UUID
    name: str
    model_config = {"from_attributes": True}


class TaskProjectBrief(BaseModel):
    code: str
    name: str
    model_config = {"from_attributes": True}


class TaskCommentOut(BaseModel):
    id: UUID
    text: Optional[str] = None
    author: Optional[TaskAssigneeBrief] = None
    attachments: List[PhotoOut] = []
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskCommentCreate(BaseModel):
    text: Optional[str] = None
    attachment_ids: List[UUID] = []


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    status: str
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    project: Optional[TaskProjectBrief] = None
    creator: Optional[TaskAssigneeBrief] = None
    assignees: List[TaskAssigneeBrief] = []
    attachments: List[PhotoOut] = []
    comments: List[TaskCommentOut] = []
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_code: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None  # low|normal|high
    due_at: Optional[datetime] = None
    assignee_ids: List[UUID] = []
    attachment_ids: List[UUID] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_code: Optional[str] = None  # передать "" чтобы убрать проект
    type: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    status: Optional[str] = None
    assignee_ids: Optional[List[UUID]] = None
    attachment_ids: Optional[List[UUID]] = None  # добавить новые приложения
