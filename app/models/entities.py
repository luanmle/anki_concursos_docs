import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    inspect,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    CardKind,
    CardReportStatus,
    CardStatus,
    CardVersionStatus,
    DeckStatus,
    DocumentExtractionStatus,
    ProcessingJobStatus,
    QuestionStatus,
    ReleaseAction,
    ReportType,
    ReviewDecision,
    ReviewTaskStatus,
    UserRole,
)


def enum_column(enum_type: type, name: str) -> Enum:
    return Enum(
        enum_type,
        name=name,
        native_enum=False,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


def generate_public_card_id() -> str:
    return f"AC-{uuid.uuid4().hex.upper()}"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole, "user_role"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    credential_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("length(email) > 3", name="email_not_empty"),
        CheckConstraint("length(display_name) > 0", name="display_name_not_empty"),
        CheckConstraint("length(password_hash) > 0", name="password_hash_not_empty"),
        CheckConstraint(
            "credential_version > 0",
            name="positive_credential_version",
        ),
    )


class RawDocument(TimestampMixin, Base):
    __tablename__ = "raw_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_file_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    raw_text: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    extraction_status: Mapped[DocumentExtractionStatus] = mapped_column(
        enum_column(DocumentExtractionStatus, "document_extraction_status"),
        default=DocumentExtractionStatus.PENDING,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    exams: Mapped[list["Exam"]] = relationship(back_populates="raw_document")
    questions: Mapped[list["Question"]] = relationship(back_populates="raw_document")


class Exam(TimestampMixin, Base):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    exam_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(255))
    board: Mapped[str | None] = mapped_column(String(100))
    year: Mapped[int | None] = mapped_column(Integer)
    role: Mapped[str | None] = mapped_column(String(255))
    level: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    raw_document: Mapped[RawDocument] = relationship(back_populates="exams")
    questions: Mapped[list["Question"]] = relationship(back_populates="exam")

    __table_args__ = (
        CheckConstraint("year IS NULL OR year >= 1900", name="valid_year"),
    )


class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    exam_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("exams.id", ondelete="SET NULL"), index=True
    )
    question_number: Mapped[str] = mapped_column(String(50), nullable=False)
    statement_text: Mapped[str] = mapped_column(Text, nullable=False)
    full_raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    detected_answer: Mapped[str | None] = mapped_column(String(20))
    official_answer: Mapped[str | None] = mapped_column(String(20))
    extraction_confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[QuestionStatus] = mapped_column(
        enum_column(QuestionStatus, "question_status"),
        default=QuestionStatus.EXTRACTED,
        nullable=False,
    )

    raw_document: Mapped[RawDocument] = relationship(back_populates="questions")
    exam: Mapped[Exam | None] = relationship(back_populates="questions")
    alternatives: Mapped[list["QuestionAlternative"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    cards: Mapped[list["Card"]] = relationship(back_populates="origin_question")

    __table_args__ = (
        UniqueConstraint(
            "raw_document_id", "question_number", name="uq_question_document_number"
        ),
        CheckConstraint(
            "extraction_confidence IS NULL OR "
            "(extraction_confidence >= 0 AND extraction_confidence <= 1)",
            name="valid_extraction_confidence",
        ),
    )


class QuestionAlternative(TimestampMixin, Base):
    __tablename__ = "question_alternatives"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)

    question: Mapped[Question] = relationship(back_populates="alternatives")

    __table_args__ = (
        UniqueConstraint("question_id", "label", name="uq_alternative_question_label"),
    )


class Discipline(TimestampMixin, Base):
    __tablename__ = "disciplines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), index=True
    )

    parent: Mapped["Discipline | None"] = relationship(remote_side=[id])
    topics: Mapped[list["Topic"]] = relationship(back_populates="discipline")


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), index=True
    )

    discipline: Mapped[Discipline] = relationship(back_populates="topics")
    parent: Mapped["Topic | None"] = relationship(remote_side=[id])

    __table_args__ = (
        UniqueConstraint("discipline_id", "name", name="uq_topic_discipline_name"),
    )


