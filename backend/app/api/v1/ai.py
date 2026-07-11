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
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db

logger = logging.getLogger("welldom.ai")

from ...core.config import settings
from ...core.deps import current_user
from ...models.models import User, Dictionary


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
    now_moscow = extras.get("now_moscow", "")
    task_types = extras.get("task_types") or []

    extras_rules = []
    if context == "task":
        # Перечислим известные типы, чтобы Grok выбирал из них, а не выдумывал.
        enum = ", ".join(f'"{t}"' for t in task_types) if task_types else '"Общая"'
        extras_rules.append(
            f'- Поле "type": строго один из [{enum}]. По умолчанию (когда явно не сказано ни '
            f'«звонок», «встреча», «монтаж», «закупка», «проверка», «сдача») — "Общая".'
        )
        extras_rules.append(
            f'- Поле "due_at": возвращай строку "YYYY-MM-DDTHH:MM" в московском времени (без Z, '
            f'без секунд). "завтра" — следующий день, "сегодня к 18" — сегодня 18:00, если '
            f'сказано «утром» — 09:00, «днём» — 14:00, «вечером» — 19:00, «ночью» — 22:00. '
            f'Если ни срок, ни день не названы — null.'
        )
        extras_rules.append(
            f'- Поле "priority": "urgent" на «срочно/немедленно», "high" на «важно/быстро», '
            f'"low" на «когда будет время», ВО ВСЕХ ОСТАЛЬНЫХ СЛУЧАЯХ (в т.ч. если ничего '
            f'про срочность не сказано) — "medium". Никогда не возвращай null здесь.'
        )
        known_users = extras.get("known_users") or []
        if known_users:
            users_enum = ", ".join(f'"{n}"' for n in known_users)
            extras_rules.append(
                f'- Поле "assignee_names": массив имён из списка [{users_enum}]. Если в речи '
                f'имя названо в другом падеже («Анзору», «Ивана», «Асхабу») — приведи к тому '
                f'написанию, что в списке (именительный падеж). Возможны сокращения: если сказано '
                f'просто имя, а в списке «Иван Петров» — верни «Иван Петров». Если имени в списке '
                f'нет — не выдумывай, оставь пустой массив []. Если сказано «мне», «на себя» — '
                f'тоже []; исполнителя-создателя подставит фронт сам.'
            )
    extras_block = "\n".join(extras_rules) + ("\n" if extras_rules else "")

    return (
        f"Ты помогаешь строительному прорабу заполнять форму: {schema['description']}.\n"
        f"На входе — транскрипт голосового сообщения на русском (возможны опечатки, разговорные обороты).\n"
        f"Твоя задача — вернуть СТРОГО JSON с полями:\n{fields_desc}\n\n"
        f"Общие правила:\n"
        f"- Если поле не упомянуто в речи — ставь null (не выдумывай), КРОМЕ полей с явно заданным дефолтом ниже.\n"
        f"- Числа возвращай как числа, а не строки (без пробелов, без символа ₽).\n"
        f"- Если сумма произнесена словами ('три с половиной тысячи') — переведи в число (3500).\n"
        f"- Не добавляй никаких других ключей кроме перечисленных.\n"
        f"- Текущее московское время: {now_moscow} (Europe/Moscow, UTC+3).\n"
        f"{extras_block}"
        f"- Уже заполненные пользователем поля не перебивай, если из речи явно не следует замена:\n"
        f"  {json.dumps(current, ensure_ascii=False)}\n"
        f"Возвращай ТОЛЬКО JSON, без пояснений."
    )


async def _grok_transcribe(client: httpx.AsyncClient, audio_bytes: bytes, filename: str) -> str:
    # xAI STT endpoint: POST https://api.x.ai/v1/stt, multipart form.
    # Ответ — JSON с полем `text`.
    files = {"file": (filename, audio_bytes, "application/octet-stream")}
    data = {"model": settings.xai_stt_model, "format": "json", "language": "ru"}
    r = await client.post(
        f"{settings.xai_base_url}/stt",
        files=files, data=data,
        headers={"Authorization": f"Bearer {settings.xai_api_key}"},
        timeout=60.0,
    )
    r.raise_for_status()
    try:
        return (r.json().get("text") or "").strip()
    except Exception:
        return r.text.strip()


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
    db: AsyncSession = Depends(get_db),
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

    # Московское время в формате YYYY-MM-DDTHH:MM (без секунд, без Z) —
    # чтобы Grok мог его сопоставить с "завтра", "сегодня к 18" и т.п.
    now_moscow_dt = datetime.now(timezone.utc) + timedelta(hours=3)
    extras: dict = {"now_moscow": now_moscow_dt.strftime("%Y-%m-%dT%H:%M")}

    # Для задач подтянем актуальные типы из справочника, чтобы Grok не
    # выдумывал левых и всегда попадал в существующую опцию.
    if context == "task":
        rows = (await db.execute(
            select(Dictionary).where(Dictionary.kind == "task_type", Dictionary.active == True)
        )).scalars().all()
        types = [r.value for r in rows if r.value]
        # Гарантируем что "Общая" есть в списке — используем как дефолт.
        if "Общая" not in types:
            types.insert(0, "Общая")
        extras["task_types"] = types
        # Известные исполнители — Grok должен возвращать имена ровно как в
        # системе (в именительном падеже), чтобы фронт их нашёл сходу.
        users_rows = (await db.execute(
            select(User).where(User.deleted_at.is_(None), User.active == True).order_by(User.name)
        )).scalars().all()
        extras["known_users"] = [u.name for u in users_rows if u.name]

    sys_prompt = _system_prompt(context, current, extras)

    async with httpx.AsyncClient() as client:
        try:
            transcript = await _grok_transcribe(client, audio_bytes, audio.filename or "voice.m4a")
        except httpx.HTTPStatusError as e:
            body = e.response.text[:400]
            logger.error("STT failed %s: %s", e.response.status_code, body)
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail={"stage": "stt", "status": e.response.status_code, "body": body},
            )
        except Exception as e:
            logger.exception("STT unexpected error")
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail={"stage": "stt", "error": str(e)})

        if not transcript:
            return {"transcript": "", "fields": {}, "warnings": ["empty transcript"]}
        try:
            fields = await _grok_parse(client, transcript, sys_prompt)
        except httpx.HTTPStatusError as e:
            body = e.response.text[:400]
            logger.error("LLM failed %s: %s", e.response.status_code, body)
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail={"stage": "llm", "status": e.response.status_code, "body": body, "transcript": transcript},
            )
        except Exception as e:
            logger.exception("LLM unexpected error")
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail={"stage": "llm", "error": str(e), "transcript": transcript})

    return {"transcript": transcript, "fields": fields, "warnings": []}
