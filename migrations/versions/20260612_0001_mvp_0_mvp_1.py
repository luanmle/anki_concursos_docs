"""Create the MVP 0 and MVP 1 database schema.

Revision ID: 20260612_0001
Revises:
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def controlled_enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def upgrade() -> None:
    op.create_table(
        "raw_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("original_file_hash", sa.String(64), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("extraction_status", controlled_enum("document_extraction_status", "pending", "extracted", "failed"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("original_file_hash"),
    )
    op.create_table(
        "disciplines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("parent_id", sa.Uuid()),
        *timestamps(),
        sa.ForeignKeyConstraint(["parent_id"], ["disciplines.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_disciplines_parent_id", "disciplines", ["parent_id"])
    op.create_table(
        "exams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("raw_document_id", sa.Uuid(), nullable=False),
        sa.Column("exam_name", sa.String(255), nullable=False),
        sa.Column("institution", sa.String(255)),
        sa.Column("board", sa.String(100)),
        sa.Column("year", sa.Integer()),
        sa.Column("role", sa.String(255)),
        sa.Column("level", sa.String(100)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("year IS NULL OR year >= 1900", name="ck_exams_valid_year"),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exams_raw_document_id", "exams", ["raw_document_id"])
    op.create_table(
        "topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("discipline_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("parent_id", sa.Uuid()),
        *timestamps(),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discipline_id", "name", name="uq_topic_discipline_name"),
    )
    op.create_index("ix_topics_discipline_id", "topics", ["discipline_id"])
    op.create_index("ix_topics_parent_id", "topics", ["parent_id"])
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("raw_document_id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid()),
        sa.Column("question_number", sa.String(50), nullable=False),
        sa.Column("statement_text", sa.Text(), nullable=False),
        sa.Column("full_raw_text", sa.Text(), nullable=False),
        sa.Column("detected_answer", sa.String(20)),
        sa.Column("official_answer", sa.String(20)),
        sa.Column("extraction_confidence", sa.Float()),
        sa.Column("status", controlled_enum("question_status", "extracted", "needs_review", "reviewed", "archived"), nullable=False),
        *timestamps(),
        sa.CheckConstraint("extraction_confidence IS NULL OR (extraction_confidence >= 0 AND extraction_confidence <= 1)", name="ck_questions_valid_extraction_confidence"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_document_id", "question_number", name="uq_question_document_number"),
    )
    op.create_index("ix_questions_exam_id", "questions", ["exam_id"])
    op.create_index("ix_questions_raw_document_id", "questions", ["raw_document_id"])
    op.create_table(
        "question_alternatives",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(10), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean()),
        *timestamps(),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "label", name="uq_alternative_question_label"),
    )
    op.create_index("ix_question_alternatives_question_id", "question_alternatives", ["question_id"])
    op.create_table(
        "cards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("origin_question_id", sa.Uuid()),
        sa.Column("canonical_key", sa.String(255), nullable=False),
        sa.Column("discipline_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("current_version_id", sa.Uuid()),
        sa.Column("status", controlled_enum("card_status", "generated", "needs_review", "approved", "published", "reported", "revised", "deprecated", "archived"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["origin_question_id"], ["questions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_key"),
    )
    op.create_index("ix_cards_current_version_id", "cards", ["current_version_id"])
    op.create_index("ix_cards_discipline_id", "cards", ["discipline_id"])
    op.create_index("ix_cards_origin_question_id", "cards", ["origin_question_id"])
    op.create_index("ix_cards_topic_id", "cards", ["topic_id"])
    op.create_table(
        "card_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("front_text", sa.Text(), nullable=False),
        sa.Column("back_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("explanation_text", sa.Text(), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("status", controlled_enum("card_version_status", "generated", "needs_review", "approved", "published", "rejected", "superseded"), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        *timestamps(),
        sa.CheckConstraint("version_number > 0", name="ck_card_versions_positive_version_number"),
        sa.CheckConstraint("length(front_text) > 0", name="ck_card_versions_front_not_empty"),
        sa.CheckConstraint("length(back_text) > 0", name="ck_card_versions_back_not_empty"),
        sa.CheckConstraint("length(answer_text) > 0", name="ck_card_versions_answer_not_empty"),
        sa.CheckConstraint("length(explanation_text) > 0", name="ck_card_versions_explanation_not_empty"),
        sa.CheckConstraint("length(change_reason) > 0", name="ck_card_versions_change_reason_not_empty"),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("card_id", "version_number", name="uq_card_version_number"),
    )
    op.create_index("ix_card_versions_card_id", "card_versions", ["card_id"])
    op.create_index("ix_card_versions_content_hash", "card_versions", ["content_hash"])
    op.create_foreign_key("fk_cards_current_version_id_card_versions", "cards", "card_versions", ["current_version_id"], ["id"], ondelete="RESTRICT")
    op.execute(
        """
        CREATE FUNCTION prevent_published_card_version_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.status = 'published' THEN
                RAISE EXCEPTION 'published card versions are immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_card_versions_immutable
        BEFORE UPDATE OR DELETE ON card_versions
        FOR EACH ROW EXECUTE FUNCTION prevent_published_card_version_mutation()
        """
    )
    op.create_table(
        "decks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("discipline_id", sa.Uuid()),
        sa.Column("description", sa.Text()),
        sa.Column("status", controlled_enum("deck_status", "draft", "published", "archived"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_decks_discipline_id", "decks", ["discipline_id"])
    op.create_table(
        "deck_cards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deck_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("card_version_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("removed_at IS NULL OR removed_at >= added_at", name="ck_deck_cards_valid_removal_time"),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["card_version_id"], ["card_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deck_id", "card_id", name="uq_deck_card"),
    )
    op.create_index("ix_deck_cards_card_id", "deck_cards", ["card_id"])
    op.create_index("ix_deck_cards_card_version_id", "deck_cards", ["card_version_id"])
    op.create_index("ix_deck_cards_deck_id", "deck_cards", ["deck_id"])
    op.create_table(
        "releases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deck_id", sa.Uuid(), nullable=False),
        sa.Column("release_number", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text()),
        *timestamps(),
        sa.CheckConstraint("release_number > 0", name="ck_releases_positive_release_number"),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deck_id", "release_number", name="uq_release_deck_number"),
    )
    op.create_index("ix_releases_deck_id", "releases", ["deck_id"])
    op.create_table(
        "release_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("card_version_id", sa.Uuid()),
        sa.Column("action", controlled_enum("release_action", "added", "updated", "removed", "deprecated"), nullable=False),
        *timestamps(),
        sa.CheckConstraint("(action IN ('removed', 'deprecated')) OR card_version_id IS NOT NULL", name="ck_release_items_version_required_for_added_or_updated"),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["card_version_id"], ["card_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_id", "card_id", name="uq_release_item_card"),
    )
    op.create_index("ix_release_items_card_id", "release_items", ["card_id"])
    op.create_index("ix_release_items_card_version_id", "release_items", ["card_version_id"])
    op.create_index("ix_release_items_release_id", "release_items", ["release_id"])
    op.create_index("ix_release_items_release_card", "release_items", ["release_id", "card_id"])


def downgrade() -> None:
    op.drop_table("release_items")
    op.drop_table("releases")
    op.drop_table("deck_cards")
    op.drop_table("decks")
    op.execute("DROP TRIGGER IF EXISTS trg_card_versions_immutable ON card_versions")
    op.execute("DROP FUNCTION IF EXISTS prevent_published_card_version_mutation()")
    op.drop_constraint("fk_cards_current_version_id_card_versions", "cards", type_="foreignkey")
    op.drop_table("card_versions")
    op.drop_table("cards")
    op.drop_table("question_alternatives")
    op.drop_table("questions")
    op.drop_table("topics")
    op.drop_table("exams")
    op.drop_table("disciplines")
    op.drop_table("raw_documents")
