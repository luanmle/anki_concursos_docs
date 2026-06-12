from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_AUTH_SECRET = "development-auth-secret-change-me"


class Settings(BaseSettings):
    app_name: str = "Anki Concursos API"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+psycopg://anki:anki@localhost:5432/anki_concursos"
    )
    redis_url: str = "redis://localhost:6379/0"
    admin_api_key: str = "development-admin-key"
    allow_legacy_admin_api_key: bool = True
    auth_secret_key: str = DEVELOPMENT_AUTH_SECRET
    access_token_expire_minutes: int = 60
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "System administrator"
    cors_origins: list[str] = []
    public_report_rate_limit: int = 20
    public_report_rate_window_seconds: int = 60
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 60
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
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

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
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
