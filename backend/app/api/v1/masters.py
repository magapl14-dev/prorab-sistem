from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ...core.database import get_db
from ...core.deps import current_user
from ...core.permissions import require_permission
from ...models.models import Master, Record, User, Project
from ...schemas.schemas import MasterCreate, MasterUpdate, MasterOut

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
    project_code: Optional[str] = None,
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
    return [await _build_out(db, m, project_id) for m in rows]


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
