from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEVELOPMENT_AUTH_SECRET = "development-auth-secret-change-me"


class Settings(BaseSettings):
    app_name: str = "Anki Concursos API"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+psycopg://anki:anki@localhost:5432/anki_concursos"
    )
    redis_url: str = "redis://localhost:6379/0"
    database_sslmode: str | None = None
    database_pool_size: int = 5
    database_max_overflow: int = 5
    database_pool_timeout_seconds: int = 30
    database_pool_recycle_seconds: int = 300
    admin_api_key: str = "development-admin-key"
    allow_legacy_admin_api_key: bool = True
    auth_secret_key: str = DEVELOPMENT_AUTH_SECRET
    honeybadger_api_key: str | None = None
    access_token_expire_minutes: int = Field(default=60, ge=1)
    refresh_token_expire_days: int = Field(default=30, ge=1)
    addon_api_version: str = "1"
    min_addon_version: str = "0.1.0"
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "System administrator"
    cors_origins: Annotated[list[str], NoDecode] = []
    public_report_rate_limit: int = 20
    public_report_rate_window_seconds: int = 60
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 60
    rate_limit_max_keys: int = 10_000
    trust_proxy_headers: bool = False
    max_request_body_bytes: int = 262_144
    docs_enabled: bool | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            for prefix in ("postgresql://", "postgres://"):
                if value.startswith(prefix):
                    return value.replace(prefix, "postgresql+psycopg://", 1)
        return value

    def database_connect_args(self) -> dict[str, str]:
        if (
            self.database_sslmode
            and self.database_url.startswith("postgresql+psycopg://")
        ):
            return {"sslmode": self.database_sslmode}
        return {}

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.docs_enabled is None:
            self.docs_enabled = self.app_env != "production"
        if self.app_env == "production":
            if self.allow_legacy_admin_api_key:
                raise ValueError(
                    "ALLOW_LEGACY_ADMIN_API_KEY must be false in production"
                )
            if (
                len(self.auth_secret_key) < 32
                or self.auth_secret_key == DEVELOPMENT_AUTH_SECRET
            ):
                raise ValueError(
                    "AUTH_SECRET_KEY must be a non-default secret with at least "
                    "32 characters in production"
                )
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError(
                    "DATABASE_URL must use postgresql+psycopg in production"
                )
            if self.database_sslmode not in {"require", "verify-ca", "verify-full"}:
                raise ValueError(
                    "DATABASE_SSLMODE must require TLS in production"
                )
        if self.database_pool_size < 1:
            raise ValueError("DATABASE_POOL_SIZE must be positive")
        if self.database_max_overflow < 0:
            raise ValueError("DATABASE_MAX_OVERFLOW cannot be negative")
        if self.rate_limit_max_keys < 100:
            raise ValueError("RATE_LIMIT_MAX_KEYS must be at least 100")
        if self.max_request_body_bytes < 1024:
            raise ValueError("MAX_REQUEST_BODY_BYTES must be at least 1024")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
