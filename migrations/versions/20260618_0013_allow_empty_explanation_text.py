"""Allow empty explanation text in card versions."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260618_0013"
down_revision: str | None = "20260618_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_card_versions_explanation_not_empty",
        "card_versions",
        type_="check",
    )


def downgrade() -> None:
    op.create_check_constraint(
        "ck_card_versions_explanation_not_empty",
        "card_versions",
        "length(explanation_text) > 0",
    )
