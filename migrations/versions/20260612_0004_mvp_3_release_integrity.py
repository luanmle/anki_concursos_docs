"""Add deck removal actions and release immutability.

Revision ID: 20260612_0004
Revises: 20260612_0003
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_0004"
down_revision: str | None = "20260612_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "deck_cards",
        sa.Column(
            "removal_action",
            sa.Enum(
                "removed",
                "deprecated",
                name="deck_card_removal_action",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE deck_cards
        SET removal_action = 'removed'
        WHERE removed_at IS NOT NULL AND removal_action IS NULL
        """
    )
    op.create_check_constraint(
        "ck_deck_cards_valid_removal_action",
        "deck_cards",
        "(removed_at IS NULL AND removal_action IS NULL) OR "
        "(removed_at IS NOT NULL AND removal_action IN ('removed', 'deprecated'))",
    )

    op.execute(
        """
        CREATE FUNCTION prevent_published_release_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'published releases are immutable';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_releases_immutable
        BEFORE UPDATE OR DELETE ON releases
        FOR EACH ROW EXECUTE FUNCTION prevent_published_release_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_release_items_immutable
        BEFORE UPDATE OR DELETE ON release_items
        FOR EACH ROW EXECUTE FUNCTION prevent_published_release_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_release_items_immutable ON release_items")
    op.execute("DROP TRIGGER IF EXISTS trg_releases_immutable ON releases")
    op.execute("DROP FUNCTION IF EXISTS prevent_published_release_mutation()")
    op.drop_constraint(
        "ck_deck_cards_valid_removal_action",
        "deck_cards",
        type_="check",
    )
    op.drop_column("deck_cards", "removal_action")
