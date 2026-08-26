# Спека: S6 sync-web

**Путь:** рефакторинг

## Preserve

- Сборка APK/IPA как в README: `npm run sync-web && cap sync …`.
- Нативный слой (плагины, appId, splash) не менять.
- Веб-контракт S5: оболочка + `/css/app.css` + `/js/app.js`.

## ADDED (процесс, не UX)

- **FR-001** `node mobile/sync-web.js` копирует всё дерево `frontend/` в `mobile/www/` (включая css/ и js/).
- **FR-002** После копирования набор относительных путей и байты файлов совпадают; версия `CACHE` в `sw.js` одна.
- **FR-003** Скрипты `open:android`, `open:ios`, `build:android`, `build:android:debug` вызывают `sync-web` до `cap`.

## Out of scope

- S7 architecture.md.
- Публикация в стор, новый APK «заодно».
- Правка вёрстки.

## Independent Test

pytest: зеркало www/frontend после sync-web; в `sw.js` одна версия CACHE; npm-скрипты сборки содержат `sync-web`.
