from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from decimal import Decimal
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ...core.database import get_db
from ...core.deps import current_user
from ...core.permissions import require_permission
from ...models.models import Master, Record, User, Project, MasterProjectVisibility, MasterRate
from ...schemas.schemas import MasterCreate, MasterUpdate, MasterOut, MasterRateIn, MasterRateOut

router = APIRouter(prefix="/masters", tags=["masters"])


async def _resolve_project_id(db: AsyncSession, project_code: Optional[str]) -> Optional[UUID]:
    if not project_code:
        return None
    p = (await db.execute(
        select(Project).where(Project.code == project_code, Project.deleted_at.is_(None))
    )).scalar_one_or_none()
    return p.id if p else None


async def _payment_stats(
    db: AsyncSession,
    masters: list[Master],
    project_id: Optional[UUID],
) -> dict[UUID, tuple[Decimal, int, Optional[object]]]:
    stats: dict[UUID, tuple[Decimal, int, Optional[object]]] = {
        m.id: (Decimal("0"), 0, None) for m in masters
    }
    if not masters:
        return stats
    ids = [m.id for m in masters]
    name_to_id = {m.name.lower(): m.id for m in masters}

    f_id = [
        Record.kind == "master_payment",
        Record.deleted_at.is_(None),
        Record.master_id.in_(ids),
    ]
    if project_id is not None:
        f_id.append(Record.project_id == project_id)
    q1 = (
        select(
            Record.master_id,
            func.coalesce(func.sum(Record.payment_amount), 0),
            func.count(Record.id),
            func.max(Record.operation_date),
        )
        .where(and_(*f_id))
        .group_by(Record.master_id)
    )
    for mid, total, cnt, last in (await db.execute(q1)).all():
        stats[mid] = (Decimal(str(total or 0)), int(cnt or 0), last)

    names = list(name_to_id)
    f_name = [
        Record.kind == "master_payment",
        Record.deleted_at.is_(None),
        Record.master_id.is_(None),
        func.lower(Record.name).in_(names),
    ]
    if project_id is not None:
        f_name.append(Record.project_id == project_id)
    q2 = (
        select(
            func.lower(Record.name),
            func.coalesce(func.sum(Record.payment_amount), 0),
            func.count(Record.id),
            func.max(Record.operation_date),
        )
        .where(and_(*f_name))
        .group_by(func.lower(Record.name))
    )
    for nlower, total, cnt, last in (await db.execute(q2)).all():
        mid = name_to_id.get(nlower)
        if not mid:
            continue
        t0, c0, l0 = stats[mid]
        new_last = last if not l0 else (max([x for x in (l0, last) if x is not None]) if last else l0)
        stats[mid] = (t0 + Decimal(str(total or 0)), c0 + int(cnt or 0), new_last)
    return stats


async def _assemble_outs(
    db: AsyncSession,
    masters: list[Master],
    project_id: Optional[UUID] = None,
    visibility_by_id: Optional[dict] = None,
) -> list[MasterOut]:
    if not masters:
        return []
    stats = await _payment_stats(db, masters, project_id)
    ids = [m.id for m in masters]
    rate_rows = (
        await db.execute(
            select(MasterRate)
            .where(MasterRate.master_id.in_(ids))
            .order_by(MasterRate.display_order, MasterRate.name)
        )
    ).scalars().all()
    rates_by: dict = defaultdict(list)
    for r in rate_rows:
        rates_by[r.master_id].append(MasterRateOut.model_validate(r))
    vis = visibility_by_id or {}
    out = []
    for m in masters:
        total, cnt, last = stats[m.id]
        out.append(
            MasterOut(
                id=m.id, name=m.name, phone=m.phone, specialty=m.specialty,
                default_rate=m.default_rate, rate_unit=m.rate_unit, color=m.color,
                notes=m.notes, active=m.active,
                total_paid=total, payments_count=cnt, last_paid_at=last,
                created_at=m.created_at,
                visibility_mode=vis.get(m.id),
                rates=rates_by.get(m.id, []),
            )
        )
    return out


