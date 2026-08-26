# Proposal: s6-sync-web

**Intent:** `mobile/www` = копия `frontend/`; `sync-web` обязателен в сборке Capacitor и проверяется тестом.
**Зачем сейчас:** нативный бандл на SW v18, веб уже v21 + css/js после S5. Прораб в приложении видит старый UI.
**In:** прогон `sync-web`; замок pytest; `make sync-web`; npm-скрипты по-прежнему зовут sync до cap.
**Out:** новая нативка, плагины, публикация стора, правка `frontend/`.
**Capability:** mobile-web-bundle
**Upset-to-break:** APK без css/js (белый экран после S5), если сборка обойдёт sync-web.

## Preserve

- Capacitor обёртка, appId, плагины — без изменений.
- `webDir: www`. npm `open:*` / `build:android*` уже начинаются с `sync-web` — не убирать.
- API_BASE детект в `api.js` — не трогать.
