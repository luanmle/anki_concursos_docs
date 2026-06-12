"""Add processing jobs and card-version ownership checks.

Revision ID: 20260612_0002
Revises: 20260612_0001
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_0002"
down_revision: str | None = "20260612_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def controlled_enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def upgrade() -> None:
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            controlled_enum(
                "processing_job_status",
                "pending",
                "running",
                "succeeded",
                "failed",
                "cancelled",
                "retrying",
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "input_snapshot",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "output_snapshot",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
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
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="ck_processing_jobs_finish_requires_start",
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_processing_jobs_valid_processing_period",
        ),
        sa.CheckConstraint(
            "length(job_type) > 0",
            name="ck_processing_jobs_job_type_not_empty",
        ),
        sa.CheckConstraint(
            "length(entity_type) > 0",
            name="ck_processing_jobs_entity_type_not_empty",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_processing_jobs_entity",
        "processing_jobs",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_processing_jobs_status_created",
        "processing_jobs",
        ["status", "created_at"],
    )

    op.execute(
        """
        CREATE FUNCTION enforce_card_version_ownership()
        RETURNS trigger AS $$
        DECLARE
            owner_card_id uuid;
        BEGIN
            IF NEW.card_version_id IS NULL THEN
                RETURN NEW;
            END IF;

            SELECT card_id INTO owner_card_id
            FROM card_versions
            WHERE id = NEW.card_version_id;

            IF owner_card_id IS DISTINCT FROM NEW.card_id THEN
                RAISE EXCEPTION
                    'card_version_id must reference a version of card_id';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_deck_cards_version_ownership
        BEFORE INSERT OR UPDATE OF card_id, card_version_id ON deck_cards
        FOR EACH ROW EXECUTE FUNCTION enforce_card_version_ownership()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_release_items_version_ownership
        BEFORE INSERT OR UPDATE OF card_id, card_version_id ON release_items
        FOR EACH ROW EXECUTE FUNCTION enforce_card_version_ownership()
        """
    )

    op.execute(
        """
        CREATE FUNCTION enforce_current_card_version_ownership()
        RETURNS trigger AS $$
        DECLARE
            owner_card_id uuid;
        BEGIN
            IF NEW.current_version_id IS NULL THEN
                RETURN NEW;
            END IF;

            SELECT card_id INTO owner_card_id
            FROM card_versions
            WHERE id = NEW.current_version_id;

            IF owner_card_id IS DISTINCT FROM NEW.id THEN
                RAISE EXCEPTION
                    'current_version_id must reference a version of the same card';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_cards_current_version_ownership
        BEFORE INSERT OR UPDATE OF id, current_version_id ON cards
        FOR EACH ROW EXECUTE FUNCTION enforce_current_card_version_ownership()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_cards_current_version_ownership ON cards"
    )
    op.execute("DROP FUNCTION IF EXISTS enforce_current_card_version_ownership()")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_release_items_version_ownership "
        "ON release_items"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_deck_cards_version_ownership ON deck_cards"
    )
    op.execute("DROP FUNCTION IF EXISTS enforce_card_version_ownership()")
    op.drop_table("processing_jobs")
