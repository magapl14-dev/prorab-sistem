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
from ...models.models import User, Task, TaskAssignee, Project, UserProject, Photo, Dictionary, TaskComment
from ...schemas.schemas import (
    TaskOut, TaskCreate, TaskUpdate, TaskAssigneeBrief, TaskProjectBrief, PhotoOut, DictionaryOut,
    TaskCommentOut, TaskCommentCreate,
)
from ...services.s3 import public_url

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


@router.get("/_types", response_model=list[DictionaryOut])
async def list_task_types(
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Dictionary).where(Dictionary.kind == "task_type", Dictionary.active == True)
        .order_by(Dictionary.display_order, Dictionary.value)
    )).scalars().all()
    return rows


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


def _photo_brief(p: Photo) -> PhotoOut:
    return PhotoOut(
        id=p.id, s3_key=p.s3_key, thumb_key=p.thumb_key,
        url=public_url(p.s3_key),
        thumb_url=public_url(p.thumb_key) if p.thumb_key else None,
        mime_type=p.mime_type, size_bytes=p.size_bytes,
        kind=p.kind, media_type=p.media_type or "image",
        duration_sec=p.duration_sec,
        uploaded_at=p.uploaded_at,
    )


def _comment_out(c: TaskComment) -> TaskCommentOut:
    author = TaskAssigneeBrief(id=c.author.id, name=c.author.name) if c.author else None
    atts = [_photo_brief(p) for p in (c.attachments or []) if not p.deleted_at]
    return TaskCommentOut(id=c.id, text=c.text, author=author, attachments=atts, created_at=c.created_at)


def _task_out(t: Task, include_comments: bool = False) -> TaskOut:
    assignees = [TaskAssigneeBrief(id=a.user.id, name=a.user.name) for a in (t.assignees_link or []) if a.user]
    project = TaskProjectBrief(code=t.project.code, name=t.project.name) if t.project else None
    creator = TaskAssigneeBrief(id=t.creator.id, name=t.creator.name) if t.creator else None
    attachments = [_photo_brief(p) for p in (t.attachments or []) if not p.deleted_at]
    comments = []
    if include_comments:
        comments = [_comment_out(c) for c in sorted((t.comments or []), key=lambda x: x.created_at) if not c.deleted_at]
    return TaskOut(
        id=t.id, title=t.title, description=t.description, type=t.type, status=t.status,
        priority=t.priority, due_at=t.due_at,
        project=project, creator=creator, assignees=assignees, attachments=attachments,
        comments=comments,
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
            selectinload(Task.attachments),
        )
        .where(and_(*filters))
        .order_by(
            (Task.status == "done").asc(),
            Task.due_at.asc().nulls_last(),
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
            selectinload(Task.attachments),
            selectinload(Task.comments).selectinload(TaskComment.author),
            selectinload(Task.comments).selectinload(TaskComment.attachments),
        )
        .where(Task.id == task_id, Task.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(404)
    return _task_out(task, include_comments=True)


# ── Task comments ─────────────────────────────────────────────────────────────

@router.get("/{task_id}/comments", response_model=list[TaskCommentOut])
async def list_comments(
    task_id: UUID,
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(TaskComment)
        .options(selectinload(TaskComment.author), selectinload(TaskComment.attachments))
        .where(TaskComment.task_id == task_id, TaskComment.deleted_at.is_(None))
        .order_by(TaskComment.created_at)
    )).scalars().all()
    return [_comment_out(c) for c in rows]


@router.post("/{task_id}/comments", response_model=TaskCommentOut, status_code=201)
async def add_comment(
    task_id: UUID,
    data: TaskCommentCreate,
    user: User = Depends(require_permission("tasks", "view")),
    db: AsyncSession = Depends(get_db),
):
    # проверим, что задача существует
    task = (await db.execute(select(Task).where(Task.id == task_id, Task.deleted_at.is_(None)))).scalar_one_or_none()
    if not task:
        raise HTTPException(404)
    text = (data.text or "").strip() or None
    if not text and not data.attachment_ids:
        raise HTTPException(400, "Comment must have text or attachments")

    comment = TaskComment(task_id=task_id, author_id=user.id, text=text)
    db.add(comment)
    await db.flush()

    if data.attachment_ids:
        photos = (await db.execute(
            select(Photo).where(
                Photo.id.in_(data.attachment_ids),
                Photo.uploaded_by == user.id,
                Photo.is_confirmed == True,
                Photo.comment_id.is_(None),
                Photo.task_id.is_(None),
                Photo.record_id.is_(None),
                Photo.deleted_at.is_(None),
            )
        )).scalars().all()
        for p in photos:
            p.comment_id = comment.id

    await db.commit()
    fetched = (await db.execute(
        select(TaskComment)
        .options(selectinload(TaskComment.author), selectinload(TaskComment.attachments))
        .where(TaskComment.id == comment.id)
    )).scalar_one()
    return _comment_out(fetched)


@router.delete("/{task_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    task_id: UUID,
    comment_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (await db.execute(
        select(TaskComment).where(TaskComment.id == comment_id, TaskComment.task_id == task_id, TaskComment.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not comment:
        raise HTTPException(404)
    is_author = comment.author_id == user.id
    if not is_author:
        if not await has_permission(db, user.role, "tasks", "delete"):
            raise HTTPException(403, "Cannot delete others' comments")
    from datetime import datetime, timezone
    comment.deleted_at = datetime.now(timezone.utc)
    await db.commit()


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
        type=data.type or None,
        project_id=project.id if project else None,
        priority=data.priority,
        due_at=data.due_at,
        created_by=user.id,
        status="open",
    )
    db.add(task)
    await db.flush()

    for uid in (data.assignee_ids or []):
        db.add(TaskAssignee(task_id=task.id, user_id=uid))

    # привязать загруженные вложения
    if data.attachment_ids:
        photos = (await db.execute(
            select(Photo).where(
                Photo.id.in_(data.attachment_ids),
                Photo.uploaded_by == user.id,
                Photo.is_confirmed == True,
                Photo.task_id.is_(None),
                Photo.record_id.is_(None),
                Photo.deleted_at.is_(None),
            )
        )).scalars().all()
        for p in photos:
            p.task_id = task.id

    await db.commit()
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees_link).selectinload(TaskAssignee.user),
            selectinload(Task.attachments),
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
    if data.type is not None:
        task.type = data.type or None
    if data.project_code is not None:
        if data.project_code == "":
            task.project_id = None
        else:
            p = await _resolve_project(db, data.project_code)
            task.project_id = p.id if p else None
    if data.priority is not None:
        task.priority = data.priority or None
    if data.due_at is not None:
        task.due_at = data.due_at
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

    # добавить новые вложения (нельзя удалить чужие через эту запись)
    if data.attachment_ids:
        photos = (await db.execute(
            select(Photo).where(
                Photo.id.in_(data.attachment_ids),
                Photo.uploaded_by == user.id,
                Photo.is_confirmed == True,
                Photo.task_id.is_(None),
                Photo.record_id.is_(None),
                Photo.deleted_at.is_(None),
            )
        )).scalars().all()
        for p in photos:
            p.task_id = task.id

    await db.commit()
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.project),
            selectinload(Task.creator),
            selectinload(Task.assignees_link).selectinload(TaskAssignee.user),
            selectinload(Task.attachments),
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
