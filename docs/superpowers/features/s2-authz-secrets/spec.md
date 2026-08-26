# Спека: S2 authz и секреты

**Путь:** фича (brownfield, security)
**Capability:** auth

## Preserve

- S1: login PIN, список записей, 403 без права/проекта.
- Залогиненный с `photos.create` по-прежнему загружает файл через upload-url → PUT → confirm.

## ADDED

- **FR-001** Анонимный PUT `/api/v1/photos/local-upload/*` → 401.
- **FR-002** После logout access-токен не проходит `/auth/me` (401).
- **FR-003** PUT с `..` в пути → 400, файл вне upload_dir не пишется.
- **FR-004** В корневом `.gitignore` credentials/json ключи, `.env.*`, `uploads/`.

## Out of scope

- Ротация GCP-ключа в консоли Google (руками).
- S3 presign.
- UI кроме заголовка Authorization на local PUT.
