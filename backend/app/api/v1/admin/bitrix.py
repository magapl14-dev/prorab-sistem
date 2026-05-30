from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....core.database import get_db
from ....core.permissions import require_permission
from ....models.models import AppSetting, User
from ....schemas.schemas import BitrixSettingsOut, BitrixSettingsUpdate, BitrixTestResult
from ....services.bitrix import BitrixConfig, get_bitrix_config, test_connection

router = APIRouter(prefix="/admin", tags=["bitrix"])


async def _row(db: AsyncSession) -> AppSetting:
    row = (await db.execute(select(AppSetting).where(AppSetting.id == 1))).scalar_one_or_none()
    if not row:
        row = AppSetting(id=1, app_name="WELL DOM")
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


@router.get("/bitrix", response_model=BitrixSettingsOut)
async def get_bitrix_settings(
    admin: User = Depends(require_permission("branding", "view")),
    db: AsyncSession = Depends(get_db),
):
    row = await _row(db)
    return BitrixSettingsOut(
        enabled=bool(row.bitrix_enabled),
        domain=row.bitrix_domain,
        user_id=row.bitrix_user_id,
        has_webhook_key=bool(row.bitrix_webhook_key),
        default_responsible_id=row.bitrix_default_responsible_id,
        default_group_id=row.bitrix_default_group_id,
    )


@router.patch("/bitrix", response_model=BitrixSettingsOut)
async def update_bitrix_settings(
    data: BitrixSettingsUpdate,
    admin: User = Depends(require_permission("branding", "edit")),
    db: AsyncSession = Depends(get_db),
):
    row = await _row(db)
    if data.enabled is not None:
        row.bitrix_enabled = data.enabled
    if data.domain is not None:
        row.bitrix_domain = data.domain.strip() or None
    if data.user_id is not None:
        row.bitrix_user_id = data.user_id.strip() or None
    if data.webhook_key is not None:
        # пустая строка = очистить
        row.bitrix_webhook_key = data.webhook_key.strip() or None
    if data.default_responsible_id is not None:
        row.bitrix_default_responsible_id = data.default_responsible_id.strip() or None
    if data.default_group_id is not None:
        row.bitrix_default_group_id = data.default_group_id.strip() or None
    await db.commit()
    await db.refresh(row)
    return BitrixSettingsOut(
        enabled=bool(row.bitrix_enabled),
        domain=row.bitrix_domain,
        user_id=row.bitrix_user_id,
        has_webhook_key=bool(row.bitrix_webhook_key),
        default_responsible_id=row.bitrix_default_responsible_id,
        default_group_id=row.bitrix_default_group_id,
    )


@router.post("/bitrix/test", response_model=BitrixTestResult)
async def test_bitrix_connection(
    admin: User = Depends(require_permission("branding", "view")),
    db: AsyncSession = Depends(get_db),
):
    cfg = await get_bitrix_config(db)
    if not cfg or not (cfg.domain and cfg.user_id and cfg.webhook_key):
        return BitrixTestResult(ok=False, error="Заполните domain, user_id и webhook_key и сохраните настройки")
    res = await test_connection(cfg)
    return BitrixTestResult(ok=res["ok"], user_name=res.get("user_name"), error=res.get("error"))
