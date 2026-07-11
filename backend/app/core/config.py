from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    app_name: str = "WELL DOM API"
    app_env: Literal["development", "production"] = "development"

    database_url: str = "postgresql+asyncpg://welldom:welldom_dev@localhost/welldom"
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = True

    # Storage: "local" or "s3"
    storage_type: Literal["local", "s3"] = "local"
    upload_dir: str = "/opt/prorab-sistem/uploads"
    public_url: str = "http://localhost:8000"

    # S3 (only when storage_type=s3)
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "welldom-photos"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin123"
    s3_region: str = "us-east-1"

    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl: int = 604800   # 7 days
    jwt_refresh_ttl: int = 2592000  # 30 days

    cors_origins: str = "http://localhost:8000"

    google_credentials_json: Optional[str] = None

    login_max_attempts: int = 3
    login_lockout_seconds: int = 900

    # xAI Grok — для голосового заполнения форм (кнопки "🎙 Сказать всё голосом")
    xai_api_key: Optional[str] = None
    xai_base_url: str = "https://api.x.ai/v1"
    xai_stt_model: str = "grok-stt"
    xai_llm_model: str = "grok-4-1-fast"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        configured = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # Capacitor нативные приложения шлют запросы с этих origins —
        # включаем всегда, чтобы Android/iOS APK работали без правки .env
        native = ["https://localhost", "capacitor://localhost", "ionic://localhost"]
        return list({*configured, *native})


settings = Settings()