async def _build_out(
    db: AsyncSession,
    m: Master,
    project_id: Optional[UUID] = None,
) -> MasterOut:
    return (await _assemble_outs(db, [m], project_id))[0]


@router.get("", response_model=list[MasterOut])
async def list_masters(
    response: Response,
    include_inactive: bool = False,
    project_code: Optional[str] = None,
    include_hidden: bool = False,   # админ-режим: показать всех вместе с скрытыми (для настройки)
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_permission("master_payments", "view")),
    db: AsyncSession = Depends(get_db),
):
    filters = [Master.deleted_at.is_(None)]
    if not include_inactive:
        filters.append(Master.active == True)
    rows = (await db.execute(
        select(Master).where(and_(*filters)).order_by(Master.name)
    )).scalars().all()
    project_id = await _resolve_project_id(db, project_code)

    # Видимость по проекту:
    #   - если для проекта есть хоть один show — показываем ТОЛЬКО show'ов;
    #   - иначе — всех кроме hide.
    # include_hidden=true отключает фильтрацию — всё видим одним списком
    # (нужно чтобы админ мог настраивать чекбоксы).
    visibility_by_id: dict = {}
    if project_id is not None:
        vis_rows = (await db.execute(
            select(MasterProjectVisibility).where(MasterProjectVisibility.project_id == project_id)
        )).scalars().all()
        visibility_by_id = {v.master_id: v.mode for v in vis_rows}

        if not include_hidden:
            has_whitelist = any(mode == "show" for mode in visibility_by_id.values())
            if has_whitelist:
                rows = [m for m in rows if visibility_by_id.get(m.id) == "show"]
            else:
                rows = [m for m in rows if visibility_by_id.get(m.id) != "hide"]

    total = len(rows)
    rows = rows[offset: offset + limit]
    response.headers["X-Total-Count"] = str(total)
    return await _assemble_outs(db, rows, project_id, visibility_by_id)


