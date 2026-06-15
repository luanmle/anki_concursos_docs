import uuid
from datetime import datetime

from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.models.enums import (
    CardReportStatus,
    ReportType,
    ReviewDecision,
    ReviewTaskStatus,
)


class ReportCreateRequest(BaseModel):
    card_id: uuid.UUID
    card_version_id: uuid.UUID
    reporter_reference: str | None = Field(
        default=None,
        max_length=255,
        validation_alias=AliasChoices("reporter_reference", "user_id"),
    )
    report_type: ReportType
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("reporter_reference", "message", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CuratedVersionInput(BaseModel):
    front_text: str = Field(min_length=1, max_length=20_000)
    back_text: str = Field(min_length=1, max_length=20_000)
    answer_text: str = Field(min_length=1, max_length=20_000)
    explanation_text: str = Field(min_length=1, max_length=20_000)
    change_reason: str = Field(min_length=1, max_length=2000)

    @field_validator(
        "front_text",
        "back_text",
        "answer_text",
        "explanation_text",
        "change_reason",
        mode="before",
    )
    @classmethod
    def strip_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ReportReviewRequest(BaseModel):
    decision: ReviewDecision
    reviewed_by: str = Field(min_length=1, max_length=255)
    admin_comment: str = Field(min_length=1, max_length=5000)
    evidence_reviewed: bool = False
    proposed_version: CuratedVersionInput | None = None

    @field_validator("reviewed_by", "admin_comment", mode="before")
    @classmethod
    def strip_review_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_proposed_version(self) -> "ReportReviewRequest":
        converts = self.decision == ReviewDecision.CONVERTED_TO_NEW_VERSION
        if converts and self.proposed_version is None:
            raise ValueError(
                "proposed_version is required when converting a report"
            )
        if not converts and self.proposed_version is not None:
            raise ValueError(
                "proposed_version is only allowed when converting a report"
            )
        return self


class ReviewTaskResponse(BaseModel):
    review_task_id: uuid.UUID
    status: ReviewTaskStatus
    assigned_to: str | None
    decision: ReviewDecision | None
    admin_comment: str | None
    evidence_reviewed: bool
    resulting_card_version_id: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CardReportResponse(BaseModel):
    report_id: uuid.UUID
    card_id: uuid.UUID
    public_id: str
    card_version_id: uuid.UUID
    version_number: int
    reporter_reference: str | None
    report_type: ReportType
    message: str
    status: CardReportStatus
    review_task: ReviewTaskResponse
    created_at: datetime
    updated_at: datetime


class CardReportListResponse(BaseModel):
    items: list[CardReportResponse]
    page: int
    page_size: int
    total: int
    pages: int
