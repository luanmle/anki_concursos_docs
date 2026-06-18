"""Store native Anki note payloads on card versions."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0014"
down_revision: str | None = "20260618_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "card_versions",
        sa.Column("note_type", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "card_versions",
        sa.Column("template_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "card_versions",
        sa.Column(
            "anki_fields",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    op.add_column(
        "card_versions",
        sa.Column(
            "anki_template",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    op.add_column(
        "card_versions",
        sa.Column(
            "anki_tags",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )
    op.add_column(
        "card_versions",
        sa.Column("source_note_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "card_versions",
        sa.Column("source_note_guid", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "card_versions",
        sa.Column("source_deck_path", sa.Text(), nullable=True),
    )
    op.create_index(
        op.f("ix_card_versions_note_type"),
        "card_versions",
        ["note_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_card_versions_template_name"),
        "card_versions",
        ["template_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_card_versions_source_note_id"),
        "card_versions",
        ["source_note_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_card_versions_source_note_guid"),
        "card_versions",
        ["source_note_guid"],
        unique=False,
    )
    op.alter_column("card_versions", "anki_fields", server_default=None)
    op.alter_column("card_versions", "anki_template", server_default=None)
    op.alter_column("card_versions", "anki_tags", server_default=None)


def downgrade() -> None:
    op.drop_index(
        op.f("ix_card_versions_source_note_guid"),
        table_name="card_versions",
    )
    op.drop_index(
        op.f("ix_card_versions_source_note_id"),
        table_name="card_versions",
    )
    op.drop_index(op.f("ix_card_versions_template_name"), table_name="card_versions")
    op.drop_index(op.f("ix_card_versions_note_type"), table_name="card_versions")
    op.drop_column("card_versions", "source_deck_path")
    op.drop_column("card_versions", "source_note_guid")
    op.drop_column("card_versions", "source_note_id")
    op.drop_column("card_versions", "anki_tags")
    op.drop_column("card_versions", "anki_template")
    op.drop_column("card_versions", "anki_fields")
    op.drop_column("card_versions", "template_name")
    op.drop_column("card_versions", "note_type")
