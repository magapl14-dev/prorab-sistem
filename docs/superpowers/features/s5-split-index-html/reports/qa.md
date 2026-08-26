# QA: s5-split-index-html

**Вердикт:** pass (структурный smoke)
**Release Gate:** не prod

| Кейс | Результат |
|------|-----------|
| B-obolochka-vkladok | pass (`test_frontend_shell.py`) |
| GET `/css/app.css` `/js/app.js` `/index.html` | 200 |
| S1–S4 suite | pass |

Команда: `cd backend && python -m pytest -q` → **19 passed**.

Не гоняли клики вкладок в реальном браузере (нет browser tools). Preserve UX — по id/`window.padPress`/`window.showTab`.
