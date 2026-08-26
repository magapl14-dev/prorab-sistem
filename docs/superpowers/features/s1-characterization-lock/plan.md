# Plan: s1-characterization-lock

**Attack surface:** no (только тесты, без смены authz продукта)

## Foundational

- T001 [be] conftest: SQLite in-memory + FakeRedis, override get_db/get_redis
- T002 [be] фикстуры user/project/permission/record

## US1

- T003 [be] тесты: вход по PIN
- T004 [be] тесты: список записей проекта
- T005 [be] тесты: отказ без права view / без проекта
- T006 Makefile `test`

## Constitution Check

- [x] Не меняем публичный JSON API
- [x] Не трогаем прод-секреты
- [x] Имена тестов = что проверяется (craft-qa)
