"""Persist add-on note suggestions."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260627_0017"
down_revision: str | None = "20260627_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "note_suggestions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "deck_id",
            sa.Uuid(),
            sa.ForeignKey("decks.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "card_id",
            sa.Uuid(),
            sa.ForeignKey("cards.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "card_version_id",
            sa.Uuid(),
            sa.ForeignKey("card_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "submitted_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("submitted_by_email", sa.String(length=320), nullable=False),
        sa.Column(
            "suggestion_type",
            sa.Enum(
                "updated_content",
                "new_content",
                "spelling/grammar",
                "content_error",
                "new_card_to_add",
                "new_tags",
                "updated_tags",
                "delete",
                "other",
                name="note_suggestion_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "accepted",
                "rejected",
                name="note_suggestion_status",
                native_enum=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("fields", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("added_tags", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("removed_tags", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resulting_card_version_id",
            sa.Uuid(),
            sa.ForeignKey("card_versions.id", ondelete="RESTRICT"),
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
        sa.CheckConstraint(
            "(card_id IS NOT NULL AND card_version_id IS NOT NULL) "
            "OR deck_id IS NOT NULL",
            name="note_suggestion_has_target",
        ),
        sa.CheckConstraint(
            "length(submitted_by_email) > 3",
            name="suggestion_email_not_empty",
        ),
        sa.CheckConstraint("length(comment) > 0", name="suggestion_comment_not_empty"),
        sa.CheckConstraint(
            "review_comment IS NULL OR length(review_comment) > 0",
            name="suggestion_review_comment_not_empty",
        ),
    )
    op.create_index(
        "ix_note_suggestions_status_created",
        "note_suggestions",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_note_suggestions_deck_id"), "note_suggestions", ["deck_id"])
    op.create_index(op.f("ix_note_suggestions_card_id"), "note_suggestions", ["card_id"])
    op.create_index(
        op.f("ix_note_suggestions_card_version_id"),
        "note_suggestions",
        ["card_version_id"],
    )
    op.create_index(
        op.f("ix_note_suggestions_submitted_by_user_id"),
        "note_suggestions",
        ["submitted_by_user_id"],
    )
    op.create_index(
        op.f("ix_note_suggestions_resulting_card_version_id"),
        "note_suggestions",
        ["resulting_card_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_note_suggestions_resulting_card_version_id"),
        table_name="note_suggestions",
    )
    op.drop_index(
        op.f("ix_note_suggestions_submitted_by_user_id"),
        table_name="note_suggestions",
    )
    op.drop_index(op.f("ix_note_suggestions_card_version_id"), table_name="note_suggestions")
    op.drop_index(op.f("ix_note_suggestions_card_id"), table_name="note_suggestions")
    op.drop_index(op.f("ix_note_suggestions_deck_id"), table_name="note_suggestions")
    op.drop_index("ix_note_suggestions_status_created", table_name="note_suggestions")
    op.drop_table("note_suggestions")
