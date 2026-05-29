from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from ...core.permissions import require_permission
from ...models.models import AppSetting, User
from ...schemas.schemas import AppSettingOut, AppSettingUpdate

router = APIRouter(tags=["settings"])


async def _get_or_create(db: AsyncSession) -> AppSetting:
    row = (await db.execute(select(AppSetting).where(AppSetting.id == 1))).scalar_one_or_none()
    if not row:
        row = AppSetting(id=1, app_name="WELL DOM")
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


@router.get("/settings", response_model=AppSettingOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await _get_or_create(db)


@router.patch("/admin/settings", response_model=AppSettingOut)
async def update_settings(
    data: AppSettingUpdate,
    admin: User = Depends(require_permission("branding", "edit")),
    db: AsyncSession = Depends(get_db),
):
    row = await _get_or_create(db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row
