from fastapi import APIRouter
from .auth import router as auth_router
from .records import router as records_router
from .photos import router as photos_router
from .earnings import router as earnings_router
from .admin.projects import router as admin_projects_router
from .admin.users import router as admin_users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(records_router)
api_router.include_router(photos_router)
api_router.include_router(earnings_router)
api_router.include_router(admin_projects_router)
api_router.include_router(admin_users_router)
