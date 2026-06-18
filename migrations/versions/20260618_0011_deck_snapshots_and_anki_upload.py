"""Add deck snapshots for full Anki deck uploads."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0011"
down_revision: str | None = "20260616_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deck_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deck_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("note_count", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["deck_id"],
            ["decks.id"],
            name=op.f("fk_deck_snapshots_deck_id_decks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["release_id"],
            ["releases.id"],
            name=op.f("fk_deck_snapshots_release_id_releases"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deck_snapshots")),
        sa.CheckConstraint("note_count >= 0", name="non_negative_note_count"),
    )
    op.create_index(
        op.f("ix_deck_snapshots_deck_id"),
        "deck_snapshots",
        ["deck_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deck_snapshots_release_id"),
        "deck_snapshots",
        ["release_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_deck_snapshots_release_id"), table_name="deck_snapshots")
    op.drop_index(op.f("ix_deck_snapshots_deck_id"), table_name="deck_snapshots")
    op.drop_table("deck_snapshots")
