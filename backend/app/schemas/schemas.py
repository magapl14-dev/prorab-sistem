"""Shim: keep `from app.schemas.schemas import X` after the domain split."""
from .analytics import UserAnalyticsRow
from .auth import (
    ChangePinRequest,
    LoginRequest,
    ProjectBrief,
    RefreshRequest,
    TokenResponse,
    UserBrief,
)
from .catalog import (
    AppSettingOut,
    AppSettingUpdate,
    BitrixSettingsOut,
    BitrixSettingsUpdate,
    BitrixTestResult,
    DictionaryCreate,
    DictionaryOut,
    DictionaryUpdate,
)
from .earnings import EarningsOut, PlanOut
from .master import MasterCreate, MasterOut, MasterRateIn, MasterRateOut, MasterUpdate
from .permission import (
    PermissionItem,
    PermissionsBulkUpdate,
    PermissionsMatrix,
    RoleCreate,
    RoleOut,
)
from .photo import ConfirmUploadRequest, PhotoOut, UploadUrlRequest, UploadUrlResponse
from .project import AssignUserRequest, ProjectCreate, ProjectOut, ProjectUpdate
from .record import AuthorBrief, RecordCreate, RecordListResponse, RecordOut, RecordUpdate
from .task import (
    TaskAssigneeBrief,
    TaskCommentCreate,
    TaskCommentOut,
    TaskCreate,
    TaskMasterBrief,
    TaskOut,
    TaskProjectBrief,
    TaskUpdate,
)
from .user import UserCreate, UserOut

__all__ = [
    "AppSettingOut",
    "AppSettingUpdate",
    "AssignUserRequest",
    "AuthorBrief",
    "BitrixSettingsOut",
    "BitrixSettingsUpdate",
    "BitrixTestResult",
    "ChangePinRequest",
    "ConfirmUploadRequest",
    "DictionaryCreate",
    "DictionaryOut",
    "DictionaryUpdate",
    "EarningsOut",
    "LoginRequest",
    "MasterCreate",
    "MasterOut",
    "MasterRateIn",
    "MasterRateOut",
    "MasterUpdate",
    "PermissionItem",
    "PermissionsBulkUpdate",
    "PermissionsMatrix",
    "PhotoOut",
    "PlanOut",
    "ProjectBrief",
    "ProjectCreate",
    "ProjectOut",
    "ProjectUpdate",
    "RecordCreate",
    "RecordListResponse",
    "RecordOut",
    "RecordUpdate",
    "RefreshRequest",
    "RoleCreate",
    "RoleOut",
    "TaskAssigneeBrief",
    "TaskCommentCreate",
    "TaskCommentOut",
    "TaskCreate",
    "TaskMasterBrief",
    "TaskOut",
    "TaskProjectBrief",
    "TaskUpdate",
    "TokenResponse",
    "UploadUrlRequest",
    "UploadUrlResponse",
    "UserAnalyticsRow",
    "UserBrief",
    "UserCreate",
    "UserOut",
]
