"""Allow cards to be uploaded without taxonomy."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0012"
down_revision: str | None = "20260618_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "cards",
        "discipline_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.alter_column(
        "cards",
        "topic_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrading nullable card taxonomy is not supported when null values exist"
    )
