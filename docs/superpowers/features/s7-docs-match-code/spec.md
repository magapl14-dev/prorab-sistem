# Спека: S7 документ = код

**Путь:** рефакторинг (документация)

## Preserve

- Код, URL, compose, Caddy, nginx unit — без изменений.
- Не внедрять replica/cache/Pub/Sub.

## ADDED

- **FR-001** `docs/architecture.md` описывает стек из репо: FastAPI, один PostgreSQL, Redis для JWT/PIN, PWA vanilla JS, Capacitor + sync-web.
- **FR-002** То, чего нет (read replica, WAL 6ч, кеш справочников, Pub/Sub) — секция «Не реализовано», не как текущий факт.
- **FR-003** README не утверждает replica и кеш агрегатов как существующие.

## Independent Test

pytest: README без «replica»/«реплик» как факта; architecture.md содержит «Не реализовано» и не выдаёт replica за работающую схему без отрицания.
