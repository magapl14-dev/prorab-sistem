# Assessment: PWA долго отдаёт старую версию

**Вердикт:** real-bug
**Симптом:** после деплоя обычное окно показывает старый UI; инкогнито — новый.

**Причина:** `sw.js` cache-first для `/js/app.js` и `/css/app.css`; регистрация без `updateViaCache: 'none'`. Пока вручную не сменить `welldom-vN` и браузер не переустановит SW, живёт старый бандл.

**Preserve:** офлайн-фолбэк из Cache Storage; API не перехватывать.
**Фикс:** network-first на оболочку; `Cache-Control` на `sw.js`; reload при смене контроллера.
