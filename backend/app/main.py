import mimetypes
import posixpath
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Response
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

_PWA_NO_CACHE = {"/sw.js", "/index.html", "/js/app.js", "/css/app.css", "/api.js", "/manifest.json"}

_UPLOAD_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jpe": "image/jpeg",
    ".jfif": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".webm": "audio/webm",
    ".weba": "audio/webm",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".mpeg": "audio/mpeg",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
    ".wave": "audio/wav",
}
_UPLOAD_CSP = "sandbox; default-src 'none'; script-src 'none'; object-src 'none'; base-uri 'none'"


@app.middleware("http")
async def pwa_no_cache_headers(request, call_next):
    path = request.url.path
    is_upload = path.startswith("/uploads/")
    relative_path = posixpath.normpath(path[len("/uploads/"):].lstrip("/")) if is_upload else ""
    filename = posixpath.basename(relative_path)
    is_incomplete_upload = (
        relative_path.startswith("photos/")
        and filename.startswith(".upload-")
        and filename.endswith(".tmp")
    )
    response = Response(status_code=404) if is_incomplete_upload else await call_next(request)
    if is_upload:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = _UPLOAD_CSP
        if response.status_code in (200, 206, 304):
            media_type = (
                "image/jpeg"
                if relative_path.startswith("thumbs/")
                else _UPLOAD_MEDIA_TYPES.get(Path(relative_path).suffix.lower())
            )
            response.headers["Content-Type"] = media_type or "application/octet-stream"
            if media_type is None:
                response.headers["Content-Disposition"] = "attachment"
    if path in _PWA_NO_CACHE or path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


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
