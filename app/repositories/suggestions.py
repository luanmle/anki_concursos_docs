import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Card, Deck, NoteSuggestion
from app.models.enums import CardStatus, DeckStatus, NoteSuggestionStatus


class NoteSuggestionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_published_card(self, card_id: uuid.UUID) -> Card | None:
        return self.session.scalar(
            select(Card)
            .options(joinedload(Card.current_version))
            .where(Card.id == card_id, Card.status == CardStatus.PUBLISHED)
        )

    def get_published_deck(self, deck_id: uuid.UUID) -> Deck | None:
        return self.session.scalar(
            select(Deck).where(Deck.id == deck_id, Deck.status == DeckStatus.PUBLISHED)
        )

    def create(self, suggestion: NoteSuggestion) -> NoteSuggestion:
        self.session.add(suggestion)
        self.session.flush()
        return suggestion

    def get(
        self,
        suggestion_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> NoteSuggestion | None:
        statement = (
            select(NoteSuggestion)
            .options(
                joinedload(NoteSuggestion.card),
                joinedload(NoteSuggestion.card_version),
            )
            .where(NoteSuggestion.id == suggestion_id)
        )
        if for_update:
            statement = statement.with_for_update(of=NoteSuggestion)
        return self.session.scalar(statement)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        status: NoteSuggestionStatus | None,
    ) -> tuple[list[NoteSuggestion], int]:
        filters = []
        if status is not None:
            filters.append(NoteSuggestion.status == status)

        total = self.session.scalar(
            select(func.count()).select_from(NoteSuggestion).where(*filters)
        ) or 0
        statement = (
            select(NoteSuggestion)
            .options(
                joinedload(NoteSuggestion.card),
                joinedload(NoteSuggestion.card_version),
            )
            .where(*filters)
            .order_by(NoteSuggestion.created_at.desc(), NoteSuggestion.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total
