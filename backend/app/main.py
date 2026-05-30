import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.database import engine
from .core.redis import close_redis
from .api.v1.router import api_router

# Перерегистрируем .webm как audio — приложение использует webm только для аудиозаписей
# (MediaRecorder). Без этого Starlette StaticFiles отдаёт Content-Type: video/webm
# и audio-плеер браузера не работает.
mimetypes.add_type("audio/webm", ".webm", strict=True)
mimetypes.add_type("audio/webm", ".weba", strict=True)
mimetypes.add_type("audio/ogg", ".ogg", strict=True)
mimetypes.add_type("audio/mp4", ".m4a", strict=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload dir exists
    if settings.storage_type == "local":
        Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Serve uploaded files
if settings.storage_type == "local":
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

# Serve frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
