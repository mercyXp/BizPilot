from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.dsn import app_async_url, owner_sync_url


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
    database_url_sync: str = ""
    redis_url: str = "memory://"
    bizpilot_app_password: str = ""

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
    demo_enabled: bool = True
    demo_compact: bool = False
    resend_api_key: str = ""
    resend_from_email: str = "BizPilot <noreply@localhost>"

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("SECRET_KEY must not be empty")
        return value

    @model_validator(mode="after")
    def normalize_data_urls(self) -> Self:
        object.__setattr__(
            self,
            "database_url_sync",
            owner_sync_url(self.database_url, self.database_url_sync or None),
        )
        app_role = "bizpilot_app" if self.uses_managed_app_role else None
        app_password = self.bizpilot_app_password.strip() or None
        if self.uses_managed_app_role and not app_password:
            raise ValueError("BIZPILOT_APP_PASSWORD is required in staging and production")
        object.__setattr__(
            self,
            "database_url",
            app_async_url(
                self.database_url,
                app_role=app_role,
                app_password=app_password,
            ),
        )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def uses_managed_app_role(self) -> bool:
        return self.app_env in {"staging", "production"}

    @property
    def requires_email_provider(self) -> bool:
        return self.app_env in {"staging", "production"}

    @property
    def uses_memory_redis(self) -> bool:
        return self.redis_url.startswith("memory://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
