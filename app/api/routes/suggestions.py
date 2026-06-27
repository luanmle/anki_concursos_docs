import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    AuthPrincipal,
    require_authenticated_user,
    require_reviewer,
)
from app.models import User
from app.models.enums import NoteSuggestionStatus
from app.repositories import NoteSuggestionRepository
from app.schemas import (
    NoteSuggestionCreateRequest,
    NoteSuggestionListResponse,
    NoteSuggestionResponse,
    NoteSuggestionReviewRequest,
)
from app.services import NoteSuggestionService

addon_router = APIRouter(prefix="/addon", tags=["addon-suggestions"])
admin_router = APIRouter(
    prefix="/admin/note-suggestions",
    tags=["admin-note-suggestions"],
    dependencies=[Depends(require_reviewer)],
)


def get_note_suggestion_service(
    session: Session = Depends(get_db),
) -> NoteSuggestionService:
    return NoteSuggestionService(NoteSuggestionRepository(session))


@addon_router.post(
    "/cards/{card_id}/suggestions",
    response_model=NoteSuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_card_note_suggestion(
    card_id: uuid.UUID,
    payload: NoteSuggestionCreateRequest,
    user: User = Depends(require_authenticated_user),
    service: NoteSuggestionService = Depends(get_note_suggestion_service),
) -> NoteSuggestionResponse:
    return service.create_for_card(card_id, payload, user)


@addon_router.post(
    "/decks/{deck_id}/note-suggestions",
    response_model=NoteSuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_note_suggestion(
    deck_id: uuid.UUID,
    payload: NoteSuggestionCreateRequest,
    user: User = Depends(require_authenticated_user),
    service: NoteSuggestionService = Depends(get_note_suggestion_service),
) -> NoteSuggestionResponse:
    return service.create_for_deck(deck_id, payload, user)


@admin_router.get("", response_model=NoteSuggestionListResponse)
def list_note_suggestions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: NoteSuggestionStatus | None = Query(default=None, alias="status"),
    service: NoteSuggestionService = Depends(get_note_suggestion_service),
) -> NoteSuggestionListResponse:
    return service.list(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@admin_router.get("/{suggestion_id}", response_model=NoteSuggestionResponse)
def get_note_suggestion(
    suggestion_id: uuid.UUID,
    service: NoteSuggestionService = Depends(get_note_suggestion_service),
) -> NoteSuggestionResponse:
    return service.get(suggestion_id)


@admin_router.post("/{suggestion_id}/review", response_model=NoteSuggestionResponse)
def review_note_suggestion(
    suggestion_id: uuid.UUID,
    payload: NoteSuggestionReviewRequest,
    principal: AuthPrincipal = Depends(require_reviewer),
    service: NoteSuggestionService = Depends(get_note_suggestion_service),
) -> NoteSuggestionResponse:
    return service.review(suggestion_id, payload, reviewed_by=principal.email)
