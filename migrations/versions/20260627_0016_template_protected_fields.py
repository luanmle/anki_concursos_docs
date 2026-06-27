"""Add protected fields to Anki deck template versions."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260627_0016"
down_revision: str | None = "20260620_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "deck_template_versions",
        sa.Column(
            "protected_fields",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("deck_template_versions", "protected_fields")
