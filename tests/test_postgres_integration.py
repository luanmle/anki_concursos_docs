import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

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
        assert revision == "20260627_0016"
        assert {
            "trg_card_versions_immutable",
            "trg_cards_current_version_ownership",
            "trg_releases_immutable",
            "trg_card_reports_audit_immutable",
        } <= triggers
        user_columns = {
            column["name"] for column in inspect(engine).get_columns("users")
        }
        report_columns = {
            column["name"]
            for column in inspect(engine).get_columns("card_reports")
        }
        template_version_columns = {
            column["name"]
            for column in inspect(engine).get_columns("deck_template_versions")
        }
        assert "credential_version" in user_columns
        assert "reporter_reference" in report_columns
        assert "user_id" not in report_columns
        assert "protected_fields" in template_version_columns
    finally:
        engine.dispose()
        get_settings.cache_clear()


def test_postgresql_enforces_immutability_and_release_uniqueness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = postgres_url()
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    engine = create_engine(url)
    discipline_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    card_id = uuid.uuid4()
    public_id = f"AC-{card_id.hex.upper()}"
    version_id = uuid.uuid4()
    deck_id = uuid.uuid4()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO disciplines (id, name) "
                    "VALUES (:id, :name)"
                ),
                {"id": discipline_id, "name": f"Postgres {discipline_id}"},
            )
            connection.execute(
                text(
                    "INSERT INTO topics (id, discipline_id, name) "
                    "VALUES (:id, :discipline_id, :name)"
                ),
                {
                    "id": topic_id,
                    "discipline_id": discipline_id,
                    "name": "Integracao",
                },
            )
            connection.execute(
                text(
                    "INSERT INTO cards "
                    "(id, public_id, canonical_key, discipline_id, topic_id, "
                    "status) VALUES (:id, :public_id, :key, :discipline_id, "
                    ":topic_id, 'published')"
                ),
                {
                    "id": card_id,
                    "public_id": public_id,
                    "key": f"postgres-{card_id}",
                    "discipline_id": discipline_id,
                    "topic_id": topic_id,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO card_versions "
                    "(id, card_id, version_number, front_text, back_text, "
                    "answer_text, explanation_text, change_reason, created_by, "
                    "status, content_hash, anki_fields, anki_template, anki_tags) VALUES "
                    "(:id, :card_id, 1, 'front', 'back', 'answer', "
                    "'explanation', 'initial', 'postgres-test', 'published', "
                    ":content_hash, :anki_fields, :anki_template, :anki_tags)"
                ),
                {
                    "id": version_id,
                    "card_id": card_id,
                    "content_hash": uuid.uuid4().hex * 2,
                    "anki_fields": "[]",
                    "anki_template": "{}",
                    "anki_tags": "[]",
                },
            )
            connection.execute(
                text(
                    "UPDATE cards SET current_version_id = :version_id "
                    "WHERE id = :card_id"
                ),
                {"version_id": version_id, "card_id": card_id},
            )
            connection.execute(
                text(
                    "INSERT INTO decks (id, name, status) "
                    "VALUES (:id, :name, 'draft')"
                ),
                {"id": deck_id, "name": f"Deck {deck_id}"},
            )
            connection.execute(
                text(
                    "INSERT INTO releases "
                    "(id, deck_id, release_number, published_at) "
                    "VALUES (:id, :deck_id, 1, now())"
                ),
                {"id": uuid.uuid4(), "deck_id": deck_id},
            )

        with pytest.raises(DBAPIError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE card_versions SET front_text = 'changed' "
                        "WHERE id = :id"
                    ),
                    {"id": version_id},
                )

        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO releases "
                        "(id, deck_id, release_number, published_at) "
                        "VALUES (:id, :deck_id, 1, now())"
                    ),
                    {"id": uuid.uuid4(), "deck_id": deck_id},
                )
    finally:
        engine.dispose()
        get_settings.cache_clear()
