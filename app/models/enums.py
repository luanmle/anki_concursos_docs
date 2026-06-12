from enum import StrEnum


class DocumentExtractionStatus(StrEnum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    FAILED = "failed"


class QuestionStatus(StrEnum):
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class CardStatus(StrEnum):
    GENERATED = "generated"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REPORTED = "reported"
    REVISED = "revised"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class CardVersionStatus(StrEnum):
    GENERATED = "generated"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class DeckStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReleaseAction(StrEnum):
    ADDED = "added"
    UPDATED = "updated"
    REMOVED = "removed"
    DEPRECATED = "deprecated"

