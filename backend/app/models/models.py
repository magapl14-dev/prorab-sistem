"""Shim: keep `from app.models.models import X` after the domain split."""
from ..core.database import Base
from .catalog import AppSetting, AuditLog, Dictionary
from .master import Master, MasterProjectVisibility, MasterRate
from .photo import Photo
from .project import Project, UserProject
from .record import Record
from .task import Task, TaskAssignee, TaskComment
from .user import Role, RolePermission, User

__all__ = [
    "Base",
    "AppSetting",
    "AuditLog",
    "Dictionary",
    "Master",
    "MasterProjectVisibility",
    "MasterRate",
    "Photo",
    "Project",
    "Record",
    "Role",
    "RolePermission",
    "Task",
    "TaskAssignee",
    "TaskComment",
    "User",
    "UserProject",
]
