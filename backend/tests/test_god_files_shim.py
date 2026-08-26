"""S4: historical import paths still see every table and schema."""
from app.models import models as models_mod
from app.models.models import Base, User
from app.models.user import User as UserDomain
from app.schemas.schemas import LoginRequest, MasterOut, PhotoOut, RecordOut, TaskOut, UserOut


EXPECTED_TABLES = {
    "users",
    "projects",
    "user_projects",
    "records",
    "photos",
    "audit_log",
    "dictionaries",
    "app_settings",
    "role_permissions",
    "roles",
    "tasks",
    "masters",
    "master_rates",
    "master_project_visibility",
    "task_comments",
    "task_assignees",
}


def test_shim_registers_all_tables():
    assert EXPECTED_TABLES <= set(Base.metadata.tables)
    assert User is UserDomain
    assert User is models_mod.User
    assert User.__tablename__ == "users"


def test_schema_shim_exports():
    assert LoginRequest.model_fields["phone"]
    assert set(RecordOut.model_fields) >= {"id", "kind", "photos"}
    assert set(MasterOut.model_fields) >= {"id", "total_paid", "rates"}
    assert set(TaskOut.model_fields) >= {"id", "title", "assignees"}
    assert set(UserOut.model_fields) >= {"id", "phone", "role"}
    assert set(PhotoOut.model_fields) >= {"id", "s3_key", "url"}
