from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ...core.database import get_db
from ...core.deps import current_user
from ...core.permissions import require_permission
from ...models.models import Master, Record, User
from ...schemas.schemas import MasterCreate, MasterUpdate, MasterOut

router = APIRouter(prefix="/masters", tags=["masters"])


async def _build_out(db: AsyncSession, m: Master) -> MasterOut:
    # агрегаты по master_payment записям
    rows = (await db.execute(
        select(
            func.coalesce(func.sum(Record.payment_amount), 0),
            func.count(Record.id),
            func.max(Record.operation_date),
        ).where(
            Record.master_id == m.id,
            Record.kind == "master_payment",
            Record.deleted_at.is_(None),
        )
    )).first()
    total = rows[0] or Decimal("0")
    cnt = rows[1] or 0
    last = rows[2]
    return MasterOut(
        id=m.id, name=m.name, phone=m.phone, specialty=m.specialty,
        default_rate=m.default_rate, color=m.color, notes=m.notes, active=m.active,
        total_paid=Decimal(str(total)),
        payments_count=cnt,
        last_paid_at=last,
        created_at=m.created_at,
    )


@router.get("", response_model=list[MasterOut])
async def list_masters(
    include_inactive: bool = False,
    user: User = Depends(require_permission("master_payments", "view")),
    db: AsyncSession = Depends(get_db),
):
    filters = [Master.deleted_at.is_(None)]
    if not include_inactive:
        filters.append(Master.active == True)
    rows = (await db.execute(
        select(Master).where(and_(*filters)).order_by(Master.name)
    )).scalars().all()
    return [await _build_out(db, m) for m in rows]


@router.get("/{master_id}", response_model=MasterOut)
async def get_master(
    master_id: UUID,
    user: User = Depends(require_permission("master_payments", "view")),
    db: AsyncSession = Depends(get_db),
):
    m = (await db.execute(
        select(Master).where(Master.id == master_id, Master.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not m:
        raise HTTPException(404)
    return await _build_out(db, m)


@router.post("", response_model=MasterOut, status_code=201)
async def create_master(
    data: MasterCreate,
    user: User = Depends(require_permission("master_payments", "create")),
    db: AsyncSession = Depends(get_db),
):
    name = data.name.strip()
    if not name:
        raise HTTPException(400, "name required")
    # Поиск дубля по точному имени (case-insensitive)
    existing = (await db.execute(
        select(Master).where(
            func.lower(Master.name) == name.lower(),
            Master.deleted_at.is_(None),
        )
    )).scalar_one_or_none()
    if existing:
        return await _build_out(db, existing)

    m = Master(
        name=name,
        phone=(data.phone or "").strip() or None,
        specialty=(data.specialty or "").strip() or None,
        default_rate=data.default_rate,
        color=data.color,
        notes=data.notes,
        active=True,
        created_by=user.id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return await _build_out(db, m)


@router.patch("/{master_id}", response_model=MasterOut)
async def update_master(
    master_id: UUID,
    data: MasterUpdate,
    user: User = Depends(require_permission("master_payments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    m = (await db.execute(
        select(Master).where(Master.id == master_id, Master.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not m:
        raise HTTPException(404)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(m, field, value)
    await db.commit()
    await db.refresh(m)
    return await _build_out(db, m)


@router.delete("/{master_id}", status_code=204)
async def delete_master(
    master_id: UUID,
    user: User = Depends(require_permission("master_payments", "delete")),
    db: AsyncSession = Depends(get_db),
):
    m = (await db.execute(
        select(Master).where(Master.id == master_id, Master.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not m:
        raise HTTPException(404)
    m.deleted_at = datetime.now(timezone.utc)
    m.active = False
    await db.commit()
