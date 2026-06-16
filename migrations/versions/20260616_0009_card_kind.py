"""Add card kind for Basic and Cloze notes."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260616_0009"
down_revision: str | None = "20260616_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cards",
        sa.Column(
            "card_kind",
            sa.Enum(
                "basic",
                "cloze",
                name="card_kind",
                native_enum=False,
            ),
            server_default="basic",
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_cards_card_kind"), "cards", ["card_kind"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cards_card_kind"), table_name="cards")
    op.drop_column("cards", "card_kind")
