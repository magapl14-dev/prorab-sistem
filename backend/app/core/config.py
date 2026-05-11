from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "WELL DOM API"
    app_env: Literal["development", "production"] = "development"

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_public_url: str = "http://localhost:9000"
    s3_bucket: str = "welldom-photos"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin123"
    s3_region: str = "us-east-1"

    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl: int = 900       # 15 minutes
    jwt_refresh_ttl: int = 2592000  # 30 days

    cors_origins: str = "http://localhost:8000,http://localhost:3000"

    login_max_attempts: int = 3
    login_lockout_seconds: int = 900

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
