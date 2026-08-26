# B-www-zerkalo-frontend

**Формат:** B (элемент)
**Поверхность:** `frontend/`, `mobile/www/`, `mobile/package.json`

| Элемент | Ожидание |
|---------|----------|
| дерево файлов www | те же относительные пути, что frontend |
| байты каждого файла | совпадают |
| `CACHE` в `sw.js` | одна строка в обоих деревьях |
| `open:android` / `build:android*` | содержат `sync-web` |
