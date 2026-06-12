"""Add authenticated administrative users for MVP 7.

Revision ID: 20260612_0006
Revises: 20260612_0005
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_0006"
down_revision: str | None = "20260612_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "curator",
                "reviewer",
                name="user_role",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(email) > 3",
            name="ck_users_email_not_empty",
        ),
        sa.CheckConstraint(
            "length(display_name) > 0",
            name="ck_users_display_name_not_empty",
        ),
        sa.CheckConstraint(
            "length(password_hash) > 0",
            name="ck_users_password_hash_not_empty",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )


def downgrade() -> None:
    op.drop_table("users")
