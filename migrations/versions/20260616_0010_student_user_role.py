"""Add student user role for addon users."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260616_0010"
down_revision: str | None = "20260616_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("user_role", "users", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('admin', 'curator', 'reviewer', 'student')",
    )


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'reviewer' WHERE role = 'student'")
    op.drop_constraint("user_role", "users", type_="check")
    op.create_check_constraint(
        "user_role",
        "users",
        "role IN ('admin', 'curator', 'reviewer')",
    )
