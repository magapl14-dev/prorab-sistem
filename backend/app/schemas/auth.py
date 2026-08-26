from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel


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
    # Экономика проекта — нужна фронту для расчётов (Отчёт: наценка, доля прораба
    # от раньтье). До этого поля не отдавались, из-за чего currentProject.markup_pct
    # был undefined и отчёт показывал «Наценка 0%».
    markup_pct: Optional[Decimal] = None
    foreman_rate_pct: Optional[Decimal] = None
    rentier_foreman_share: Optional[Decimal] = None
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
