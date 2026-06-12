"""Add immutable public identifiers to cards.

Revision ID: 20260612_0003
Revises: 20260612_0002
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_0003"
down_revision: str | None = "20260612_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("public_id", sa.String(35), nullable=True))
    op.execute(
        """
        UPDATE cards
        SET public_id = 'AC-' || upper(replace(id::text, '-', ''))
        WHERE public_id IS NULL
        """
    )
    op.alter_column("cards", "public_id", nullable=False)
    op.create_unique_constraint("uq_cards_public_id", "cards", ["public_id"])
    op.alter_column(
        "cards",
        "public_id",
        server_default=sa.text(
            "'AC-' || upper(replace(gen_random_uuid()::text, '-', ''))"
        ),
    )
    op.create_check_constraint(
        "ck_cards_public_id_format",
        "cards",
        "public_id ~ '^AC-[0-9A-F]{32}$'",
    )
    op.execute(
        """
        CREATE FUNCTION prevent_card_public_id_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.public_id IS DISTINCT FROM OLD.public_id THEN
                RAISE EXCEPTION 'card public_id is immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_cards_public_id_immutable
        BEFORE UPDATE OF public_id ON cards
        FOR EACH ROW EXECUTE FUNCTION prevent_card_public_id_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_cards_public_id_immutable ON cards")
    op.execute("DROP FUNCTION IF EXISTS prevent_card_public_id_mutation()")
    op.drop_constraint("ck_cards_public_id_format", "cards", type_="check")
    op.drop_constraint("uq_cards_public_id", "cards", type_="unique")
    op.drop_column("cards", "public_id")
