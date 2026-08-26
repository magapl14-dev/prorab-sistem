# WELL DOM / prorab-sistem

Учёт для прорабов: PWA + FastAPI + Capacitor. Тот же UI в браузере и в обёртке приложения.

**Новый запуск / агент:** сначала [`STATUS.md`](STATUS.md) — что уже сделано, что на проде, чего не делать заодно.

## Стек

- **Клиент:** vanilla JS (`frontend/`: оболочка HTML, `css/app.css`, `js/app.js`, `api.js`). Не Vue.
- **API:** FastAPI / Python 3.12, один PostgreSQL, Redis для JWT и защиты PIN.
- **Мобайл:** Capacitor 6, `npm run sync-web` копирует фронт в `mobile/www`.

Как устроено подробно и что **ещё нет** в коде — [`docs/architecture.md`](docs/architecture.md).

## Тесты

```bash
make test
# или: cd backend && python -m pytest -q
```

Dev-стенд: `make up` (`infra/docker-compose.yml`).