@router.get("/{master_id}", response_model=MasterOut)
async def get_master(
    master_id: UUID,
    project_code: Optional[str] = None,
    user: User = Depends(require_permission("master_payments", "view")),
    db: AsyncSession = Depends(get_db),
):
    m = (await db.execute(
        select(Master).where(Master.id == master_id, Master.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not m:
        raise HTTPException(404)
    project_id = await _resolve_project_id(db, project_code)
    return await _build_out(db, m, project_id)


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
        rate_unit=(data.rate_unit or "").strip() or None,
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
    force: bool = False,
    user: User = Depends(require_permission("master_payments", "delete")),
    db: AsyncSession = Depends(get_db),
):
    m = (await db.execute(
        select(Master).where(Master.id == master_id, Master.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not m:
        raise HTTPException(404)

    # Проверяем нет ли за мастером выплат/авансов. Если есть — просим
    # подтверждение (force=true). Сами записи никогда не удаляются: даже
    # после удаления мастера они остаются в отчёте по проекту как
    # исторические данные.
    if not force:
        base_filter = [
            or_(
                Record.master_id == m.id,
                and_(
                    Record.master_id.is_(None),
                    func.lower(Record.name) == m.name.lower(),
                ),
            ),
            Record.kind == "master_payment",
            Record.deleted_at.is_(None),
        ]
        advances_row = (await db.execute(
            select(func.count(Record.id), func.coalesce(func.sum(Record.payment_amount), 0))
            .where(and_(*base_filter, Record.is_advance == True))
        )).first()
        payments_row = (await db.execute(
            select(func.count(Record.id), func.coalesce(func.sum(Record.payment_amount), 0))
            .where(and_(*base_filter, Record.is_advance == False))
        )).first()
        adv_cnt = int(advances_row[0] or 0)
        adv_sum = float(advances_row[1] or 0)
        pay_cnt = int(payments_row[0] or 0)
        pay_sum = float(payments_row[1] or 0)
        if adv_cnt or pay_cnt:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail={
                    "error": "has_history",
                    "master_name": m.name,
                    "advances_count": adv_cnt,
                    "advances_sum": adv_sum,
                    "payments_count": pay_cnt,
                    "payments_sum": pay_sum,
                    "message": (
                        "У мастера есть история выплат/авансов. Удаление скроет мастера, "
                        "но сами записи останутся в отчёте (историю задним числом не чистим)."
                    ),
                },
            )

    m.deleted_at = datetime.now(timezone.utc)
    m.active = False
    await db.commit()


class VisibilityIn(BaseModel):
    project_code: str
    mode: Optional[str] = None  # 'show' | 'hide' | None → сбросить в дефолт


@router.put("/{master_id}/visibility")
async def set_master_visibility(
    master_id: UUID,
    data: VisibilityIn,
    user: User = Depends(require_permission("master_payments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Задать per-project режим видимости мастера (`show` / `hide`), либо
    сбросить (mode=null) — тогда действует автоматика."""
    project_id = await _resolve_project_id(db, data.project_code)
    if project_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")

    if data.mode is not None and data.mode not in ("show", "hide"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "mode must be 'show' | 'hide' | null")

    existing = (await db.execute(
        select(MasterProjectVisibility).where(
            MasterProjectVisibility.master_id == master_id,
            MasterProjectVisibility.project_id == project_id,
        )
    )).scalar_one_or_none()

    if data.mode is None:
        if existing:
            await db.delete(existing)
            await db.commit()
        return {"ok": True, "mode": None}

    if existing:
        existing.mode = data.mode
        existing.set_by = user.id
    else:
        db.add(MasterProjectVisibility(
            master_id=master_id, project_id=project_id,
            mode=data.mode, set_by=user.id,
        ))
    await db.commit()
    return {"ok": True, "mode": data.mode}


# ── Прайс мастера (Master Rates) ────────────────────────────────────────────

@router.get("/{master_id}/rates", response_model=list[MasterRateOut])
async def list_master_rates(
    master_id: UUID,
    user: User = Depends(require_permission("master_payments", "view")),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(MasterRate).where(MasterRate.master_id == master_id)
        .order_by(MasterRate.display_order, MasterRate.name)
    )).scalars().all()
    return rows


@router.post("/{master_id}/rates", response_model=MasterRateOut, status_code=201)
async def add_master_rate(
    master_id: UUID,
    data: MasterRateIn,
    user: User = Depends(require_permission("master_payments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    m = (await db.execute(
        select(Master).where(Master.id == master_id, Master.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not m:
        raise HTTPException(404)
    r = MasterRate(
        master_id=master_id,
        name=data.name.strip(),
        amount=data.amount,
        unit=(data.unit or "").strip() or None,
        display_order=data.display_order,
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


@router.patch("/{master_id}/rates/{rate_id}", response_model=MasterRateOut)
async def update_master_rate(
    master_id: UUID,
    rate_id: UUID,
    data: MasterRateIn,
    user: User = Depends(require_permission("master_payments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    r = (await db.execute(
        select(MasterRate).where(MasterRate.id == rate_id, MasterRate.master_id == master_id)
    )).scalar_one_or_none()
    if not r:
        raise HTTPException(404)
    r.name = data.name.strip()
    r.amount = data.amount
    r.unit = (data.unit or "").strip() or None
    r.display_order = data.display_order
    await db.commit()
    await db.refresh(r)
    return r


@router.delete("/{master_id}/rates/{rate_id}", status_code=204)
async def delete_master_rate(
    master_id: UUID,
    rate_id: UUID,
    user: User = Depends(require_permission("master_payments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    r = (await db.execute(
        select(MasterRate).where(MasterRate.id == rate_id, MasterRate.master_id == master_id)
    )).scalar_one_or_none()
    if not r:
        raise HTTPException(404)
    await db.delete(r)
    await db.commit()
