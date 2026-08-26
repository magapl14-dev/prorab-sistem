# Список записей проекта

**Формат:** A
**ID:** TC-002
**Связь:** S1 Preserve records

## Таблица

| Действие | Ожидаемый результат |
|----------|---------------------|
| 1. Войти. 2. GET /projects/{code}/records с правом expenses.view. | 1. 200. 2. total ≥ 1. 3. В items есть запись с известным name. |
| 1. GET /projects/{code}/records без Authorization. | 1. 401. |
