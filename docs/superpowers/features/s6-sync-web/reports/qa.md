# QA: s6-sync-web

**Вердикт:** pass
**Release Gate:** не prod; APK не собирали

| Кейс | Результат |
|------|-----------|
| B-www-zerkalo-frontend | pass (`test_www_mirrors_frontend.py`) |
| `node mobile/sync-web.js` | 6 files |
| CACHE | `welldom-v21` в frontend и www |
| S1–S5 | pass |

Команда: `cd backend && python -m pytest -q` → **21 passed**.
