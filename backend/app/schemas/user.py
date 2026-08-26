from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


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
