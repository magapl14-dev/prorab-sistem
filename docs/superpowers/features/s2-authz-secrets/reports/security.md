# Security: s2-authz-secrets

**Вердикт:** pass (дыры закрываем этим срезом)

## До кода

- Анонимный PUT local-upload — HIGH, закрыт authz `photos.create`.
- Access после logout жил до 7 суток — HIGH, `revoked:{token}`.
- Path traversal в save_local — HIGH, resolve+prefix `photos/`.
- google-credentials.json на диске — HIGH, gitignore расширен; ротация GCP — руками.

## После диффа

- Секреты в диффе продукта: нет.
- Prod не деплоим.
