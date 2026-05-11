from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ....core.database import get_db
from ....core.deps import admin_only
from ....models.models import User, Project, UserProject, Dictionary
from ....schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut, AssignUserRequest, DictionaryOut, DictionaryCreate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(admin: User = Depends(admin_only), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Project).where(Project.deleted_at.is_(None)).order_by(Project.name)
    )).scalars().all()
    return rows


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(
    data: ProjectCreate,
    admin: User = Depends(admin_only),
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
    admin: User = Depends(admin_only), db: AsyncSession = Depends(get_db),
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
    admin: User = Depends(admin_only), db: AsyncSession = Depends(get_db),
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
    admin: User = Depends(admin_only), db: AsyncSession = Depends(get_db),
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


# ── Dictionaries ──────────────────────────────────────────────────────────────

@router.get("/dictionaries", response_model=list[DictionaryOut])
async def list_dictionaries(admin: User = Depends(admin_only), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Dictionary).where(Dictionary.active == True).order_by(Dictionary.kind, Dictionary.display_order)
    )).scalars().all()
    return rows


@router.post("/dictionaries", response_model=DictionaryOut, status_code=201)
async def create_dictionary(
    data: DictionaryCreate,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    d = Dictionary(**data.model_dump(), created_by=admin.id)
    db.add(d)
    await db.commit()
    return d
