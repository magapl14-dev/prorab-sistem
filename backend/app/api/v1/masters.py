from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
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


async def _build_out(
    db: AsyncSession,
    m: Master,
    project_id: Optional[UUID] = None,
) -> MasterOut:
    # агрегаты по master_payment записям. Учитываем и записи без явного master_id,
    # если имя совпадает с именем мастера (миграционная совместимость: раньше
    # мастера были просто текстом в records.name, а после появления сущности
    # часть записей могла сохраниться с NULL master_id).
    filters = [
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
    # Когда задан project_id — сумма/счётчик/дата считаются только по этому проекту.
    # Так карточка мастера внутри конкретного объекта показывает сколько ему
    # выплачено на этом объекте, а не по всем объектам сразу.
    if project_id is not None:
        filters.append(Record.project_id == project_id)

    rows = (await db.execute(
        select(
            func.coalesce(func.sum(Record.payment_amount), 0),
            func.count(Record.id),
            func.max(Record.operation_date),
        ).where(and_(*filters))
    )).first()
    total = rows[0] or Decimal("0")
    cnt = rows[1] or 0
    last = rows[2]
    # подтягиваем прайс мастера
    rate_rows = (await db.execute(
        select(MasterRate).where(MasterRate.master_id == m.id).order_by(MasterRate.display_order, MasterRate.name)
    )).scalars().all()
    rates = [MasterRateOut.model_validate(r) for r in rate_rows]

    return MasterOut(
        id=m.id, name=m.name, phone=m.phone, specialty=m.specialty,
        default_rate=m.default_rate, rate_unit=m.rate_unit, color=m.color, notes=m.notes, active=m.active,
        total_paid=Decimal(str(total)),
        payments_count=cnt,
        last_paid_at=last,
        created_at=m.created_at,
        rates=rates,
    )


@router.get("", response_model=list[MasterOut])
async def list_masters(
    include_inactive: bool = False,
    project_code: Optional[str] = None,
    include_hidden: bool = False,   # админ-режим: показать всех вместе с скрытыми (для настройки)
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

    out = []
    for m in rows:
        item = await _build_out(db, m, project_id)
        # Прокидываем режим видимости в поле (Pydantic позволит extra в MasterOut? —
        # проще пометкой в notes-адаптере на фронте, но нам она нужна как отдельное поле).
        setattr(item, "visibility_mode", visibility_by_id.get(m.id))
        out.append(item)
    return out


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
