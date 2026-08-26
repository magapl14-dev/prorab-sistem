# Спека: S1 замок поведения API

**Статус:** ready
**Capability:** auth-records-lock
**Путь:** рефакторинг (brownfield)

## Intent

Лочим существующий HTTP-контракт тестами. Продукт не меняем.

## Preserve

- POST `/api/v1/auth/login` — телефон+PIN, 200 + access_token при верном PIN; 401 при неверном.
- GET `/api/v1/auth/me` — 401 без токена; 200 с именем и ролью при валидном access.
- GET `/api/v1/projects/{code}/records` — 401 без токена; 403 если нет ни одного `*.view` по kinds; 200 и запись в `items`, если есть `expenses.view` и доступ к проекту.
- 403, если пользователь не в проекте (не admin).

## Out of scope

- Смена полей ответа, статусов, PIN-политики.
- Закрытие local-upload, распил index.html.

## Independent Test

`cd backend && pytest` — все тесты замка зелёные без живого прода.
