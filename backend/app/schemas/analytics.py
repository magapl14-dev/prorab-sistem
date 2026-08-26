from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class UserAnalyticsRow(BaseModel):
    user_id: UUID
    name: str
    phone: str
    role: str
    active: bool
    last_login_at: Optional[datetime] = None
    records_total: int = 0
    records_today: int = 0
    records_week: int = 0
    expenses_sum: Decimal = Decimal("0")
    expenses_count: int = 0
    client_payments_sum: Decimal = Decimal("0")
    client_payments_count: int = 0
    master_payments_sum: Decimal = Decimal("0")
    master_payments_count: int = 0
    tasks_created: int = 0
    tasks_assigned_open: int = 0
    tasks_completed: int = 0
    last_activity_at: Optional[datetime] = None
