from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "BizPilot"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me-in-development-only")

    database_url: str = "postgresql+asyncpg://bizpilot@127.0.0.1:55432/bizpilot"
    database_url_sync: str = "postgresql+psycopg://bizpilot@127.0.0.1:55432/bizpilot"
    redis_url: str = "memory://"

    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    public_app_url: str = "http://localhost:3000"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    email_token_hours: int = 24
    password_reset_hours: int = 2
    invitation_days: int = 7
    auth_cookie_name: str = "bp_refresh"
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 900

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("SECRET_KEY must not be empty")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def uses_memory_redis(self) -> bool:
        return self.redis_url.startswith("memory://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
