from fastapi import APIRouter
from .auth import router as auth_router
from .records import router as records_router
from .photos import router as photos_router
from .earnings import router as earnings_router
from .tasks import router as tasks_router
from .masters import router as masters_router
from .admin.projects import router as admin_projects_router
from .admin.users import router as admin_users_router
from .admin.permissions import router as admin_permissions_router
from .admin.roles import router as admin_roles_router
from .admin.bitrix import router as admin_bitrix_router
from .admin.analytics import router as admin_analytics_router
from .settings import router as settings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(records_router)
api_router.include_router(photos_router)
api_router.include_router(earnings_router)
api_router.include_router(tasks_router)
api_router.include_router(masters_router)
api_router.include_router(admin_projects_router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_permissions_router)
api_router.include_router(admin_roles_router)
api_router.include_router(admin_bitrix_router)
api_router.include_router(admin_analytics_router)
api_router.include_router(settings_router)
