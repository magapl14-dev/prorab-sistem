from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel

from .photo import PhotoOut


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
    master_id: Optional[UUID] = None
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
