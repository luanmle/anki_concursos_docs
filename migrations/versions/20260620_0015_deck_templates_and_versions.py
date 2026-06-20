"""Persist deck templates and template versions for Anki uploads."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260620_0015"
down_revision: str | None = "20260618_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deck_templates",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "deck_id",
            sa.Uuid(),
            sa.ForeignKey("decks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("template_key", sa.String(length=255), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("note_type", sa.String(length=255), nullable=False),
        sa.Column(
            "card_kind",
            sa.Enum(
                "basic",
                "cloze",
                name="deck_template_card_kind",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "current_version_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("deck_id", "template_key", name="uq_deck_template_key"),
        sa.UniqueConstraint(
            "deck_id", "template_name", name="uq_deck_template_name"
        ),
        sa.CheckConstraint("length(template_key) > 0", name="template_key_not_empty"),
        sa.CheckConstraint(
            "length(template_name) > 0", name="template_name_not_empty"
        ),
        sa.CheckConstraint(
            "length(note_type) > 0", name="template_note_type_not_empty"
        ),
    )
    op.create_index(op.f("ix_deck_templates_deck_id"), "deck_templates", ["deck_id"], unique=False)
    op.create_index(
        op.f("ix_deck_templates_current_version_id"),
        "deck_templates",
        ["current_version_id"],
        unique=False,
    )
    op.create_table(
        "deck_template_versions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "deck_template_id",
            sa.Uuid(),
            sa.ForeignKey("deck_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("fields", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column(
            "field_mapping",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("front_html", sa.Text(), nullable=False),
        sa.Column("back_html", sa.Text(), nullable=False),
        sa.Column(
            "styling_css",
            sa.Text(),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="published",
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "deck_template_id", "version_number", name="uq_deck_template_version"
        ),
        sa.CheckConstraint(
            "version_number > 0", name="positive_template_version_number"
        ),
        sa.CheckConstraint(
            "length(front_html) > 0", name="template_front_not_empty"
        ),
        sa.CheckConstraint(
            "length(back_html) > 0", name="template_back_not_empty"
        ),
        sa.CheckConstraint(
            "length(content_hash) = 64", name="template_hash_length"
        ),
        sa.CheckConstraint(
            "length(created_by) > 0", name="template_created_by_not_empty"
        ),
    )
    op.create_index(
        op.f("ix_deck_template_versions_deck_template_id"),
        "deck_template_versions",
        ["deck_template_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deck_template_versions_content_hash"),
        "deck_template_versions",
        ["content_hash"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_deck_templates_current_version_id_deck_template_versions"),
        "deck_templates",
        "deck_template_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_deck_template_versions_content_hash"),
        table_name="deck_template_versions",
    )
    op.drop_index(
        op.f("ix_deck_template_versions_deck_template_id"),
        table_name="deck_template_versions",
    )
    op.drop_table("deck_template_versions")
    op.drop_index(
        op.f("ix_deck_templates_current_version_id"),
        table_name="deck_templates",
    )
    op.drop_index(op.f("ix_deck_templates_deck_id"), table_name="deck_templates")
    op.drop_table("deck_templates")
