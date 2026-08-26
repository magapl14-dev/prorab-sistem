# Research: prorab-refactor-epic

Карта репо 2026-08-26. Код не меняли.

## Decision: не монорефакторинг, а срезы + замок тестами

**Rationale:** нет `tests/`; CI только SSH-deploy; фронт — один `index.html` ~7k строк; architecture.md описывает replica/cache, которых в коде нет.

**Alternatives considered:**

- Переписать на Vue/Laravel «как регламент» — отвергнут: смена стека = фича+Decision, ломает Preserve.
- Один PR распила всего — отвергнут: >500 строк, нет suite.
- Сначала UI kit — отвергнут: без S1 регресс невидим.

## Факты (пути)

- Бэк: `backend/app/` FastAPI 3.12, Alembic 001–017, JWT+PIN+RBAC.
- Фронт: `frontend/index.html` (~7370) + `api.js` (362). Не Vue. PWA.
- Мобайл: Capacitor 6, `mobile/www` **отстаёт** от `frontend/` (~1.1k строк).
- Тестов нет. pytest в optional deps. Makefile без `test`.
- Секрет: `google-credentials.json` на диске (gitignore по имени). Дефолты JWT в compose.
- Дыры: `PUT /photos/local-upload` без auth; logout не отзывает access; N+1 masters/analytics; списки без пагинации кроме records.

## ASSUMPTION

- Prod на welldom05.duckdns.org живой; ломать UX нельзя.
- Стек остаётся FastAPI + ванильный JS + Capacitor, пока нет явного OK на замену.
