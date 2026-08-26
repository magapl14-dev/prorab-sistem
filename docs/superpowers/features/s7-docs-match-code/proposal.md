# Proposal: s7-docs-match-code

**Intent:** `docs/architecture.md` и README описывают код как есть. Replica/cache не внедрять.
**Зачем сейчас:** документ обещает primary+replica и кеш дашборда — этого нет; следующий срез снова начнёт со лжи.
**In:** переписать architecture.md (факт + ADR «ещё нет»); короткий честный README; тест на запрещённые утверждения.
**Out:** поднимать replica, Redis cache, Pub/Sub, WAL, менять compose/продукт.
**Capability:** docs-architecture
**Upset-to-break:** README снова обещает реплику как текущую схему.

## Preserve

- Поведение продукта и инфраструктурные файлы compose/Caddy не трогать.
- Не добавлять второй Postgres и не включать кеш «чтобы документ стал правдой».
