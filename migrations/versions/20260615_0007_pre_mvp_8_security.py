"""Add credential revocation and clarify public report identity.

Revision ID: 20260615_0007
Revises: 20260612_0006
Create Date: 2026-06-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260615_0007"
down_revision: str | None = "20260612_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "credential_version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_users_positive_credential_version",
        "users",
        "credential_version > 0",
    )
    op.alter_column(
        "card_reports",
        "user_id",
        new_column_name="reporter_reference",
        existing_type=sa.String(255),
        existing_nullable=True,
    )
    op.drop_index("ix_card_reports_user_id", table_name="card_reports")
    op.create_index(
        "ix_card_reports_reporter_reference",
        "card_reports",
        ["reporter_reference"],
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION protect_card_report_audit()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.card_id IS DISTINCT FROM OLD.card_id
                OR NEW.card_version_id IS DISTINCT FROM OLD.card_version_id
                OR NEW.reporter_reference IS DISTINCT FROM OLD.reporter_reference
                OR NEW.report_type IS DISTINCT FROM OLD.report_type
                OR NEW.message IS DISTINCT FROM OLD.message THEN
                RAISE EXCEPTION 'card report content is immutable';
            END IF;

            IF OLD.status IN ('rejected', 'resolved', 'duplicate') THEN
                RAISE EXCEPTION 'reviewed card reports are immutable';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION protect_card_report_audit()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.card_id IS DISTINCT FROM OLD.card_id
                OR NEW.card_version_id IS DISTINCT FROM OLD.card_version_id
                OR NEW.user_id IS DISTINCT FROM OLD.user_id
                OR NEW.report_type IS DISTINCT FROM OLD.report_type
                OR NEW.message IS DISTINCT FROM OLD.message THEN
                RAISE EXCEPTION 'card report content is immutable';
            END IF;

            IF OLD.status IN ('rejected', 'resolved', 'duplicate') THEN
                RAISE EXCEPTION 'reviewed card reports are immutable';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.drop_index(
        "ix_card_reports_reporter_reference",
        table_name="card_reports",
    )
    op.alter_column(
        "card_reports",
        "reporter_reference",
        new_column_name="user_id",
        existing_type=sa.String(255),
        existing_nullable=True,
    )
    op.create_index("ix_card_reports_user_id", "card_reports", ["user_id"])
    op.drop_constraint(
        "ck_users_positive_credential_version",
        "users",
        type_="check",
    )
    op.drop_column("users", "credential_version")
