import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings


pytestmark = pytest.mark.postgres


def postgres_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    if not url.startswith("postgresql+psycopg://"):
        pytest.fail("TEST_DATABASE_URL must use postgresql+psycopg")
    return url


def test_migrations_apply_to_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    url = postgres_url()
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert {"users", "cards", "card_versions", "releases"} <= tables
        with engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            triggers = set(
                connection.execute(
                    text(
                        "SELECT tgname FROM pg_trigger "
                        "WHERE NOT tgisinternal"
                    )
                ).scalars()
            )
        assert revision == "20260612_0006"
        assert {
            "trg_card_versions_immutable",
            "trg_cards_current_version_ownership",
            "trg_releases_immutable",
            "trg_card_reports_audit_immutable",
        } <= triggers
    finally:
        engine.dispose()
        get_settings.cache_clear()
