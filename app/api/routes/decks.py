import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_curator, require_reviewer, require_staff
from app.repositories import DeckRepository
from app.schemas import (
    DeckCardAddRequest,
    DeckCardRemoveRequest,
    DeckCreateRequest,
    DeckListResponse,
    DeckResponse,
    DeckSyncResponse,
    ReleaseListResponse,
    ReleasePublishRequest,
    ReleaseResponse,
)
from app.services import DeckService

router = APIRouter(prefix="/decks", tags=["decks"])


def get_deck_service(session: Session = Depends(get_db)) -> DeckService:
    return DeckService(DeckRepository(session))


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def create_deck(
    payload: DeckCreateRequest,
    _principal=Depends(require_curator),
    service: DeckService = Depends(get_deck_service),
) -> DeckResponse:
    return service.create_deck(payload)


@router.get("", response_model=DeckListResponse)
def list_decks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _principal=Depends(require_staff),
    service: DeckService = Depends(get_deck_service),
) -> DeckListResponse:
    return service.list_decks(page=page, page_size=page_size)


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(
    deck_id: uuid.UUID,
    _principal=Depends(require_staff),
    service: DeckService = Depends(get_deck_service),
) -> DeckResponse:
    return service.get_deck(deck_id)


@router.post("/{deck_id}/cards", response_model=DeckResponse)
def add_card_to_deck(
    deck_id: uuid.UUID,
    payload: DeckCardAddRequest,
    _principal=Depends(require_curator),
    service: DeckService = Depends(get_deck_service),
) -> DeckResponse:
    return service.add_card(deck_id, payload.card_id)


@router.post("/{deck_id}/cards/{card_id}/remove", response_model=DeckResponse)
def remove_card_from_deck(
    deck_id: uuid.UUID,
    card_id: uuid.UUID,
    payload: DeckCardRemoveRequest,
    _principal=Depends(require_curator),
    service: DeckService = Depends(get_deck_service),
) -> DeckResponse:
    return service.remove_card(deck_id, card_id, payload.action)


@router.post(
    "/{deck_id}/publish-release",
    response_model=ReleaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def publish_release(
    deck_id: uuid.UUID,
    payload: ReleasePublishRequest,
    _principal=Depends(require_reviewer),
    service: DeckService = Depends(get_deck_service),
) -> ReleaseResponse:
    return service.publish_release(deck_id, payload)


@router.get("/{deck_id}/releases", response_model=ReleaseListResponse)
def list_releases(
    deck_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _principal=Depends(require_staff),
    service: DeckService = Depends(get_deck_service),
) -> ReleaseListResponse:
    return service.list_releases(
        deck_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{deck_id}/sync", response_model=DeckSyncResponse)
def sync_deck(
    deck_id: uuid.UUID,
    since_release: int = Query(default=0, ge=0),
    _principal=Depends(require_staff),
    service: DeckService = Depends(get_deck_service),
) -> DeckSyncResponse:
    return service.sync(deck_id, since_release=since_release)


@router.get("/{deck_id}/releases/{release_id}/export.csv")
def export_release_csv(
    deck_id: uuid.UUID,
    release_id: uuid.UUID,
    delimiter: Literal["comma", "semicolon", "tab"] = Query("comma"),
    include_tags: bool = Query(True),
    _principal=Depends(require_staff),
    service: DeckService = Depends(get_deck_service),
) -> Response:
    release, csv_export = service.export_release_csv(
        deck_id,
        release_id,
        delimiter_name=delimiter,
        include_tags=include_tags,
    )
    filename = f"deck-{deck_id}-release-{release.release_number}.csv"
    return Response(
        content=csv_export.content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-SHA256": csv_export.sha256,
            "X-Row-Count": str(csv_export.row_count),
            "X-Release-Number": str(release.release_number),
        },
    )
