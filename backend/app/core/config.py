from pydantic_settings import BaseSettings
from typing import Literal


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
    jwt_access_ttl: int = 900
    jwt_refresh_ttl: int = 2592000

    cors_origins: str = "http://localhost:8000"

    login_max_attempts: int = 3
    login_lockout_seconds: int = 900

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
