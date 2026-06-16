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


class CardKind(StrEnum):
    BASIC = "basic"
    CLOZE = "cloze"


class DeckStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReleaseAction(StrEnum):
    ADDED = "added"
    UPDATED = "updated"
    REMOVED = "removed"
    DEPRECATED = "deprecated"


class ProcessingJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ReportType(StrEnum):
    TYPO = "typo"
    WRONG_ANSWER = "wrong_answer"
    OUTDATED_LAW = "outdated_law"
    BAD_EXPLANATION = "bad_explanation"
    CLASSIFICATION_ERROR = "classification_error"
    DUPLICATE_CARD = "duplicate_card"
    SUGGESTION = "suggestion"


class CardReportStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RESOLVED = "resolved"
    DUPLICATE = "duplicate"


class ReviewTaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReviewDecision(StrEnum):
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    CONVERTED_TO_NEW_VERSION = "converted_to_new_version"


class UserRole(StrEnum):
    ADMIN = "admin"
    CURATOR = "curator"
    REVIEWER = "reviewer"
