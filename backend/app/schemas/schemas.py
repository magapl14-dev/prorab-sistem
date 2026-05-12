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


class UserOut(BaseModel):
    id: UUID
    phone: str
    name: str
    role: str
    email: Optional[str] = None
    active: bool
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


class UploadUrlResponse(BaseModel):
    photo_id: UUID
    upload_url: str
    expires_in: int


class ConfirmUploadRequest(BaseModel):
    photo_id: UUID
    record_id: Optional[UUID] = None


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
