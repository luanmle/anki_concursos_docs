import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    AuthPrincipal,
    require_curator,
    require_reviewer,
    require_staff,
)
from app.models.enums import CardStatus
from app.repositories import CardRepository
from app.schemas import (
    CardCreateRequest,
    CardCsvImportRequest,
    CardCsvImportResponse,
    CardDetailResponse,
    CardListResponse,
    CardSummaryResponse,
    CardVersionCreateRequest,
    CardVersionResponse,
)
from app.services import CardService

router = APIRouter(prefix="/cards", tags=["cards"])
import_router = APIRouter(prefix="/card-imports", tags=["card-imports"])


def get_card_service(
    session: Session = Depends(get_db, use_cache=False),
) -> CardService:
    return CardService(CardRepository(session))


@router.post("", response_model=CardDetailResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreateRequest,
    principal: AuthPrincipal = Depends(require_curator),
    service: CardService = Depends(get_card_service),
) -> CardDetailResponse:
    return service.create_card(
        payload.model_copy(update={"created_by": principal.email})
    )


@import_router.post("/csv", response_model=CardCsvImportResponse)
def import_cards_csv(
    payload: CardCsvImportRequest,
    principal: AuthPrincipal = Depends(require_curator),
    service: CardService = Depends(get_card_service),
) -> CardCsvImportResponse:
    return service.import_csv(payload, created_by=principal.email)


@router.get("", response_model=CardListResponse)
def list_cards(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    discipline_id: uuid.UUID | None = None,
    topic_id: uuid.UUID | None = None,
    status_filter: CardStatus | None = Query(default=None, alias="status"),
    public_id: str | None = None,
    _principal: AuthPrincipal = Depends(require_staff),
    service: CardService = Depends(get_card_service),
) -> CardListResponse:
    return service.list_cards(
        page=page,
        page_size=page_size,
        discipline_id=discipline_id,
        topic_id=topic_id,
        status_filter=status_filter,
        public_id=public_id,
    )


@router.get("/public/{public_id}", response_model=CardSummaryResponse)
def get_public_card(
    public_id: str,
    service: CardService = Depends(get_card_service),
) -> CardSummaryResponse:
    return service.get_public_card(public_id)


@router.get("/{card_id}", response_model=CardDetailResponse)
def get_card(
    card_id: uuid.UUID,
    _principal: AuthPrincipal = Depends(require_staff),
    service: CardService = Depends(get_card_service),
) -> CardDetailResponse:
    return service.get_card(card_id)


@router.post(
    "/{card_id}/versions",
    response_model=CardVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_card_version(
    card_id: uuid.UUID,
    payload: CardVersionCreateRequest,
    principal: AuthPrincipal = Depends(require_curator),
    service: CardService = Depends(get_card_service),
) -> CardVersionResponse:
    return service.create_version(
        card_id,
        payload.model_copy(update={"created_by": principal.email}),
    )


@router.post(
    "/{card_id}/versions/{version_id}/approve",
    response_model=CardDetailResponse,
)
def approve_card_version(
    card_id: uuid.UUID,
    version_id: uuid.UUID,
    _principal: AuthPrincipal = Depends(require_reviewer),
    service: CardService = Depends(get_card_service),
) -> CardDetailResponse:
    return service.approve_version(card_id, version_id)


@router.post(
    "/{card_id}/versions/{version_id}/publish",
    response_model=CardDetailResponse,
)
def publish_card_version(
    card_id: uuid.UUID,
    version_id: uuid.UUID,
    _principal: AuthPrincipal = Depends(require_reviewer),
    service: CardService = Depends(get_card_service),
) -> CardDetailResponse:
    return service.publish_version(card_id, version_id)
