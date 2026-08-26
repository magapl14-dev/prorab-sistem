from typing import List
from pydantic import BaseModel


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
