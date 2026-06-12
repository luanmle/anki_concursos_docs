"""Add reports and review tasks for MVP 6 curation.

Revision ID: 20260612_0005
Revises: 20260612_0004
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_0005"
down_revision: str | None = "20260612_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def controlled_enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
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
    )


def upgrade() -> None:
    op.create_table(
        "card_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("card_version_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(255)),
        sa.Column(
            "report_type",
            controlled_enum(
                "report_type",
                "typo",
                "wrong_answer",
                "outdated_law",
                "bad_explanation",
                "classification_error",
                "duplicate_card",
                "suggestion",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            controlled_enum(
                "card_report_status",
                "open",
                "in_review",
                "approved",
                "rejected",
                "resolved",
                "duplicate",
            ),
            server_default=sa.text("'open'"),
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint(
            "length(message) > 0",
            name="ck_card_reports_message_not_empty",
        ),
        sa.ForeignKeyConstraint(
            ["card_id"], ["cards.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["card_version_id"],
            ["card_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_card_reports_card_id", "card_reports", ["card_id"])
    op.create_index(
        "ix_card_reports_card_version_id",
        "card_reports",
        ["card_version_id"],
    )
    op.create_index("ix_card_reports_user_id", "card_reports", ["user_id"])
    op.create_index(
        "ix_card_reports_status_created",
        "card_reports",
        ["status", "created_at"],
    )

    op.create_table(
        "review_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            controlled_enum(
                "review_task_status",
                "pending",
                "assigned",
                "completed",
                "cancelled",
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("assigned_to", sa.String(255)),
        sa.Column(
            "decision",
            controlled_enum(
                "review_decision",
                "rejected",
                "duplicate",
                "converted_to_new_version",
            ),
        ),
        sa.Column("admin_comment", sa.Text()),
        sa.Column(
            "evidence_reviewed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("resulting_card_version_id", sa.Uuid()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.CheckConstraint(
            "(status = 'completed' AND decision IS NOT NULL "
            "AND assigned_to IS NOT NULL AND admin_comment IS NOT NULL "
            "AND reviewed_at IS NOT NULL) OR "
            "(status <> 'completed' AND decision IS NULL "
            "AND admin_comment IS NULL AND reviewed_at IS NULL)",
            name="ck_review_tasks_valid_review_completion",
        ),
        sa.CheckConstraint(
            "(decision = 'converted_to_new_version' "
            "AND resulting_card_version_id IS NOT NULL) OR "
            "(decision IS NULL AND resulting_card_version_id IS NULL) OR "
            "(decision IN ('rejected', 'duplicate') "
            "AND resulting_card_version_id IS NULL)",
            name="ck_review_tasks_valid_review_result_version",
        ),
        sa.CheckConstraint(
            "admin_comment IS NULL OR length(admin_comment) > 0",
            name="ck_review_tasks_admin_comment_not_empty",
        ),
        sa.ForeignKeyConstraint(
            ["report_id"], ["card_reports.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["resulting_card_version_id"],
            ["card_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
    )
    op.create_index(
        "ix_review_tasks_resulting_card_version_id",
        "review_tasks",
        ["resulting_card_version_id"],
    )
    op.create_index(
        "ix_review_tasks_status_created",
        "review_tasks",
        ["status", "created_at"],
    )

    op.execute(
        """
        CREATE TRIGGER trg_card_reports_version_ownership
        BEFORE INSERT OR UPDATE OF card_id, card_version_id ON card_reports
        FOR EACH ROW EXECUTE FUNCTION enforce_card_version_ownership()
        """
    )
    op.execute(
        """
        CREATE FUNCTION enforce_review_result_version_ownership()
        RETURNS trigger AS $$
        DECLARE
            report_card_id uuid;
            version_card_id uuid;
        BEGIN
            IF NEW.resulting_card_version_id IS NULL THEN
                RETURN NEW;
            END IF;

            SELECT card_id INTO report_card_id
            FROM card_reports
            WHERE id = NEW.report_id;

            SELECT card_id INTO version_card_id
            FROM card_versions
            WHERE id = NEW.resulting_card_version_id;

            IF report_card_id IS DISTINCT FROM version_card_id THEN
                RAISE EXCEPTION
                    'resulting version must belong to the reported card';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_review_result_version_ownership
        BEFORE INSERT OR UPDATE OF report_id, resulting_card_version_id
        ON review_tasks
        FOR EACH ROW EXECUTE FUNCTION enforce_review_result_version_ownership()
        """
    )
    op.execute(
        """
        CREATE FUNCTION prevent_curation_audit_delete()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'curation audit records cannot be deleted';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_card_reports_no_delete
        BEFORE DELETE ON card_reports
        FOR EACH ROW EXECUTE FUNCTION prevent_curation_audit_delete()
        """
    )
    op.execute(
        """
        CREATE FUNCTION protect_card_report_audit()
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
    op.execute(
        """
        CREATE TRIGGER trg_card_reports_audit_immutable
        BEFORE UPDATE ON card_reports
        FOR EACH ROW EXECUTE FUNCTION protect_card_report_audit()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_review_tasks_no_delete
        BEFORE DELETE ON review_tasks
        FOR EACH ROW EXECUTE FUNCTION prevent_curation_audit_delete()
        """
    )
    op.execute(
        """
        CREATE FUNCTION prevent_completed_review_task_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.report_id IS DISTINCT FROM OLD.report_id THEN
                RAISE EXCEPTION 'review task report_id is immutable';
            END IF;
            IF OLD.status = 'completed' THEN
                RAISE EXCEPTION 'completed review tasks are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_completed_review_tasks_immutable
        BEFORE UPDATE ON review_tasks
        FOR EACH ROW EXECUTE FUNCTION prevent_completed_review_task_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_completed_review_tasks_immutable "
        "ON review_tasks"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS prevent_completed_review_task_mutation()"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_card_reports_audit_immutable "
        "ON card_reports"
    )
    op.execute("DROP FUNCTION IF EXISTS protect_card_report_audit()")
    op.execute("DROP TRIGGER IF EXISTS trg_review_tasks_no_delete ON review_tasks")
    op.execute("DROP TRIGGER IF EXISTS trg_card_reports_no_delete ON card_reports")
    op.execute("DROP FUNCTION IF EXISTS prevent_curation_audit_delete()")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_review_result_version_ownership "
        "ON review_tasks"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS enforce_review_result_version_ownership()"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_card_reports_version_ownership "
        "ON card_reports"
    )
    op.drop_table("review_tasks")
    op.drop_table("card_reports")
