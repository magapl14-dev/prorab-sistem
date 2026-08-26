# Proposal: s3-pagination-nplus1

**Intent:** Списки masters/tasks/users с limit как у records; N+1 masters и analytics — пакетными запросами.
**Зачем сейчас:** горячие списки без лимита и 2 запроса на мастера.
**In:** Query limit/offset + заголовок X-Total-Count; батч агрегатов.
**Out:** смена JSON с массива на {items}; Vue; earnings/all; распил index.html.
**Capability:** api-lists
**Upset-to-break:** карточки мастеров потеряли total_paid после батча.
