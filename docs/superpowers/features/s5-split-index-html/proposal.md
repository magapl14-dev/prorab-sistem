# Proposal: s5-split-index-html

**Intent:** Вынести CSS и JS из `frontend/index.html` в файлы; HTML-оболочка с теми же id и `onclick`.
**Зачем сейчас:** 7k god-файл нельзя ревьюить; правки вкладок бьют стили и логику сразу.
**In:** `css/app.css`, `js/app.js`; оболочка `index.html`; SW знает новые URL.
**Out:** Vue/бандлер; смена UX; разрезание JS по экранам (общее состояние/`window.*`); sync `mobile/www` (S6).
**Capability:** frontend-structure
**Upset-to-break:** вкладки не открываются, PIN-клавиатура молчит, PWA отдаёт пустой кэш.

## Preserve

- Те же экраны: login, projects, main.
- Те же вкладки: home, expenses, masters, payments, dashboard, report, tasks, profile.
- Те же `id` и `onclick="showTab"|padPress|openAddForm|…`.
- Не Vue. Не новый сборщик.
- `api.js` без смены контракта.
