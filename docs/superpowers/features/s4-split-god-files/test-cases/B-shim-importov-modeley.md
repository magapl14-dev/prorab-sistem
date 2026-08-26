# B-shim-importov-modeley

**Формат:** B (элемент)
**Поверхность:** `app.models.models`, `app.schemas.schemas`

## Элементы

| Элемент | Ожидание |
|---------|----------|
| `from app.models.models import Base, User` | `User.__tablename__ == "users"`; `Base.metadata` содержит users, projects, records, photos, tasks, masters и остальные таблицы до сплита |
| `from app.schemas.schemas import RecordOut, MasterOut, TaskOut` | те же поля, что до сплита |
| GET `/api/v1/auth/login` PIN | 200 как в S1 |
