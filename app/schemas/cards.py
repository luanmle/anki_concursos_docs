import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CardStatus, CardVersionStatus


class CardContentInput(BaseModel):
    front_text: str = Field(min_length=1)
    back_text: str = Field(min_length=1)
    answer_text: str = Field(min_length=1)
    explanation_text: str = Field(min_length=1)

    @field_validator(
        "front_text",
        "back_text",
        "answer_text",
        "explanation_text",
        mode="before",
    )
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CardCreateRequest(CardContentInput):
    canonical_key: str = Field(min_length=1, max_length=255)
    discipline_id: uuid.UUID
    topic_id: uuid.UUID
    change_reason: str = Field(default="Versao inicial", min_length=1)
    created_by: str = Field(min_length=1, max_length=255)

    @field_validator("canonical_key", "change_reason", "created_by", mode="before")
    @classmethod
    def strip_card_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CardVersionCreateRequest(CardContentInput):
    change_reason: str = Field(min_length=1)
    created_by: str = Field(min_length=1, max_length=255)

    @field_validator("change_reason", "created_by", mode="before")
    @classmethod
    def strip_version_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CardVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_version_id: uuid.UUID
    version_number: int
    front_text: str
    back_text: str
    answer_text: str
    explanation_text: str
    change_reason: str
    created_by: str
    status: CardVersionStatus
    content_hash: str
    created_at: datetime


class CardSummaryResponse(BaseModel):
    card_id: uuid.UUID
    public_id: str
    canonical_key: str
    discipline_id: uuid.UUID
    topic_id: uuid.UUID
    status: CardStatus
    current_version: CardVersionResponse | None
    created_at: datetime
    updated_at: datetime


class CardDetailResponse(CardSummaryResponse):
    versions: list[CardVersionResponse]


class CardListResponse(BaseModel):
    items: list[CardSummaryResponse]
    page: int
    page_size: int
    total: int
    pages: int


PublicCardVersionResponse = CardVersionResponse
PublicCardResponse = CardSummaryResponse
