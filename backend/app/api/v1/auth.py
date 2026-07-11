from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from ...core.redis import get_redis
from ...core.security import verify_pin, hash_pin, create_access_token, create_refresh_token, decode_token, normalize_phone
from ...core.deps import current_user
from ...core.permissions import get_user_permissions
from ...core.config import settings
from ...models.models import User, UserProject, Project
from ...schemas.schemas import (
    LoginRequest, TokenResponse, RefreshRequest, ChangePinRequest,
    UserBrief, ProjectBrief,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    phone = normalize_phone(data.phone)

    ip = (request.client.host if request.client else "unknown")
    ip_key = f"login_ip:{ip}"
    ip_count = await redis.incr(ip_key)
    if ip_count == 1:
        await redis.expire(ip_key, 60)
    if ip_count > 10:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests")

    result = await db.execute(
        select(User).where(User.phone == phone, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        retry_after = int((user.locked_until - datetime.now(timezone.utc)).total_seconds())
        raise HTTPException(
            status.HTTP_423_LOCKED,
            detail={"error": "account_locked", "retry_after": retry_after},
        )

    if not verify_pin(data.pin, user.pin_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= settings.login_max_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(seconds=settings.login_lockout_seconds)
            user.failed_attempts = 0
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    await redis.setex(f"refresh:{refresh_token}", settings.jwt_refresh_ttl, str(user.id))

    ups = await db.execute(
        select(UserProject, Project)
        .join(Project, UserProject.project_id == Project.id)
        .where(
            UserProject.user_id == user.id,
            UserProject.revoked_at.is_(None),
            Project.active == True,
            Project.deleted_at.is_(None),
        )
    )
    projects = [
        ProjectBrief(
            id=up.project_id, code=p.code, name=p.name, role=up.role,
            markup_pct=p.markup_pct,
            foreman_rate_pct=p.foreman_rate_pct,
            rentier_foreman_share=p.rentier_foreman_share,
        )
        for up, p in ups.all()
    ]

    perms = await get_user_permissions(db, user.role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_ttl,
        user=UserBrief(id=user.id, name=user.name, role=user.role, projects=projects, permissions=perms),
    )


@router.post("/refresh")
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    stored = await redis.get(f"refresh:{data.refresh_token}")
    if not stored:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired or revoked")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return {
        "access_token": create_access_token(user.id, user.role),
        "expires_in": settings.jwt_access_ttl,
    }


@router.post("/logout")
async def logout(data: RefreshRequest, redis=Depends(get_redis)):
    await redis.delete(f"refresh:{data.refresh_token}")
    return {"ok": True}


@router.post("/change-pin")
async def change_pin(
    data: ChangePinRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_pin(data.old_pin, user.pin_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect current PIN")
    user.pin_hash = hash_pin(data.new_pin)
    await db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserBrief)
async def me(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    ups = await db.execute(
        select(UserProject, Project)
        .join(Project)
        .where(
            UserProject.user_id == user.id,
            UserProject.revoked_at.is_(None),
            Project.active == True,
            Project.deleted_at.is_(None),
        )
    )
    projects = [
        ProjectBrief(
            id=up.project_id, code=p.code, name=p.name, role=up.role,
            markup_pct=p.markup_pct,
            foreman_rate_pct=p.foreman_rate_pct,
            rentier_foreman_share=p.rentier_foreman_share,
        )
        for up, p in ups.all()
    ]
    perms = await get_user_permissions(db, user.role)
    return UserBrief(id=user.id, name=user.name, role=user.role, projects=projects, permissions=perms)
