from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....core.database import get_db
from ....core.deps import admin_only
from ....core.security import hash_pin, normalize_phone
from ....models.models import User
from ....schemas.schemas import UserCreate, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(admin: User = Depends(admin_only), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(User).where(User.deleted_at.is_(None)).order_by(User.name)
    )).scalars().all()
    return rows


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    data: UserCreate,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    if data.role not in ("admin", "foreman", "client"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")

    phone = normalize_phone(data.phone)
    existing = (await db.execute(
        select(User).where(User.phone == phone, User.deleted_at.is_(None))
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "User with this phone already exists")

    user = User(phone=phone, name=data.name, pin_hash=hash_pin(data.pin), role=data.role, email=data.email)
    db.add(user)
    await db.commit()
    return user


@router.patch("/users/{user_id}", status_code=200)
async def update_user(
    user_id: str,
    data: dict,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if "role" in data and data["role"] in ("admin", "foreman", "client"):
        user.role = data["role"]
    if "pin" in data and data["pin"]:
        user.pin_hash = hash_pin(str(data["pin"]))
    if "name" in data and data["name"]:
        user.name = data["name"]
    await db.commit()
    return {"ok": True}


@router.patch("/users/{user_id}/deactivate", status_code=200)
async def deactivate_user(
    user_id: str,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    user.active = False
    await db.commit()
    return {"ok": True}
