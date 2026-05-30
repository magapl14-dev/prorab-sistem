"""Bitrix24 REST API client (webhook-based).

Usage:
    cfg = await get_bitrix_config(db)
    if not cfg or not cfg.enabled:
        return
    res = await bitrix_call(cfg, "tasks.task.add", {"fields": {...}})

Note: Bitrix24 has per-call rate limits (~2 req/sec). Keep calls sparse.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.models import AppSetting


class BitrixError(Exception):
    """Raised on Bitrix24 API errors (network or business)."""


@dataclass
class BitrixConfig:
    enabled: bool
    domain: str
    user_id: str
    webhook_key: str
    default_responsible_id: Optional[str]
    default_group_id: Optional[str]

    @property
    def base_url(self) -> str:
        d = self.domain.rstrip("/")
        if not d.startswith("http"):
            d = "https://" + d
        return f"{d}/rest/{self.user_id}/{self.webhook_key}"


async def get_bitrix_config(db: AsyncSession) -> Optional[BitrixConfig]:
    row = (await db.execute(select(AppSetting).where(AppSetting.id == 1))).scalar_one_or_none()
    if not row:
        return None
    if not (row.bitrix_domain and row.bitrix_user_id and row.bitrix_webhook_key):
        return BitrixConfig(
            enabled=False,
            domain=row.bitrix_domain or "",
            user_id=row.bitrix_user_id or "",
            webhook_key=row.bitrix_webhook_key or "",
            default_responsible_id=row.bitrix_default_responsible_id,
            default_group_id=row.bitrix_default_group_id,
        )
    return BitrixConfig(
        enabled=bool(row.bitrix_enabled),
        domain=row.bitrix_domain,
        user_id=row.bitrix_user_id,
        webhook_key=row.bitrix_webhook_key,
        default_responsible_id=row.bitrix_default_responsible_id,
        default_group_id=row.bitrix_default_group_id,
    )


async def bitrix_call(cfg: BitrixConfig, method: str, params: Optional[dict] = None) -> Any:
    """Call any Bitrix24 REST method. Returns `result` payload on success."""
    url = f"{cfg.base_url}/{method}"
    payload = params or {}
    timeout = httpx.Timeout(20.0, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
    except httpx.HTTPError as e:
        raise BitrixError(f"Network error: {e}") from e

    if resp.status_code >= 500:
        raise BitrixError(f"Bitrix24 {resp.status_code}: {resp.text[:200]}")

    try:
        data = resp.json()
    except Exception:
        raise BitrixError(f"Non-JSON response ({resp.status_code}): {resp.text[:200]}")

    if "error" in data:
        # формат: {"error":"ERROR_CODE","error_description":"..."}
        raise BitrixError(f"{data.get('error')}: {data.get('error_description', '')}")

    return data.get("result")


async def test_connection(cfg: BitrixConfig) -> dict:
    """Light-weight ping: tries to get current Bitrix user via profile method.
    Returns {ok: bool, user_name?: str, error?: str}."""
    try:
        res = await bitrix_call(cfg, "profile")
        # profile returns {"ID":"1","NAME":"...","LAST_NAME":"...","EMAIL":"..."}
        name = ""
        if isinstance(res, dict):
            name = (res.get("NAME") or "") + " " + (res.get("LAST_NAME") or "")
        return {"ok": True, "user_name": name.strip() or "?", "raw": res}
    except BitrixError as e:
        return {"ok": False, "error": str(e)}


def _priority_to_bitrix(p: Optional[str]) -> str:
    # local: low|normal|high → bitrix: 0|1|2
    return {"low": "0", "high": "2"}.get(p or "normal", "1")


def _datetime_to_bitrix(dt) -> Optional[str]:
    # Bitrix24 принимает ISO 8601. У нас datetime с TZ.
    if not dt:
        return None
    return dt.isoformat()


def task_to_bitrix_fields(task, assignee_bitrix_id: Optional[str], cfg: BitrixConfig) -> dict:
    """Mapping local Task → Bitrix24 fields dict."""
    responsible = assignee_bitrix_id or cfg.default_responsible_id
    fields = {
        "TITLE": task.title,
        "DESCRIPTION": task.description or "",
        "PRIORITY": _priority_to_bitrix(task.priority),
    }
    if responsible:
        fields["RESPONSIBLE_ID"] = responsible
    if cfg.default_group_id:
        fields["GROUP_ID"] = cfg.default_group_id
    if task.due_at:
        fields["DEADLINE"] = _datetime_to_bitrix(task.due_at)
    return fields
