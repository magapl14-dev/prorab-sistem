# Спека: S4 распил god-files бэкенда

**Путь:** рефакторинг

## Preserve

- HTTP URL `/api/v1/*` и JSON-тела ответов/запросов — без изменений.
- Импорты `from app.models.models import …` и `from app.schemas.schemas import …` работают (alembic, тесты, роутеры, скрипты).
- `Base.metadata` содержит те же таблицы, что до сплита.
- Тела списков (массив vs `{items}`) — как в S3.
- S1–S3 pytest зелёные.

## ADDED

- **FR-001** SQLAlchemy-модели живут в доменных модулях (`user`, `project`, `record`, `photo`, `master`, `task`, `catalog`); `models.py` — тонкий реэкспорт.
- **FR-002** Pydantic-схемы живут в доменных модулях; `schemas.py` — тонкий реэкспорт.
- **FR-003** Роутеры не меняют контракт. Общие хелперы не сливать, если сериализация сейчас разная (`records._photo_out` без `media_type`).

## Out of scope

- Распил `frontend/index.html` (S5).
- Смена URL, полей JSON, миграции БД.
- Новый слой сервисов «заодно».
- `earnings/all` N+1 (S3 out).

## Independent Test

`pytest`: импорт шимов видит все таблицы; S1–S3 suite зелёный.
