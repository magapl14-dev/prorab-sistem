# Статус WELL DOM / prorab-sistem

**Читать это первым** при новом запуске агента или сессии. Архитектура кода — [`docs/architecture.md`](docs/architecture.md). Не переписывать продукт целиком.

**Дата сверки:** 2026-08-26  
**Ветка:** `main` → `origin/main` (`https://github.com/magapl14-dev/prorab-sistem`)  
**Прод:** https://welldom05.duckdns.org — выкатывается сам при `git push origin main` (Actions `Deploy to VPS`: pull → pip → alembic → `systemctl restart prorab-sistem`)  
**Тесты:** `cd backend && python -m pytest -q` → **25 passed** (на момент сверки)

Последние коммиты на проде:

| SHA | Что |
|-----|-----|
| `eb2b4b0` | PWA больше не держит старый бандл (нужен был инкогнито) |
| `5038e34` | Эпик рефакторинга S1–S7 |

Активный kit: баг `docs/superpowers/bugs/pwa-stale-cache` (закрыт, на проде). Новый срез — завести свой kit, не дописывать закрытый эпик.

---

## Что это

Учёт для прорабов (бренд WELL DOM): PWA + FastAPI + Capacitor. Вход телефон+PIN, проекты, закупки / выплаты мастерам / приходы, задачи, фото, админка.

Стек **как в коде** (не как старые черновики): vanilla JS, не Vue; один PostgreSQL; Redis только JWT/PIN; фото по умолчанию на диск.

---

## Сделано в этом цикле

Эпик `docs/superpowers/features/prorab-refactor-epic/` — срезы закрыты. Полный rewrite одним PR запрещён: сначала был замок тестами.

| ID | Сделано | Где смотреть |
|----|---------|--------------|
| **S1** | Characterization: вход PIN, список записей, 403 без права | `backend/tests/test_vhod_po_pin.py`, `test_spisok_zapisey.py`, `test_otkaz_bez_prava.py` |
| **S2** | Auth на `PUT /photos/local-upload`, logout отзывает access, gitignore секретов | `photos.py`, `auth.py`, `s3.py`, `redis.py`, `frontend/api.js` |
| **S3** | `limit`/`offset` + `X-Total-Count` на masters/tasks/admin/users; N+1 мастеров и analytics убран (тело списка — по-прежнему массив) | `masters.py`, `analytics.py`, `test_spiski_limit.py` |
| **S4** | Модели и схемы по доменам; `models.models` / `schemas.schemas` — шимы | `backend/app/models/`, `backend/app/schemas/` |
| **S5** | CSS/JS вынесены из `index.html`; вкладки и `onclick` те же | `frontend/index.html`, `css/app.css`, `js/app.js` |
| **S6** | `mobile/www` = копия `frontend/` через `sync-web` (www в gitignore) | `mobile/sync-web.js`, `make sync-web` |
| **S7** | `architecture.md` и README = факт; replica/cache — секция «Не реализовано», не внедряли | `docs/architecture.md` |
| **Баг PWA** | Network-first оболочка, `Cache-Control: no-store` на `sw.js`, reload при новом worker (`welldom-v22`) | `frontend/sw.js`, `js/app.js`, `app/main.py` |

Деплой S1–S7 и фикса PWA на прод уже был (явный OK). Prod агент сам не катит без новой просьбы.

---

## Не сделано / не трогать «заодно»

- Распил `frontend/js/app.js` на модули экранов (общее `currentProject` и десятки `window.*`).
- N+1 на `GET /earnings/all`.
- Новая сборка APK / публикация стора. `android/.../assets/public` обновится только при `npm run open:android` или `build:android*` (там уже `sync-web && cap sync`).
- Ротация GCP-ключа `google-credentials.json` — человек; файл в gitignore, не коммитить.
- Баг `hash_pin` (passlib + bcrypt 5) в продукте: в тестах обход, в `security.py` не меняли.
- PostgreSQL replica, WAL-бэкапы, Redis-кеш справочников/дашборда, Pub/Sub — **нет в коде**, не внедрять без отдельной фичи.
- Vue / новый бандлер — нет Decision.
- `GET /health` на проде 404: маршрут объявлен **после** `StaticFiles("/")`.
- Не коммитить: `.claude/settings.local.json`, `mcps/`, `google-credentials.json`, `mobile/www/`.

---

## Как работать дальше

1. Прочитать этот файл и `docs/architecture.md`.
2. Путь агента разработки: **brownfield**. Preserve: URL `/api/v1/*`, JSON, PIN, вкладки.
3. Новый кусок — свой kit в `docs/superpowers/features/<slug>/` (или `bugs/`). Один живой kit.
4. Тесты: `cd backend && python -m pytest -q` (не из корня без `--rootdir=backend` — сломается asyncio).
5. Прод: только после явного «пуш в прод»; тогда `git push origin main`.

Конституция процесса агента — skill `agent-razrabotki`, не 33 роли и не Platrum/HR.
