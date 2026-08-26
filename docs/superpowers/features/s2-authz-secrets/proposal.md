# Proposal: s2-authz-secrets

**Intent:** Закрыть анонимную запись файлов и живой access после logout; не тащить credentials в git.
**Зачем сейчас:** Blocker-класс дыр; S1 уже лочит вход/списки.
**In:** auth на local-upload, revoke access, path-sanitize, gitignore, фронт шлёт Bearer на local PUT.
**Out:** S3, распил index.html, пагинация, ротация ключа в GCP (человек).
**Capability:** auth
**Upset-to-break:** чужой без логина кладёт файл в uploads; после «Выйти» старый access ещё ходит в /me.
