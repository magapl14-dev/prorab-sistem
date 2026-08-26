# План: S5

1. Characterization: список id экранов/вкладок/nav.
2. Вырезать `<style>` → `css/app.css`, `<script type="module">` → `js/app.js` байт-в-байт.
3. Оболочка: `<link href="/css/app.css">`, `<script type="module" src="/js/app.js">`.
4. SW: `welldom-v21`, STATIC += css/js.
5. pytest: shell + static 200 + S1–S4.
