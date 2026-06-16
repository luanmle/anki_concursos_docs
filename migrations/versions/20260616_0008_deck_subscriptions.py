"""Add deck subscriptions for addon sync."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260616_0008"
down_revision: str | None = "20260615_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deck_subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("deck_id", sa.Uuid(), nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
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
            name=op.f("fk_deck_subscriptions_deck_id_decks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_deck_subscriptions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deck_subscriptions")),
        sa.UniqueConstraint(
            "user_id",
            "deck_id",
            name="uq_deck_subscription_user_deck",
        ),
    )
    op.create_index(
        op.f("ix_deck_subscriptions_deck_id"),
        "deck_subscriptions",
        ["deck_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deck_subscriptions_user_id"),
        "deck_subscriptions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_deck_subscriptions_user_id"),
        table_name="deck_subscriptions",
    )
    op.drop_index(
        op.f("ix_deck_subscriptions_deck_id"),
        table_name="deck_subscriptions",
    )
    op.drop_table("deck_subscriptions")
