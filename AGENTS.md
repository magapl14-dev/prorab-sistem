# Агенту

Перед любой работой прочитай [`STATUS.md`](STATUS.md), затем [`docs/architecture.md`](docs/architecture.md).

- Не переписывать весь продукт одним PR.
- Preserve: `/api/v1/*`, JSON, PIN, вкладки, vanilla JS.
- Тесты: `cd backend && python -m pytest -q`.
- Прод только с явным OK человека (`git push origin main` → Actions Deploy to VPS).
- Секреты, `mcps/`, `.claude/settings.local.json` не коммитить.
