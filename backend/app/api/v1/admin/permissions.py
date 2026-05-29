from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....core.database import get_db
from ....core.deps import admin_only
from ....core.permissions import RESOURCES, ACTIONS
from ....models.models import RolePermission, User
from ....schemas.schemas import PermissionsMatrix, PermissionsBulkUpdate

router = APIRouter(prefix="/admin", tags=["permissions"])

ROLES = ["admin", "foreman", "client"]


@router.get("/permissions", response_model=PermissionsMatrix)
async def get_permissions(
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(RolePermission))).scalars().all()
    matrix: dict = {r: {res: {a: False for a in ACTIONS} for res in RESOURCES} for r in ROLES}
    for row in rows:
        if row.role in matrix and row.resource in matrix[row.role] and row.action in matrix[row.role][row.resource]:
            matrix[row.role][row.resource][row.action] = row.allowed
    # admin всегда все true в выдаче
    for res in RESOURCES:
        for a in ACTIONS:
            matrix["admin"][res][a] = True
    return PermissionsMatrix(roles=ROLES, resources=RESOURCES, actions=ACTIONS, matrix=matrix)


@router.patch("/permissions")
async def update_permissions(
    data: PermissionsBulkUpdate,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    for item in data.items:
        if item.role == "admin":
            continue  # admin неизменяем
        if item.role not in ROLES or item.resource not in RESOURCES or item.action not in ACTIONS:
            raise HTTPException(400, f"Unknown role/resource/action: {item.role}/{item.resource}/{item.action}")
        row = (await db.execute(
            select(RolePermission).where(
                RolePermission.role == item.role,
                RolePermission.resource == item.resource,
                RolePermission.action == item.action,
            )
        )).scalar_one_or_none()
        if row:
            row.allowed = item.allowed
        else:
            db.add(RolePermission(
                role=item.role, resource=item.resource, action=item.action, allowed=item.allowed,
            ))
    await db.commit()
    return {"ok": True, "updated": len(data.items)}
