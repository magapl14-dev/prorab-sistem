# Proposal: s4-split-god-files

**Intent:** Разнести models/schemas по доменам; HTTP-контракт и импортные пути `models.models` / `schemas.schemas` сохранить.
**Зачем сейчас:** god-файлы блокируют безопасные правки S5+ и ревью.
**In:** доменные модули + тонкие шимы.
**Out:** смена URL, фронт, новый стек, унификация сериализации фото (records без media_type — Preserve).
**Capability:** backend-structure
**Upset-to-break:** alembic/тесты не видят таблицу после сплита.

## Preserve

- URL и JSON как сейчас.
- `from app.models.models import Base` (alembic).
- `from app.schemas.schemas import …` в роутерах.

