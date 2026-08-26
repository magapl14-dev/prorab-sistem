# Plan: s2-authz-secrets

**Attack surface:** yes (upload, JWT)

## Foundational

- T001 [be] падающие тесты FR-001…003 (TDD)
- T002 [be] local-upload: current_user + photos.create + sanitize path
- T003 [be] logout пишет `revoked:{access}`; NullRedis хранит ключи в процессе
- T004 [fe] Photos.upload: Bearer на URL local-upload, не на S3
- T005 gitignore

## Preserve check

- T006 suite S1 зелёный