class Card(TimestampMixin, Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    public_id: Mapped[str] = mapped_column(
        String(35),
        unique=True,
        nullable=False,
        default=generate_public_card_id,
    )
    origin_question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), index=True
    )
    canonical_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    discipline_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), index=True
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), index=True
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "card_versions.id",
            name="fk_cards_current_version_id_card_versions",
            use_alter=True,
            ondelete="RESTRICT",
        ),
        index=True,
    )
    status: Mapped[CardStatus] = mapped_column(
        enum_column(CardStatus, "card_status"),
        default=CardStatus.GENERATED,
        nullable=False,
    )
    card_kind: Mapped[CardKind] = mapped_column(
        enum_column(CardKind, "card_kind"),
        default=CardKind.BASIC,
        server_default=CardKind.BASIC.value,
        index=True,
        nullable=False,
    )

    origin_question: Mapped[Question | None] = relationship(back_populates="cards")
    discipline: Mapped[Discipline] = relationship()
    topic: Mapped[Topic] = relationship()
    versions: Mapped[list["CardVersion"]] = relationship(
        back_populates="card",
        foreign_keys="CardVersion.card_id",
    )
    current_version: Mapped["CardVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )


class CardVersion(TimestampMixin, Base):
    __tablename__ = "card_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    front_text: Mapped[str] = mapped_column(Text, nullable=False)
    back_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str | None] = mapped_column(String(255), index=True)
    template_name: Mapped[str | None] = mapped_column(String(255), index=True)
    anki_fields: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    anki_template: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    anki_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_note_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_note_guid: Mapped[str | None] = mapped_column(String(255), index=True)
    source_deck_path: Mapped[str | None] = mapped_column(Text)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CardVersionStatus] = mapped_column(
        enum_column(CardVersionStatus, "card_version_status"),
        default=CardVersionStatus.GENERATED,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    card: Mapped[Card] = relationship(
        back_populates="versions", foreign_keys=[card_id]
    )

    __table_args__ = (
        UniqueConstraint("card_id", "version_number", name="uq_card_version_number"),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint("length(front_text) > 0", name="front_not_empty"),
        CheckConstraint("length(back_text) > 0", name="back_not_empty"),
        CheckConstraint("length(answer_text) > 0", name="answer_not_empty"),
        CheckConstraint("length(change_reason) > 0", name="change_reason_not_empty"),
    )


class CardReport(TimestampMixin, Base):
    __tablename__ = "card_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    card_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("card_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reporter_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    report_type: Mapped[ReportType] = mapped_column(
        enum_column(ReportType, "report_type"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CardReportStatus] = mapped_column(
        enum_column(CardReportStatus, "card_report_status"),
        default=CardReportStatus.OPEN,
        server_default=CardReportStatus.OPEN.value,
        nullable=False,
    )

    card: Mapped[Card] = relationship()
    card_version: Mapped[CardVersion] = relationship()
    review_task: Mapped["ReviewTask"] = relationship(
        back_populates="report",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("length(message) > 0", name="message_not_empty"),
        Index("ix_card_reports_status_created", "status", "created_at"),
    )


class ReviewTask(TimestampMixin, Base):
    __tablename__ = "review_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("card_reports.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    status: Mapped[ReviewTaskStatus] = mapped_column(
        enum_column(ReviewTaskStatus, "review_task_status"),
        default=ReviewTaskStatus.PENDING,
        server_default=ReviewTaskStatus.PENDING.value,
        nullable=False,
    )
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    decision: Mapped[ReviewDecision | None] = mapped_column(
        enum_column(ReviewDecision, "review_decision")
    )
    admin_comment: Mapped[str | None] = mapped_column(Text)
    evidence_reviewed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    resulting_card_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("card_versions.id", ondelete="RESTRICT"), index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    report: Mapped[CardReport] = relationship(back_populates="review_task")
    resulting_card_version: Mapped[CardVersion | None] = relationship()

    __table_args__ = (
        CheckConstraint(
            "(status = 'completed' AND decision IS NOT NULL "
            "AND assigned_to IS NOT NULL AND admin_comment IS NOT NULL "
            "AND reviewed_at IS NOT NULL) OR "
            "(status <> 'completed' AND decision IS NULL "
            "AND admin_comment IS NULL AND reviewed_at IS NULL)",
            name="valid_review_completion",
        ),
        CheckConstraint(
            "(decision = 'converted_to_new_version' "
            "AND resulting_card_version_id IS NOT NULL) OR "
            "(decision IS NULL AND resulting_card_version_id IS NULL) OR "
            "(decision IN ('rejected', 'duplicate') "
            "AND resulting_card_version_id IS NULL)",
            name="valid_review_result_version",
        ),
        CheckConstraint(
            "admin_comment IS NULL OR length(admin_comment) > 0",
            name="admin_comment_not_empty",
        ),
        Index("ix_review_tasks_status_created", "status", "created_at"),
    )


class Deck(TimestampMixin, Base):
    __tablename__ = "decks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    discipline_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DeckStatus] = mapped_column(
        enum_column(DeckStatus, "deck_status"),
        default=DeckStatus.DRAFT,
        nullable=False,
    )

    discipline: Mapped[Discipline | None] = relationship()
    cards: Mapped[list["DeckCard"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["DeckSnapshot"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )
    releases: Mapped[list["Release"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["DeckSubscription"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )


class DeckSubscription(TimestampMixin, Base):
    __tablename__ = "deck_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
    deck: Mapped[Deck] = relationship(back_populates="subscriptions")

    __table_args__ = (
        UniqueConstraint("user_id", "deck_id", name="uq_deck_subscription_user_deck"),
    )


class DeckSnapshot(TimestampMixin, Base):
    __tablename__ = "deck_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    note_count: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        "payload", JSON, default=dict, nullable=False
    )
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("releases.id", ondelete="SET NULL"), index=True
    )

    deck: Mapped[Deck] = relationship(back_populates="snapshots")
    release: Mapped["Release | None"] = relationship()

    __table_args__ = (
        CheckConstraint("note_count >= 0", name="non_negative_note_count"),
    )


class DeckTemplate(TimestampMixin, Base):
    __tablename__ = "deck_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_key: Mapped[str] = mapped_column(String(255), nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    note_type: Mapped[str] = mapped_column(String(255), nullable=False)
    card_kind: Mapped[CardKind] = mapped_column(
        enum_column(CardKind, "deck_template_card_kind"), nullable=False
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deck_template_versions.id", ondelete="SET NULL"), index=True
    )

    deck: Mapped[Deck] = relationship()
    versions: Mapped[list["DeckTemplateVersion"]] = relationship(
        back_populates="template",
        foreign_keys="DeckTemplateVersion.deck_template_id",
    )
    current_version: Mapped["DeckTemplateVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )

    __table_args__ = (
        UniqueConstraint("deck_id", "template_key", name="uq_deck_template_key"),
        UniqueConstraint("deck_id", "template_name", name="uq_deck_template_name"),
        CheckConstraint("length(template_key) > 0", name="template_key_not_empty"),
        CheckConstraint("length(template_name) > 0", name="template_name_not_empty"),
        CheckConstraint("length(note_type) > 0", name="template_note_type_not_empty"),
    )


class DeckTemplateVersion(TimestampMixin, Base):
    __tablename__ = "deck_template_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deck_template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deck_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fields: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    field_mapping: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    front_html: Mapped[str] = mapped_column(Text, nullable=False)
    back_html: Mapped[str] = mapped_column(Text, nullable=False)
    styling_css: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="published", nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    template: Mapped[DeckTemplate] = relationship(
        back_populates="versions",
        foreign_keys=[deck_template_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "deck_template_id", "version_number", name="uq_deck_template_version"
        ),
        CheckConstraint("version_number > 0", name="positive_template_version_number"),
        CheckConstraint("length(front_html) > 0", name="template_front_not_empty"),
        CheckConstraint("length(back_html) > 0", name="template_back_not_empty"),
        CheckConstraint("length(content_hash) = 64", name="template_hash_length"),
        CheckConstraint("length(created_by) > 0", name="template_created_by_not_empty"),
    )


class DeckCard(Base):
    __tablename__ = "deck_cards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    card_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("card_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removal_action: Mapped[ReleaseAction | None] = mapped_column(
        enum_column(ReleaseAction, "deck_card_removal_action")
    )

    deck: Mapped[Deck] = relationship(back_populates="cards")
    card: Mapped[Card] = relationship()
    card_version: Mapped[CardVersion] = relationship()

    __table_args__ = (
        UniqueConstraint("deck_id", "card_id", name="uq_deck_card"),
        CheckConstraint(
            "removed_at IS NULL OR removed_at >= added_at", name="valid_removal_time"
        ),
        CheckConstraint(
            "(removed_at IS NULL AND removal_action IS NULL) OR "
            "(removed_at IS NOT NULL AND removal_action IN ('removed', 'deprecated'))",
            name="valid_removal_action",
        ),
    )


class Release(TimestampMixin, Base):
    __tablename__ = "releases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deck_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("decks.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    release_number: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)

    deck: Mapped[Deck] = relationship(back_populates="releases")
    items: Mapped[list["ReleaseItem"]] = relationship(
        back_populates="release", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("deck_id", "release_number", name="uq_release_deck_number"),
        CheckConstraint("release_number > 0", name="positive_release_number"),
    )


class ReleaseItem(TimestampMixin, Base):
    __tablename__ = "release_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    card_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("card_versions.id", ondelete="RESTRICT"), index=True
    )
    action: Mapped[ReleaseAction] = mapped_column(
        enum_column(ReleaseAction, "release_action"), nullable=False
    )

    release: Mapped[Release] = relationship(back_populates="items")
    card: Mapped[Card] = relationship()
    card_version: Mapped[CardVersion | None] = relationship()

    __table_args__ = (
        UniqueConstraint("release_id", "card_id", name="uq_release_item_card"),
        CheckConstraint(
            "(action IN ('removed', 'deprecated')) OR card_version_id IS NOT NULL",
            name="version_required_for_added_or_updated",
        ),
    )


Index("ix_release_items_release_card", ReleaseItem.release_id, ReleaseItem.card_id)


class ProcessingJob(TimestampMixin, Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[ProcessingJobStatus] = mapped_column(
        enum_column(ProcessingJobStatus, "processing_job_status"),
        default=ProcessingJobStatus.PENDING,
        server_default=ProcessingJobStatus.PENDING.value,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'"), nullable=False
    )
    output_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'"), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NOT NULL",
            name="finish_requires_start",
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="valid_processing_period",
        ),
        CheckConstraint("length(job_type) > 0", name="job_type_not_empty"),
        CheckConstraint("length(entity_type) > 0", name="entity_type_not_empty"),
        Index("ix_processing_jobs_entity", "entity_type", "entity_id"),
        Index("ix_processing_jobs_status_created", "status", "created_at"),
    )


def _assert_card_version_ownership(
    connection, card_id: uuid.UUID, card_version_id: uuid.UUID | None, field: str
) -> None:
    if card_version_id is None:
        return
    version_card_id = connection.execute(
        CardVersion.__table__.select()
        .with_only_columns(CardVersion.card_id)
        .where(CardVersion.id == card_version_id)
    ).scalar_one_or_none()
    if version_card_id is not None and version_card_id != card_id:
        raise ValueError(f"{field} must reference a version of the same card")


@event.listens_for(Card, "before_insert")
@event.listens_for(Card, "before_update")
def validate_current_version_ownership(_mapper, connection, target: Card) -> None:
    _assert_card_version_ownership(
        connection, target.id, target.current_version_id, "current_version_id"
    )


@event.listens_for(Card, "before_update")
def prevent_public_card_id_update(_mapper, _connection, target: Card) -> None:
    if inspect(target).attrs.public_id.history.has_changes():
        raise ValueError("public_id is immutable")


@event.listens_for(DeckCard, "before_insert")
@event.listens_for(DeckCard, "before_update")
def validate_deck_card_version_ownership(
    _mapper, connection, target: DeckCard
) -> None:
    _assert_card_version_ownership(
        connection, target.card_id, target.card_version_id, "card_version_id"
    )


@event.listens_for(ReleaseItem, "before_insert")
@event.listens_for(ReleaseItem, "before_update")
def validate_release_item_version_ownership(
    _mapper, connection, target: ReleaseItem
) -> None:
    _assert_card_version_ownership(
        connection, target.card_id, target.card_version_id, "card_version_id"
    )


@event.listens_for(CardReport, "before_insert")
@event.listens_for(CardReport, "before_update")
def validate_card_report_version_ownership(
    _mapper, connection, target: CardReport
) -> None:
    _assert_card_version_ownership(
        connection, target.card_id, target.card_version_id, "card_version_id"
    )


@event.listens_for(ReviewTask, "before_insert")
@event.listens_for(ReviewTask, "before_update")
def validate_review_result_version_ownership(
    _mapper, connection, target: ReviewTask
) -> None:
    if target.resulting_card_version_id is None:
        return
    report_card_id = connection.execute(
        CardReport.__table__.select()
        .with_only_columns(CardReport.card_id)
        .where(CardReport.id == target.report_id)
    ).scalar_one_or_none()
    _assert_card_version_ownership(
        connection,
        report_card_id,
        target.resulting_card_version_id,
        "resulting_card_version_id",
    )


@event.listens_for(CardVersion, "before_update")
def prevent_published_version_update(_mapper, _connection, target: CardVersion) -> None:
    status_history = inspect(target).attrs.status.history
    was_published = (
        CardVersionStatus.PUBLISHED in status_history.deleted
        or (
            not status_history.has_changes()
            and target.status == CardVersionStatus.PUBLISHED
        )
    )
    if was_published:
        raise ValueError("Published card versions are immutable")


@event.listens_for(CardVersion, "before_delete")
def prevent_published_version_delete(_mapper, _connection, target: CardVersion) -> None:
    if target.status == CardVersionStatus.PUBLISHED:
        raise ValueError("Published card versions cannot be deleted")


@event.listens_for(Release, "before_update")
@event.listens_for(Release, "before_delete")
def prevent_release_mutation(_mapper, _connection, _target: Release) -> None:
    raise ValueError("Published releases are immutable")


@event.listens_for(ReleaseItem, "before_update")
@event.listens_for(ReleaseItem, "before_delete")
def prevent_release_item_mutation(
    _mapper, _connection, _target: ReleaseItem
) -> None:
    raise ValueError("Published release items are immutable")


@event.listens_for(CardReport, "before_delete")
def prevent_card_report_delete(_mapper, _connection, _target: CardReport) -> None:
    raise ValueError("Card reports cannot be deleted")


@event.listens_for(CardReport, "before_update")
def protect_card_report_audit_fields(
    _mapper, _connection, target: CardReport
) -> None:
    state = inspect(target)
    immutable_fields = (
        "card_id",
        "card_version_id",
        "reporter_reference",
        "report_type",
        "message",
    )
    if any(state.attrs[field].history.has_changes() for field in immutable_fields):
        raise ValueError("Card report content is immutable")
    status_history = state.attrs.status.history
    terminal_statuses = {
        CardReportStatus.REJECTED,
        CardReportStatus.RESOLVED,
        CardReportStatus.DUPLICATE,
    }
    if any(status in terminal_statuses for status in status_history.deleted):
        raise ValueError("Reviewed card reports are immutable")


@event.listens_for(ReviewTask, "before_update")
def prevent_completed_review_task_update(
    _mapper, _connection, target: ReviewTask
) -> None:
    state = inspect(target)
    if state.attrs.report_id.history.has_changes():
        raise ValueError("Review task report_id is immutable")
    status_history = state.attrs.status.history
    was_completed = (
        ReviewTaskStatus.COMPLETED in status_history.deleted
        or (
            not status_history.has_changes()
            and target.status == ReviewTaskStatus.COMPLETED
        )
    )
    if was_completed:
        raise ValueError("Completed review tasks are immutable")


@event.listens_for(ReviewTask, "before_delete")
def prevent_review_task_delete(_mapper, _connection, _target: ReviewTask) -> None:
    raise ValueError("Review tasks cannot be deleted")
