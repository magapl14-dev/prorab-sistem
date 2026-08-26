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
    if not users:
        return []

    user_ids = [u.id for u in users]
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    rec_filters = [Record.author_id.in_(user_ids), Record.deleted_at.is_(None)]
    if project_id:
        rec_filters.append(Record.project_id == project_id)
    if date_from:
        rec_filters.append(Record.operation_date >= date_from.date())
    if date_to:
        rec_filters.append(Record.operation_date <= date_to.date())
    rec_map: dict = {}
    rec_q = (
        select(
            Record.author_id,
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
        )
        .where(and_(*rec_filters))
        .group_by(Record.author_id)
    )
    for row in (await db.execute(rec_q)).all():
        rec_map[row[0]] = row[1:]

    created_f = [Task.created_by.in_(user_ids), Task.deleted_at.is_(None)]
    if project_id:
        created_f.append(Task.project_id == project_id)
    if date_from:
        created_f.append(Task.created_at >= date_from)
    if date_to:
        created_f.append(Task.created_at <= date_to)
    created_map = {
        uid: int(cnt or 0)
        for uid, cnt in (await db.execute(
            select(Task.created_by, func.count()).where(and_(*created_f)).group_by(Task.created_by)
        )).all()
    }

    done_f = [
        Task.completed_by.in_(user_ids),
        Task.deleted_at.is_(None),
        Task.status == "done",
    ]
    if project_id:
        done_f.append(Task.project_id == project_id)
    if date_from:
        done_f.append(Task.completed_at >= date_from)
    if date_to:
        done_f.append(Task.completed_at <= date_to)
    done_map: dict = {}
    last_task_map: dict = {}
    for uid, cnt, last in (await db.execute(
        select(Task.completed_by, func.count(), func.max(Task.completed_at))
        .where(and_(*done_f))
        .group_by(Task.completed_by)
    )).all():
        done_map[uid] = int(cnt or 0)
        last_task_map[uid] = last

    open_f = [
        TaskAssignee.user_id.in_(user_ids),
        Task.deleted_at.is_(None),
        Task.status.in_(["open", "in_progress"]),
    ]
    if project_id:
        open_f.append(Task.project_id == project_id)
    open_map = {
        uid: int(cnt or 0)
        for uid, cnt in (await db.execute(
            select(TaskAssignee.user_id, func.count())
            .join(Task, Task.id == TaskAssignee.task_id)
            .where(and_(*open_f))
            .group_by(TaskAssignee.user_id)
        )).all()
    }

    zeros = (0, 0, 0, 0, 0, 0, 0, 0, 0, None)
    rows = []
    for u in users:
        (
            rec_total, rec_today, rec_week,
            exp_sum, exp_cnt,
            cp_sum, cp_cnt,
            mp_sum, mp_cnt,
            last_rec_at,
        ) = rec_map.get(u.id, zeros)
        last_task_at = last_task_map.get(u.id)
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
            tasks_created=created_map.get(u.id, 0),
            tasks_assigned_open=open_map.get(u.id, 0),
            tasks_completed=done_map.get(u.id, 0),
            last_activity_at=last_activity,
        ))

    return rows
