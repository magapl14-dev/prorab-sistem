# B-obolochka-vkladok

**Формат:** B (элемент)
**Поверхность:** `frontend/index.html`, `css/app.css`, `js/app.js`

| Элемент | Ожидание |
|---------|----------|
| `#login-screen` `#project-screen` `#main-screen` | есть в оболочке |
| `#tab-home` `#tab-expenses` `#tab-masters` `#tab-payments` `#tab-dashboard` `#tab-report` `#tab-tasks` `#tab-profile` | есть |
| `#nav-home` `#nav-expenses` `#nav-masters` `#nav-tasks` | есть |
| GET `/css/app.css` | 200, есть `--blue` |
| GET `/js/app.js` | 200, есть `padPress` и `showTab` |
| inline `<style>` / большой `<script>` в index | нет |
