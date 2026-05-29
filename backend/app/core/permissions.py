from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .deps import current_user
from ..models.models import RolePermission, User


RESOURCES = [
    "expenses",
    "master_payments",
    "client_payments",
    "tasks",
    "dashboard",
    "reports",
    "photos",
    "users",
    "projects",
    "dictionaries",
    "branding",
    "permissions",
]
ACTIONS = ["view", "create", "edit", "delete"]


async def get_user_permissions(db: AsyncSession, role: str) -> dict:
    """Return {resource: [action, ...]} for the given role."""
    rows = (await db.execute(
        select(RolePermission).where(
            RolePermission.role == role, RolePermission.allowed == True
        )
    )).scalars().all()
    out: dict = {}
    for r in rows:
        out.setdefault(r.resource, []).append(r.action)
    return out


async def has_permission(db: AsyncSession, role: str, resource: str, action: str) -> bool:
    # admin всегда true (safety net — на случай если строки в БД удалили)
    if role == "admin":
        return True
    row = (await db.execute(
        select(RolePermission).where(
            RolePermission.role == role,
            RolePermission.resource == resource,
            RolePermission.action == action,
        )
    )).scalar_one_or_none()
    return bool(row and row.allowed)


def require_permission(resource: str, action: str):
    """FastAPI dependency: 403 if user lacks the permission."""
    async def _check(
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not await has_permission(db, user.role, resource, action):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Permission denied: {resource}.{action}",
            )
        return user
    return _check
