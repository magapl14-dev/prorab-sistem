"""
Голосовое заполнение форм через xAI Grok.

Логика: фронт записывает голосовое сообщение, отправляет сюда вместе с
контекстом (какая форма) и текущими значениями полей. Мы:
  1. Транскрибируем через grok-stt (OpenAI-совместимый /audio/transcriptions)
  2. Отдаём транскрипт LLM'у с system-prompt'ом под контекст (форматом ответа
     задаётся структурированный JSON, поля которого фронт распихает по input'ам)
  3. Возвращаем {transcript, fields, warnings}

Если ключ не настроен — 503; фронт по этому статусу переходит на браузерный STT.
"""
import json
import re
from typing import Optional, Any
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from ...core.config import settings
from ...core.deps import current_user
from ...models.models import User


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
async def ai_health():
    """Публичный статус: активен ли Grok. Фронт по нему рисует индикатор
    рядом с кнопкой 'Сказать всё голосом' (зелёный/красный)."""
    return {"active": bool(settings.xai_api_key)}


# ── Схемы полей для каждого контекста ───────────────────────────────────────
# Ключи в JSON, который вернёт LLM. Фронт по этим ключам расставит значения
# в конкретные input'ы (id'шники маппит сам).

CONTEXT_SCHEMAS: dict[str, dict[str, Any]] = {
    "expense": {
        "description": "закупка / расход материалов",
        "fields": {
            "name":           "название товара, например 'Цемент М500' или 'Плитка керамогранит'",
            "type":           "тип расхода одним словом ('Материал', 'Инструмент', 'Транспорт' и т.п.), если явно не сказан — null",
            "category":       "категория одним словом, если сказана — иначе null",
            "kassa":          "название кассы, из которой оплата ('Наличные', 'Карта', 'Основная' и т.п.) — если сказано, иначе null",
            "qty":            "количество (число), если не названо — 1",
            "price":          "цена за единицу в рублях (число), если названа общая сумма без цены за штуку — null",
            "sum_buy":        "общая сумма закупки в рублях (число), если названа только она (например 'на 3500') — заполни её, а qty поставь 1",
            "comment":        "любые пояснения, которые не влезли в другие поля",
            "rentier_gross":  "если сказано про откат/скидку от поставщика — сумма в рублях, иначе null",
        },
    },
    "master_payment": {
        "description": "выплата мастеру",
        "fields": {
            "master_name":    "имя мастера (например 'Иван' или 'Асхаб-каменщик')",
            "payment_amount": "сумма выплаты в рублях (число)",
            "pay_type":       "тип выплаты: 'salary' (зарплата), 'advance' (аванс), 'bonus' (премия), 'debt' (возврат долга). Если явно не назван — 'salary'.",
            "comment":        "пояснения не для остальных полей",
            "rentier_gross":  "если сказано про раньтье / удержание — сумма в рублях, иначе null",
        },
    },
    "client_payment": {
        "description": "оплата клиента",
        "fields": {
            "rep_name":       "имя представителя клиента, если названо",
            "payment_amount": "сумма в рублях (число)",
            "is_advance":     "true если это аванс, false если основная оплата. Если непонятно — false.",
            "comment":        "пояснения",
        },
    },
    "task": {
        "description": "задача бригадиру / рабочему",
        "fields": {
            "name":            "короткое название задачи (одна строка, суть)",
            "description":     "подробное описание — что именно надо сделать",
            "assignee_names":  "массив имён исполнителей (например ['Иван', 'Асхаб']). Если не названы — []",
            "type":            "тип задачи одним словом ('монтаж', 'ремонт', 'закупка', 'проверка', 'сдача'), null если не понятно",
            "priority":        "приоритет: 'low', 'medium', 'high' или 'urgent'. По умолчанию 'medium'.",
            "due_at":          "срок ISO-формат 'YYYY-MM-DDTHH:MM' (московское время). 'на завтра к 10:00' → следующий день 10:00. Если срок не назван — null.",
        },
    },
}


def _system_prompt(context: str, current: dict, extras: dict) -> str:
    schema = CONTEXT_SCHEMAS.get(context)
    if not schema:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown context: {context}")
    fields_desc = "\n".join(f'  - "{k}": {v}' for k, v in schema["fields"].items())
    now_note = extras.get("now_iso") or ""
    tz_note = extras.get("timezone") or "Europe/Moscow"
    return (
        f"Ты помогаешь строительному прорабу заполнять форму: {schema['description']}.\n"
        f"На входе — транскрипт голосового сообщения на русском (возможны опечатки, разговорные обороты).\n"
        f"Твоя задача — вернуть СТРОГО JSON с полями:\n{fields_desc}\n\n"
        f"Правила:\n"
        f"- Если поле не упомянуто в речи — ставь null (не выдумывай).\n"
        f"- Числа возвращай как числа, а не строки (без пробелов, без символа ₽).\n"
        f"- Если сумма произнесена словами ('три с половиной тысячи') — переведи в число (3500).\n"
        f"- Не добавляй никаких других ключей кроме перечисленных.\n"
        f"- Текущее время сервера: {now_note}, часовой пояс {tz_note}.\n"
        f"- Уже заполненные пользователем поля не перебивай, если из речи явно не следует замена:\n"
        f"  {json.dumps(current, ensure_ascii=False)}\n"
        f"Возвращай ТОЛЬКО JSON, без пояснений."
    )


async def _grok_transcribe(client: httpx.AsyncClient, audio_bytes: bytes, filename: str) -> str:
    files = {"file": (filename, audio_bytes, "application/octet-stream")}
    data = {"model": settings.xai_stt_model, "response_format": "text"}
    r = await client.post(
        f"{settings.xai_base_url}/audio/transcriptions",
        files=files, data=data,
        headers={"Authorization": f"Bearer {settings.xai_api_key}"},
        timeout=60.0,
    )
    r.raise_for_status()
    # response_format=text → тело это уже строка
    return r.text.strip() if r.headers.get("content-type", "").startswith("text/") else r.json().get("text", "")


async def _grok_parse(client: httpx.AsyncClient, transcript: str, sys_prompt: str) -> dict:
    payload = {
        "model": settings.xai_llm_model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": transcript},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }
    r = await client.post(
        f"{settings.xai_base_url}/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {settings.xai_api_key}"},
        timeout=60.0,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    # Иногда LLM оборачивает JSON в ```json ... ``` — снимем на всякий случай
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "LLM did not return JSON")
    return json.loads(m.group(0))


@router.post("/voice-fill")
async def voice_fill(
    audio: UploadFile = File(...),
    context: str = Form(...),
    current_json: str = Form("{}"),
    user: User = Depends(current_user),
):
    if not settings.xai_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "xai_not_configured")

    if context not in CONTEXT_SCHEMAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown context: {context}")

    try:
        current = json.loads(current_json) if current_json else {}
    except Exception:
        current = {}

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty audio")

    from datetime import datetime, timezone
    extras = {"now_iso": datetime.now(timezone.utc).isoformat(timespec="seconds"), "timezone": "Europe/Moscow"}
    sys_prompt = _system_prompt(context, current, extras)

    async with httpx.AsyncClient() as client:
        try:
            transcript = await _grok_transcribe(client, audio_bytes, audio.filename or "voice.m4a")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"stt_failed: {e.response.status_code}")
        if not transcript:
            return {"transcript": "", "fields": {}, "warnings": ["empty transcript"]}
        try:
            fields = await _grok_parse(client, transcript, sys_prompt)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"llm_failed: {e.response.status_code}")

    return {"transcript": transcript, "fields": fields, "warnings": []}
