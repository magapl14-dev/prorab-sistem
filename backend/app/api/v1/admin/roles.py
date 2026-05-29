import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ....core.database import get_db
from ....core.permissions import RESOURCES, ACTIONS, require_permission
from ....models.models import Role, RolePermission, User
from ....schemas.schemas import RoleOut, RoleCreate

router = APIRouter(prefix="/admin", tags=["roles"])

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,49}$")


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    admin: User = Depends(require_permission("permissions", "view")),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(Role).order_by(Role.is_system.desc(), Role.id))).scalars().all()
    return rows


@router.post("/roles", response_model=RoleOut, status_code=201)
async def create_role(
    data: RoleCreate,
    admin: User = Depends(require_permission("permissions", "edit")),
    db: AsyncSession = Depends(get_db),
):
    name = data.name.strip().lower()
    label = data.label.strip()
    if not NAME_RE.match(name):
        raise HTTPException(400, "name must be lowercase latin/digits/underscore, start with letter, 2-50 chars")
    if not label:
        raise HTTPException(400, "label required")

    existing = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Role with this name already exists")

    role = Role(name=name, label=label, is_system=False)
    db.add(role)

    # засеять permission-строки (все false — админ сам выставит)
    for res in RESOURCES:
        for act in ACTIONS:
            db.add(RolePermission(role=name, resource=res, action=act, allowed=False))

    await db.commit()
    await db.refresh(role)
    return role


@router.delete("/roles/{name}", status_code=204)
async def delete_role(
    name: str,
    admin: User = Depends(require_permission("permissions", "edit")),
    db: AsyncSession = Depends(get_db),
):
    role = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Role not found")
    if role.is_system:
        raise HTTPException(400, "Cannot delete system role")

    # запретим если есть пользователи с этой ролью
    users_with_role = (await db.execute(
        select(User).where(User.role == name, User.deleted_at.is_(None))
    )).scalars().first()
    if users_with_role:
        raise HTTPException(409, "Role is assigned to users — reassign them first")

    # удалить и саму роль, и связанные permission-строки
    await db.execute(delete(RolePermission).where(RolePermission.role == name))
    await db.delete(role)
    await db.commit()
