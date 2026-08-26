from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class MasterCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    default_rate: Optional[Decimal] = None
    rate_unit: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None


class MasterUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    default_rate: Optional[Decimal] = None
    rate_unit: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class MasterRateOut(BaseModel):
    id: UUID
    name: str
    amount: Decimal
    unit: Optional[str] = None
    display_order: int = 0
    model_config = {"from_attributes": True}


class MasterRateIn(BaseModel):
    name: str
    amount: Decimal
    unit: Optional[str] = None
    display_order: int = 0


class MasterOut(BaseModel):
    id: UUID
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    default_rate: Optional[Decimal] = None
    rate_unit: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    active: bool
    total_paid: Decimal = Decimal("0")
    payments_count: int = 0
    last_paid_at: Optional[date] = None
    created_at: datetime
    visibility_mode: Optional[str] = None  # 'show' | 'hide' | null
    rates: List[MasterRateOut] = []
    model_config = {"from_attributes": True}
