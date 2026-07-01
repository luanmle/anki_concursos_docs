"""Community comments on published cards (notes)."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260701_0019"
down_revision: str | None = "20260627_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "note_comments",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "card_id",
            sa.Uuid(),
            sa.ForeignKey("cards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("author_email", sa.String(length=320), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
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
        sa.CheckConstraint("length(body) > 0", name="note_comment_body_not_empty"),
    )
    op.create_index(op.f("ix_note_comments_card_id"), "note_comments", ["card_id"])
    op.create_index(
        op.f("ix_note_comments_author_user_id"),
        "note_comments",
        ["author_user_id"],
    )
    op.create_index(
        "ix_note_comments_card_created",
        "note_comments",
        ["card_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_note_comments_card_created", table_name="note_comments")
    op.drop_index(op.f("ix_note_comments_author_user_id"), table_name="note_comments")
    op.drop_index(op.f("ix_note_comments_card_id"), table_name="note_comments")
    op.drop_table("note_comments")
