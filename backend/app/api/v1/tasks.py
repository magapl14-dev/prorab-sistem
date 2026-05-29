from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.deps import current_user
from ...core.permissions import has_permission, require_permission
from ...models.models import User, Task, TaskAssignee, Project, UserProject
from ...schemas.schemas import TaskOut, TaskCreate, TaskUpdate, TaskAssigneeBrief, TaskProjectBrief

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/_users", response_model=list[TaskAssigneeBrief])
async def list_assignable_users(
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Список активных пользователей для назначения исполнителями."""
    rows = (await db.execute(
        select(User).where(User.deleted_at.is_(None), User.active == True).order_by(User.name)
    )).scalars().all()
    return [TaskAssigneeBrief(id=u.id, name=u.name) for u in rows]


@router.get("/_projects", response_model=list[TaskProjectBrief])
async def list_task_projects(
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Доступные проекты для привязки задачи."""
    if user.role == "admin":
        rows = (await db.execute(
            select(Project).where(Project.deleted_at.is_(None), Project.active == True).order_by(Project.name)
        )).scalars().all()
    else:
        rows = (await db.execute(
            select(Project)
            .join(UserProject, UserProject.project_id == Project.id)
            .where(
                UserProject.user_id == user.id,
                UserProject.revoked_at.is_(None),
                Project.deleted_at.is_(None),
                Project.active == True,
            )
            .order_by(Project.name)
        )).scalars().all()
    return [TaskProjectBrief(code=p.code, name=p.name) for p in rows]


def _task_out(t: Task) -> TaskOut:
    assignees = [TaskAssigneeBrief(id=a.user.id, name=a.user.name) for a in (t.assignees_link or []) if a.user]
    project = TaskProjectBrief(code=t.project.code, name=t.project.name) if t.project else None
    creator = TaskAssigneeBrief(id=t.creator.id, name=t.creator.name) if t.creator else None
    return TaskOut(
        id=t.id, title=t.title, description=t.description, status=t.status,
        priority=t.priority, due_date=t.due_date,
        project=project, creator=creator, assignees=assignees,
        completed_at=t.completed_at, created_at=t.created_at,
    )


async def _user_project_ids(db: AsyncSession, user: User) -> set:
    if user.role == "admin":
        return None  # все проекты
    rows = (await db.execute(
        select(UserProject.project_id).where(
            UserProject.user_id == user.id,
            UserProject.revoked_at.is_(None),
        )
    )).scalars().all()
    return set(rows)


async def _resolve_project(db: AsyncSession, code: Optional[str]) -> Optional[Project]:
    if not code:
        return None
    p = (await db.execute(
        select(Project).where(Project.code == code, Project.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(404, f"Project {code} not found")
    return p


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    project_code: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    assignee: Optional[str] = None,  # 'me' or user UUID
    creator: Optional[str] = None,   # 'me' or user UUID
    include_done: bool = True,
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    filters = [Task.deleted_at.is_(None)]
    # ограничить видимость: видны задачи (1) без проекта или (2) в проектах где есть доступ или (3) куда назначен
    project_ids = await _user_project_ids(db, user)
    if project_ids is not None:  # не админ
        visibility = or_(
            Task.project_id.is_(None),
            Task.project_id.in_(project_ids) if project_ids else False,
            Task.id.in_(select(TaskAssignee.task_id).where(TaskAssignee.user_id == user.id)),
            Task.created_by == user.id,
        )
        filters.append(visibility)

    if project_code:
        if project_code == "none":
            filters.append(Task.project_id.is_(None))
        else:
            p = await _resolve_project(db, project_code)
            filters.append(Task.project_id == p.id)

    if status_filter:
        filters.append(Task.status == status_filter)
    elif not include_done:
        filters.append(Task.status.in_(["open", "in_progress"]))

    if assignee:
        uid = user.id if assignee == "me" else UUID(assignee)
        filters.append(Task.id.in_(select(TaskAssignee.task_id).where(TaskAssignee.user_id == uid)))
    if creator:
        uid = user.id if creator == "me" else UUID(creator)
        filters.append(Task.created_by == uid)

    rows = (await db.execute(
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees_link).selectinload(TaskAssignee.user),
        )
        .where(and_(*filters))
        .order_by(
            (Task.status == "done").asc(),
            Task.due_date.asc().nulls_last(),
            Task.created_at.desc(),
        )
    )).scalars().all()
    return [_task_out(t) for t in rows]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: UUID,
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    task = (await db.execute(
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees_link).selectinload(TaskAssignee.user),
        )
        .where(Task.id == task_id, Task.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(404)
    return _task_out(task)


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    data: TaskCreate,
    user: User = Depends(require_permission("tasks", "create")),
    db: AsyncSession = Depends(get_db),
):
    project = await _resolve_project(db, data.project_code)
    if data.priority and data.priority not in ("low", "normal", "high"):
        raise HTTPException(400, "Invalid priority")

    task = Task(
        title=data.title.strip(),
        description=data.description,
        project_id=project.id if project else None,
        priority=data.priority,
        due_date=data.due_date,
        created_by=user.id,
        status="open",
    )
    db.add(task)
    await db.flush()

    for uid in (data.assignee_ids or []):
        db.add(TaskAssignee(task_id=task.id, user_id=uid))

    await db.commit()
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees_link).selectinload(TaskAssignee.user),
        )
        .where(Task.id == task.id)
    )
    return _task_out(result.scalar_one())


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    task = (await db.execute(
        select(Task)
        .options(selectinload(Task.assignees_link))
        .where(Task.id == task_id, Task.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(404)

    # Своё (создатель или назначенец) — можно если есть create; чужое — нужен edit
    is_creator = task.created_by == user.id
    is_assignee = any(a.user_id == user.id for a in (task.assignees_link or []))
    is_own = is_creator or is_assignee
    if is_own:
        if not await has_permission(db, user.role, "tasks", "create"):
            raise HTTPException(403)
    else:
        if not await has_permission(db, user.role, "tasks", "edit"):
            raise HTTPException(403, "Cannot edit others' tasks")

    if data.title is not None:
        task.title = data.title.strip()
    if data.description is not None:
        task.description = data.description
    if data.project_code is not None:
        if data.project_code == "":
            task.project_id = None
        else:
            p = await _resolve_project(db, data.project_code)
            task.project_id = p.id if p else None
    if data.priority is not None:
        task.priority = data.priority or None
    if data.due_date is not None:
        task.due_date = data.due_date
    if data.status is not None:
        if data.status not in ("open", "in_progress", "done", "cancelled"):
            raise HTTPException(400, "Invalid status")
        task.status = data.status
        if data.status == "done":
            task.completed_at = datetime.now(timezone.utc)
            task.completed_by = user.id
        else:
            task.completed_at = None
            task.completed_by = None

    if data.assignee_ids is not None:
        # переписать список назначенцев
        existing = {a.user_id for a in (task.assignees_link or [])}
        new_set = set(data.assignee_ids)
        to_remove = existing - new_set
        to_add = new_set - existing
        for a in list(task.assignees_link or []):
            if a.user_id in to_remove:
                await db.delete(a)
        for uid in to_add:
            db.add(TaskAssignee(task_id=task.id, user_id=uid))

    await db.commit()
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees_link).selectinload(TaskAssignee.user),
        )
        .where(Task.id == task.id)
    )
    return _task_out(result.scalar_one())


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    task = (await db.execute(
        select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(404)
    is_creator = task.created_by == user.id
    if is_creator:
        if not await has_permission(db, user.role, "tasks", "create"):
            raise HTTPException(403)
    else:
        if not await has_permission(db, user.role, "tasks", "delete"):
            raise HTTPException(403, "Cannot delete others' tasks")
    task.deleted_at = datetime.now(timezone.utc)
    await db.commit()
