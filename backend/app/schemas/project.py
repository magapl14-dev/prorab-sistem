from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


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
