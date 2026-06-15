import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_legacy_api_key() -> None:
    with pytest.raises(ValidationError, match="ALLOW_LEGACY_ADMIN_API_KEY"):
        Settings(
            _env_file=None,
            app_env="production",
            allow_legacy_admin_api_key=True,
            auth_secret_key="x" * 32,
            database_url="postgresql+psycopg://user:pass@db/app",
        )


def test_production_disables_docs_by_default() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        allow_legacy_admin_api_key=False,
        auth_secret_key="x" * 32,
        database_url="postgresql+psycopg://user:pass@db/app",
        database_sslmode="require",
    )

    assert settings.docs_enabled is False


def test_production_rejects_default_auth_secret() -> None:
    with pytest.raises(ValidationError, match="AUTH_SECRET_KEY"):
        Settings(
            _env_file=None,
            app_env="production",
            allow_legacy_admin_api_key=False,
            database_url="postgresql+psycopg://user:pass@db/app",
            database_sslmode="require",
        )


def test_cors_origins_are_parsed_from_environment_format() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins="https://admin.example.com, http://localhost:3000",
    )

    assert settings.cors_origins == [
        "https://admin.example.com",
        "http://localhost:3000",
    ]


def test_cors_origins_are_parsed_from_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://admin.example.com, http://localhost:3000",
    )

    settings = Settings(_env_file=None)

    assert settings.cors_origins == [
        "https://admin.example.com",
        "http://localhost:3000",
    ]


def test_native_postgresql_url_is_normalized_for_psycopg() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://user:pass@db.example.com:25060/app",
    )

    assert settings.database_url == (
        "postgresql+psycopg://user:pass@db.example.com:25060/app"
    )


def test_production_requires_database_tls() -> None:
    with pytest.raises(ValidationError, match="DATABASE_SSLMODE"):
        Settings(
            _env_file=None,
            app_env="production",
            allow_legacy_admin_api_key=False,
            auth_secret_key="x" * 32,
            database_url="postgresql+psycopg://user:pass@db/app",
            database_sslmode=None,
        )
