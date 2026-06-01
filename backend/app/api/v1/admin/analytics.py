from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from ....core.database import get_db
from ....core.permissions import require_permission
from ....models.models import User, Record, Task, TaskAssignee, Project
from ....schemas.schemas import UserAnalyticsRow

router = APIRouter(prefix="/admin/analytics", tags=["admin", "analytics"])


@router.get("/users", response_model=list[UserAnalyticsRow])
async def users_analytics(
    project_code: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    admin: User = Depends(require_permission("users", "view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Аналитика по пользователям: кто что внёс.

    Возвращает по каждому активному пользователю:
    - суммы и количества записей по типам (expense / client_payment / master_payment)
    - количество задач (создал / на нём открытых / завершил)
    - дата последней активности (любая запись или завершённая задача)
    """
    project_id = None
    if project_code:
        p = (await db.execute(
            select(Project).where(Project.code == project_code, Project.deleted_at.is_(None))
        )).scalar_one_or_none()
        if p:
            project_id = p.id

    users = (await db.execute(
        select(User).where(User.deleted_at.is_(None)).order_by(User.name)
    )).scalars().all()

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    rows = []
    for u in users:
        # ── Records by kind ───────────────────────────────────────────────────
        rec_filters = [Record.author_id == u.id, Record.deleted_at.is_(None)]
        if project_id:
            rec_filters.append(Record.project_id == project_id)
        if date_from:
            rec_filters.append(Record.operation_date >= date_from.date())
        if date_to:
            rec_filters.append(Record.operation_date <= date_to.date())

        agg = (await db.execute(
            select(
                func.count(Record.id),
                func.sum(case((Record.operation_date >= today.date(), 1), else_=0)),
                func.sum(case((Record.operation_date >= week_ago.date(), 1), else_=0)),
                func.coalesce(func.sum(case((Record.kind == "expense", Record.sum_buy), else_=0)), 0),
                func.sum(case((Record.kind == "expense", 1), else_=0)),
                func.coalesce(func.sum(case((Record.kind == "client_payment", Record.payment_amount), else_=0)), 0),
                func.sum(case((Record.kind == "client_payment", 1), else_=0)),
                func.coalesce(func.sum(case((Record.kind == "master_payment", Record.payment_amount), else_=0)), 0),
                func.sum(case((Record.kind == "master_payment", 1), else_=0)),
                func.max(Record.created_at),
            ).where(and_(*rec_filters))
        )).first()

        (
            rec_total, rec_today, rec_week,
            exp_sum, exp_cnt,
            cp_sum, cp_cnt,
            mp_sum, mp_cnt,
            last_rec_at,
        ) = agg or (0, 0, 0, 0, 0, 0, 0, 0, 0, None)

        # ── Tasks ─────────────────────────────────────────────────────────────
        task_filters_created = [Task.created_by == u.id, Task.deleted_at.is_(None)]
        if project_id:
            task_filters_created.append(Task.project_id == project_id)
        if date_from:
            task_filters_created.append(Task.created_at >= date_from)
        if date_to:
            task_filters_created.append(Task.created_at <= date_to)

        tasks_created = (await db.execute(
            select(func.count()).select_from(Task).where(and_(*task_filters_created))
        )).scalar() or 0

        task_filters_completed = [Task.completed_by == u.id, Task.deleted_at.is_(None), Task.status == "done"]
        if project_id:
            task_filters_completed.append(Task.project_id == project_id)
        if date_from:
            task_filters_completed.append(Task.completed_at >= date_from)
        if date_to:
            task_filters_completed.append(Task.completed_at <= date_to)

        tasks_completed_row = (await db.execute(
            select(func.count(), func.max(Task.completed_at)).select_from(Task).where(and_(*task_filters_completed))
        )).first()
        tasks_completed = (tasks_completed_row[0] if tasks_completed_row else 0) or 0
        last_task_at = tasks_completed_row[1] if tasks_completed_row else None

        # tasks assigned to user and still open
        task_filters_open = [
            Task.id.in_(select(TaskAssignee.task_id).where(TaskAssignee.user_id == u.id)),
            Task.deleted_at.is_(None),
            Task.status.in_(["open", "in_progress"]),
        ]
        if project_id:
            task_filters_open.append(Task.project_id == project_id)

        tasks_open = (await db.execute(
            select(func.count()).select_from(Task).where(and_(*task_filters_open))
        )).scalar() or 0

        last_at_candidates = [x for x in (last_rec_at, last_task_at, u.last_login_at) if x is not None]
        last_activity = max(last_at_candidates) if last_at_candidates else None

        rows.append(UserAnalyticsRow(
            user_id=u.id,
            name=u.name,
            phone=u.phone,
            role=u.role,
            active=u.active,
            last_login_at=u.last_login_at,
            records_total=int(rec_total or 0),
            records_today=int(rec_today or 0),
            records_week=int(rec_week or 0),
            expenses_sum=Decimal(str(exp_sum or 0)),
            expenses_count=int(exp_cnt or 0),
            client_payments_sum=Decimal(str(cp_sum or 0)),
            client_payments_count=int(cp_cnt or 0),
            master_payments_sum=Decimal(str(mp_sum or 0)),
            master_payments_count=int(mp_cnt or 0),
            tasks_created=tasks_created,
            tasks_assigned_open=tasks_open,
            tasks_completed=tasks_completed,
            last_activity_at=last_activity,
        ))

    return rows
