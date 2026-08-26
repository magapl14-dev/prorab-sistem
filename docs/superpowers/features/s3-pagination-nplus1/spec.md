# Спека: S3 пагинация и N+1

**Путь:** рефакторинг + узкий MODIFIED контракта (query-параметры)

## Preserve

- Тело GET `/masters`, `/tasks`, `/admin/users`, `/admin/analytics/users` — по-прежнему **массив**.
- Агрегаты мастера (total_paid, payments_count, rates) те же формулы.
- S1–S2 тесты зелёные.

## MODIFIED / ADDED

- **FR-001** `limit` (1…500, default 200) и `offset` на GET masters, tasks, admin/users.
- **FR-002** Заголовок `X-Total-Count` — полное число до среза.
- **FR-003** Список мастеров и аналитика пользователей не делают запрос в цикле на каждую строку.

## Independent Test

pytest: limit=1 режет массив; полный список при default; S1/S2 зелёные.
