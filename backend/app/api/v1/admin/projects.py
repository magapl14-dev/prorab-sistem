from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ....core.database import get_db
from ....core.permissions import require_permission
from ....models.models import User, Project, UserProject, Dictionary
from ....schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut, AssignUserRequest, DictionaryOut, DictionaryCreate, DictionaryUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(admin: User = Depends(require_permission("projects", "view")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Project).where(Project.deleted_at.is_(None)).order_by(Project.name)
    )).scalars().all()
    return rows


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(
    data: ProjectCreate,
    admin: User = Depends(require_permission("projects", "create")),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(Project).where(Project.code == data.code))).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Project code already exists")

    project = Project(**data.model_dump())
    db.add(project)
    await db.commit()
    return project


@router.patch("/projects/{code}", response_model=ProjectOut)
async def update_project(
    code: str, data: ProjectUpdate,
    admin: User = Depends(require_permission("projects", "edit")), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.code == code, Project.deleted_at.is_(None)))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    await db.commit()
    return project


@router.post("/projects/{code}/users", status_code=201)
async def assign_user(
    code: str, data: AssignUserRequest,
    admin: User = Depends(require_permission("projects", "edit")), db: AsyncSession = Depends(get_db),
):
    project = (await db.execute(select(Project).where(Project.code == code))).scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    # Upsert: if exists revoked, restore
    existing = (await db.execute(
        select(UserProject).where(UserProject.user_id == data.user_id, UserProject.project_id == project.id)
    )).scalar_one_or_none()

    if existing:
        existing.role = data.role
        existing.revoked_at = None
        existing.granted_by = admin.id
    else:
        db.add(UserProject(user_id=data.user_id, project_id=project.id, role=data.role, granted_by=admin.id))

    await db.commit()
    return {"ok": True}


@router.delete("/projects/{code}/users/{user_id}", status_code=204)
async def revoke_user(
    code: str, user_id: UUID,
    admin: User = Depends(require_permission("projects", "edit")), db: AsyncSession = Depends(get_db),
):
    project = (await db.execute(select(Project).where(Project.code == code))).scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    up = (await db.execute(
        select(UserProject).where(
            UserProject.user_id == user_id,
            UserProject.project_id == project.id,
            UserProject.revoked_at.is_(None),
        )
    )).scalar_one_or_none()
    if up:
        up.revoked_at = datetime.now(timezone.utc)
        await db.commit()


@router.patch("/projects/{code}/activate")
async def activate_project(
    code: str,
    admin: User = Depends(require_permission("projects", "edit")),
    db: AsyncSession = Depends(get_db),
):
    project = (await db.execute(select(Project).where(Project.code == code, Project.deleted_at.is_(None)))).scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    project.active = True
    await db.commit()
    return {"ok": True}


@router.patch("/projects/{code}/deactivate")
async def deactivate_project(
    code: str,
    admin: User = Depends(require_permission("projects", "edit")),
    db: AsyncSession = Depends(get_db),
):
    project = (await db.execute(select(Project).where(Project.code == code, Project.deleted_at.is_(None)))).scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    project.active = False
    await db.commit()
    return {"ok": True}


@router.delete("/projects/{code}", status_code=204)
async def delete_project(
    code: str,
    admin: User = Depends(require_permission("projects", "delete")),
    db: AsyncSession = Depends(get_db),
):
    project = (await db.execute(select(Project).where(Project.code == code, Project.deleted_at.is_(None)))).scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    project.deleted_at = datetime.now(timezone.utc)
    await db.commit()


# ── Dictionaries ──────────────────────────────────────────────────────────────

@router.get("/dictionaries", response_model=list[DictionaryOut])
async def list_dictionaries(admin: User = Depends(require_permission("dictionaries", "view")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Dictionary).where(Dictionary.active == True).order_by(Dictionary.kind, Dictionary.display_order)
    )).scalars().all()
    return rows


@router.post("/dictionaries", response_model=DictionaryOut, status_code=201)
async def create_dictionary(
    data: DictionaryCreate,
    admin: User = Depends(require_permission("dictionaries", "create")),
    db: AsyncSession = Depends(get_db),
):
    d = Dictionary(**data.model_dump(), created_by=admin.id)
    db.add(d)
    await db.commit()
    return d


@router.patch("/dictionaries/{dict_id}", response_model=DictionaryOut)
async def update_dictionary(
    dict_id: UUID,
    data: DictionaryUpdate,
    admin: User = Depends(require_permission("dictionaries", "edit")),
    db: AsyncSession = Depends(get_db),
):
    d = (await db.execute(select(Dictionary).where(Dictionary.id == dict_id, Dictionary.active == True))).scalar_one_or_none()
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(d, field, value)
    await db.commit()
    return d


@router.delete("/dictionaries/{dict_id}", status_code=204)
async def delete_dictionary(
    dict_id: UUID,
    admin: User = Depends(require_permission("dictionaries", "delete")),
    db: AsyncSession = Depends(get_db),
):
    d = (await db.execute(select(Dictionary).where(Dictionary.id == dict_id, Dictionary.active == True))).scalar_one_or_none()
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    d.active = False
    await db.commit()


# ── Google Sheets sync ────────────────────────────────────────────────────────

@router.post("/projects/{code}/sync-sheets")
async def sync_sheets(
    code: str,
    admin: User = Depends(require_permission("projects", "edit")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload
    from ....models.models import Record
    from ....services.gsheets import sync_project_to_sheet

    project = (await db.execute(
        select(Project).where(Project.code == code, Project.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not project.gsheet_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google Sheet ID not set for this project")

    records = (await db.execute(
        select(Record)
        .options(selectinload(Record.author))
        .where(Record.project_id == project.id, Record.deleted_at.is_(None))
        .order_by(Record.operation_date)
    )).scalars().all()

    try:
        result = await sync_project_to_sheet(project, list(records))
    except RuntimeError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Google Sheets error: {e}")

    return result
