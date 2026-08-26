# Архитектура WELL DOM

Сверка с репозиторием, срез S7. Ниже — **как устроено в коде**, не целевая схема из старых черновиков.

Продукт: учёт для прорабов (закупки, выплаты мастерам, приходы клиента, задачи, фото, админка). Бренд в UI — WELL DOM.

## Стек (факт)

| Слой | Что в репо |
|------|------------|
| Клиент | Vanilla JS PWA: `frontend/index.html` (оболочка вкладок) + `frontend/css/app.css` + `frontend/js/app.js` + `frontend/api.js`. Не Vue. |
| API | FastAPI, Python 3.12, SQLAlchemy 2 async, Alembic, Pydantic v2. Префикс `/api/v1`. |
| Auth | JWT access + refresh, PIN (bcrypt), RBAC `RolePermission` / `Role`. |
| БД | **Один** PostgreSQL 16. Один `DATABASE_URL`. |
| Redis | Refresh-токены (`refresh:`), отзыв access (`revoked:`), счётчик попыток логина по IP. |
| Файлы | По умолчанию `storage_type=local` (диск + `PUT /api/v1/photos/local-upload/…`). MinIO/S3 — если явно `STORAGE_TYPE=s3` (presigned PUT). |
| Мобайл | Capacitor 6. `mobile/www` собирается `node mobile/sync-web.js` из `frontend/`. |
| Тесты | `cd backend && python -m pytest -q` (25 тестов: S1–S7 + PWA-кэш). Канон статуса — `STATUS.md` в корне. |

## Как ходят запросы

**Dev (`infra/docker-compose.yml`):** Postgres, Redis, MinIO, API на `:8000`. FastAPI сам раздаёт `frontend/` через StaticFiles.

**Prod-compose (`infra/docker-compose.prod.yml`):** Caddy 2 слушает 80/443, TLS, gzip. `/api/*` и `/health` → FastAPI; `/s3/*` → MinIO; остальное — файлы `/srv/frontend`.

**Альтернатива в репо (не compose):** `infra/nginx.conf` + `infra/welldom.service` (uvicorn `--workers 2` на 127.0.0.1:8000). Какой из двух вариантов крутится на конкретном хосте — смотреть деплой, не этот файл.

Docker-образ API: `uvicorn --reload`, один процесс. Пул SQLAlchemy в коде: `pool_size=20`.

## Данные и файлы

- Таблицы: users, projects, records, photos, masters, tasks, roles, dictionaries, app_settings и связанные (Alembic `001`…`017`).
- Источник истины — PostgreSQL. Google Sheets (`app/services/gsheets.py`) — выгрузка админом, write-only из БД.
- Bitrix24 и xAI (голос в формах) — опциональные настройки/ключи, не ядро учёта.

## Не реализовано

ADR: **не внедрять это «заодно»**, пока нет отдельной фичи и OK.

| Раньше architecture.md писал как факт | В коде |
|----------------------------------------|--------|
| PostgreSQL primary + **read replica**, отчёты с реплики | Один инстанс, один URL |
| Бэкапы каждые 6 часов, WAL / PITR | В репо не настроено |
| Redis кеширует справочники и агрегаты дашборда | Нет чтения кеша на этих путях |
| Redis Pub/Sub, уведомления в реальном времени | Нет |
| Клиент всегда грузит фото в S3 напрямую | Дефолт — local upload через API |

Смена этого списка — фича со спекой, не правка документа задним числом и не скрытый деплой replica.
