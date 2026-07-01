import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import NoteSuggestionStatus, NoteSuggestionType


class NoteSuggestionCreateRequest(BaseModel):
    suggestion_type: NoteSuggestionType
    fields: dict[str, Any] = Field(default_factory=dict)
    added_tags: list[str] = Field(default_factory=list)
    removed_tags: list[str] = Field(default_factory=list)
    comment: str = Field(min_length=1, max_length=5000)
    source: str | None = Field(default=None, max_length=255)

    @field_validator("comment", "source", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("added_tags", "removed_tags", mode="after")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        normalized: list[str] = []
        for item in value:
            tag = item.strip() if isinstance(item, str) else ""
            if tag and tag not in seen:
                seen.add(tag)
                normalized.append(tag)
        return normalized

    @model_validator(mode="after")
    def require_payload_delta(self) -> "NoteSuggestionCreateRequest":
        if (
            self.suggestion_type != NoteSuggestionType.DELETE
            and not self.fields
            and not self.added_tags
            and not self.removed_tags
        ):
            raise ValueError("fields or tag changes are required")
        return self


class NoteSuggestionReviewRequest(BaseModel):
    status: NoteSuggestionStatus
    review_comment: str | None = Field(default=None, min_length=1, max_length=5000)
    resulting_card_version_id: uuid.UUID | None = None

    @field_validator("review_comment", mode="before")
    @classmethod
    def strip_comment(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_terminal_status(self) -> "NoteSuggestionReviewRequest":
        if self.status == NoteSuggestionStatus.PENDING:
            raise ValueError("review status must be accepted or rejected")
        return self


class NoteSuggestionResponse(BaseModel):
    suggestion_id: uuid.UUID
    deck_id: uuid.UUID | None
    card_id: uuid.UUID | None
    public_id: str | None
    card_version_id: uuid.UUID | None
    version_number: int | None
    submitted_by_user_id: uuid.UUID
    submitted_by_email: str
    suggestion_type: NoteSuggestionType
    status: NoteSuggestionStatus
    fields: dict[str, Any]
    added_tags: list[str]
    removed_tags: list[str]
    comment: str
    source: str | None
    reviewed_by: str | None
    review_comment: str | None
    reviewed_at: datetime | None
    resulting_card_version_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class NoteSuggestionListResponse(BaseModel):
    items: list[NoteSuggestionResponse]
    page: int
    page_size: int
    total: int
    pages: int


class NoteSuggestionCommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

    @field_validator("body", mode="before")
    @classmethod
    def strip_body(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class NoteSuggestionCommentResponse(BaseModel):
    comment_id: uuid.UUID
    suggestion_id: uuid.UUID
    author_user_id: uuid.UUID
    author_email: str
    body: str
    created_at: datetime


class NoteSuggestionCommentListResponse(BaseModel):
    items: list[NoteSuggestionCommentResponse]
    total: int


class NoteCommentResponse(BaseModel):
    comment_id: uuid.UUID
    card_id: uuid.UUID
    author_user_id: uuid.UUID
    author_email: str
    body: str
    created_at: datetime


class NoteCommentListResponse(BaseModel):
    items: list[NoteCommentResponse]
    total: int
