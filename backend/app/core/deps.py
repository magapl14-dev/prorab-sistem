from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from .database import get_db
from .redis import get_redis
from .security import decode_token
from ..models.models import User

bearer = HTTPBearer()


async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    if await redis.get(f"revoked:{token}"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token revoked")

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or disabled")

    return user


def require_role(*roles: str):
    async def _check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return _check


admin_only = require_role("admin")
foreman_or_admin = require_role("foreman", "admin")
