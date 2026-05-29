from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from ...core.deps import current_user
from ...core.permissions import has_permission, require_permission
from ...models.models import User, Project, UserProject
from ...schemas.schemas import EarningsOut, PlanOut
from ...services.earnings import calc_project_earnings, calc_plan, calc_period_stats, calc_monthly_breakdown, calc_chart14

router = APIRouter(tags=["earnings"])


async def _get_user_project(code: str, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.code == code, Project.active == True, Project.deleted_at.is_(None))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if user.role != "admin":
        up = (await db.execute(
            select(UserProject).where(
                UserProject.user_id == user.id,
                UserProject.project_id == project.id,
                UserProject.revoked_at.is_(None),
            )
        )).scalar_one_or_none()
        if not up:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No access")
    return project


@router.get("/projects/{code}/earnings", response_model=EarningsOut)
async def project_earnings(
    code: str,
    user: User = Depends(require_permission("dashboard", "view")),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(code, user, db)
    target_id = user.id if user.role == "foreman" else user.id
    data = await calc_project_earnings(db, project, target_id)
    return EarningsOut(**data)


@router.get("/earnings/all", response_model=list[EarningsOut])
async def all_earnings(
    user: User = Depends(require_permission("dashboard", "view")),
    db: AsyncSession = Depends(get_db),
):
    ups = (await db.execute(
        select(UserProject, Project)
        .join(Project)
        .where(
            UserProject.user_id == user.id,
            UserProject.revoked_at.is_(None),
            Project.active == True,
            Project.deleted_at.is_(None),
        )
    )).all()

    results = []
    for _, project in ups:
        data = await calc_project_earnings(db, project, user.id)
        results.append(EarningsOut(**data))
    return results


@router.get("/projects/{code}/period-stats")
async def period_stats(code: str, user: User = Depends(require_permission("dashboard", "view")), db: AsyncSession = Depends(get_db)):
    project = await _get_user_project(code, user, db)
    return await calc_period_stats(db, project, user.id)


@router.get("/projects/{code}/monthly")
async def monthly_breakdown(code: str, user: User = Depends(require_permission("dashboard", "view")), db: AsyncSession = Depends(get_db)):
    project = await _get_user_project(code, user, db)
    return await calc_monthly_breakdown(db, project, user.id)


@router.get("/projects/{code}/chart14")
async def chart14(code: str, user: User = Depends(require_permission("dashboard", "view")), db: AsyncSession = Depends(get_db)):
    project = await _get_user_project(code, user, db)
    return await calc_chart14(db, project, user.id)


@router.get("/projects/{code}/plan", response_model=PlanOut)
async def project_plan(
    code: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(code, user, db)
    data = await calc_plan(db, project)
    return PlanOut(**data)
