import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CardKind, CardStatus, CardVersionStatus


class CardContentInput(BaseModel):
    card_kind: CardKind = CardKind.BASIC
    front_text: str = Field(min_length=1, max_length=20_000)
    back_text: str = Field(min_length=1, max_length=20_000)
    answer_text: str = Field(min_length=1, max_length=20_000)
    explanation_text: str = Field(min_length=1, max_length=20_000)

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
    change_reason: str = Field(
        default="Versao inicial",
        min_length=1,
        max_length=2000,
    )
    created_by: str = Field(min_length=1, max_length=255)

    @field_validator("canonical_key", "change_reason", "created_by", mode="before")
    @classmethod
    def strip_card_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CardVersionCreateRequest(CardContentInput):
    change_reason: str = Field(min_length=1, max_length=2000)
    created_by: str = Field(min_length=1, max_length=255)

    @field_validator("change_reason", "created_by", mode="before")
    @classmethod
    def strip_version_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CardCsvImportRequest(BaseModel):
    csv_text: str = Field(min_length=1, max_length=2_000_000)
    delimiter: str = Field(default=",", min_length=1, max_length=1)
    dry_run: bool = False
    default_change_reason: str = Field(
        default="Importação CSV",
        min_length=1,
        max_length=2000,
    )

    @field_validator("csv_text", "default_change_reason", mode="before")
    @classmethod
    def strip_csv_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CardCsvImportRowResult(BaseModel):
    row_number: int
    status: str
    message: str
    card_kind: CardKind | None = None
    public_id: str | None = None
    card_id: uuid.UUID | None = None
    card_version_id: uuid.UUID | None = None


class CardCsvImportResponse(BaseModel):
    dry_run: bool
    total_rows: int
    created: int
    duplicates: int
    errors: int
    items: list[CardCsvImportRowResult]


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
    card_kind: CardKind
    note_type: str
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
