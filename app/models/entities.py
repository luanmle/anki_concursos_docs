import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    CardStatus,
    CardVersionStatus,
    DeckStatus,
    DocumentExtractionStatus,
    QuestionStatus,
    ReleaseAction,
)


def enum_column(enum_type: type, name: str) -> Enum:
    return Enum(
        enum_type,
        name=name,
        native_enum=False,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


class RawDocument(TimestampMixin, Base):
    __tablename__ = "raw_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
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
    origin_question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), index=True
    )
    canonical_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False, index=True
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
        CheckConstraint("length(explanation_text) > 0", name="explanation_not_empty"),
        CheckConstraint("length(change_reason) > 0", name="change_reason_not_empty"),
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
    releases: Mapped[list["Release"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
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

    deck: Mapped[Deck] = relationship(back_populates="cards")
    card: Mapped[Card] = relationship()
    card_version: Mapped[CardVersion] = relationship()

    __table_args__ = (
        UniqueConstraint("deck_id", "card_id", name="uq_deck_card"),
        CheckConstraint(
            "removed_at IS NULL OR removed_at >= added_at", name="valid_removal_time"
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


@event.listens_for(CardVersion, "before_update")
def prevent_published_version_update(_mapper, _connection, target: CardVersion) -> None:
    status_history = inspect(target).attrs.status.history
    was_published = (
        target.status == CardVersionStatus.PUBLISHED
        or CardVersionStatus.PUBLISHED in status_history.deleted
    )
    if was_published:
        raise ValueError("Published card versions are immutable")


@event.listens_for(CardVersion, "before_delete")
def prevent_published_version_delete(_mapper, _connection, target: CardVersion) -> None:
    if target.status == CardVersionStatus.PUBLISHED:
        raise ValueError("Published card versions cannot be deleted")
