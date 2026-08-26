from typing import Optional
from uuid import UUID
from pydantic import BaseModel


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
