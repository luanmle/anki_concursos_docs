import hashlib
import json
import math
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models import (
    CardVersion,
    NoteComment,
    NoteSuggestion,
    NoteSuggestionComment,
    User,
)
from app.models.enums import (
    CardStatus,
    CardVersionStatus,
    NoteSuggestionStatus,
    NoteSuggestionType,
)
from app.repositories import NoteSuggestionRepository
from app.repositories.cards import CardRepository
from app.repositories.decks import DeckRepository
from app.schemas import (
    NoteCommentListResponse,
    NoteCommentResponse,
    NoteSuggestionCommentCreateRequest,
    NoteSuggestionCommentListResponse,
    NoteSuggestionCommentResponse,
    NoteSuggestionCreateRequest,
    NoteSuggestionListResponse,
    NoteSuggestionResponse,
    NoteSuggestionReviewRequest,
)
from app.schemas.cards import CardVersionCreateRequest
from app.schemas.decks import ReleasePublishRequest
from app.services.cards import CardService, calculate_content_hash
from app.services.decks import DeckService


class NoteSuggestionService:
    def __init__(self, repository: NoteSuggestionRepository) -> None:
        self.repository = repository
        self.session = repository.session

    def create_for_card(
        self,
        card_id: uuid.UUID,
        payload: NoteSuggestionCreateRequest,
        user: User,
    ) -> NoteSuggestionResponse:
        try:
            card = self.repository.get_published_card(card_id)
            if card is None or card.current_version is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Published card not found",
                )
            suggestion = self.repository.create(
                NoteSuggestion(
                    card_id=card.id,
                    card_version_id=card.current_version.id,
                    submitted_by_user_id=user.id,
                    submitted_by_email=user.email,
                    suggestion_type=payload.suggestion_type,
                    fields=payload.fields,
                    added_tags=payload.added_tags,
                    removed_tags=payload.removed_tags,
                    comment=payload.comment,
                    source=payload.source,
                )
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suggestion could not be created",
            ) from exc
        return self.get(suggestion.id)

    def create_for_deck(
        self,
        deck_id: uuid.UUID,
        payload: NoteSuggestionCreateRequest,
        user: User,
    ) -> NoteSuggestionResponse:
        try:
            if self.repository.get_published_deck(deck_id) is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Published deck not found",
                )
            suggestion = self.repository.create(
                NoteSuggestion(
                    deck_id=deck_id,
                    submitted_by_user_id=user.id,
                    submitted_by_email=user.email,
                    suggestion_type=payload.suggestion_type,
                    fields=payload.fields,
                    added_tags=payload.added_tags,
                    removed_tags=payload.removed_tags,
                    comment=payload.comment,
                    source=payload.source,
                )
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suggestion could not be created",
            ) from exc
        return self.get(suggestion.id)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        status_filter: NoteSuggestionStatus | None,
    ) -> NoteSuggestionListResponse:
        suggestions, total = self.repository.list(
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        return NoteSuggestionListResponse(
            items=[self._response(item) for item in suggestions],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def get(self, suggestion_id: uuid.UUID) -> NoteSuggestionResponse:
        suggestion = self.repository.get(suggestion_id)
        if suggestion is None:
            self._raise_not_found()
        return self._response(suggestion)

    def list_for_deck(
        self,
        deck_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        status_filter: NoteSuggestionStatus | None,
    ) -> NoteSuggestionListResponse:
        if self.repository.get_deck(deck_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found",
            )
        suggestions, total = self.repository.list_for_deck(
            deck_id,
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        return NoteSuggestionListResponse(
            items=[self._response(item) for item in suggestions],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def list_comments(
        self, suggestion_id: uuid.UUID
    ) -> NoteSuggestionCommentListResponse:
        if self.repository.get(suggestion_id) is None:
            self._raise_not_found()
        comments = self.repository.list_comments(suggestion_id)
        return NoteSuggestionCommentListResponse(
            items=[self._comment_response(item) for item in comments],
            total=len(comments),
        )

    def add_comment(
        self,
        suggestion_id: uuid.UUID,
        payload: NoteSuggestionCommentCreateRequest,
        user: User,
    ) -> NoteSuggestionCommentResponse:
        if self.repository.get(suggestion_id) is None:
            self._raise_not_found()
        comment = self.repository.create_comment(
            NoteSuggestionComment(
                suggestion_id=suggestion_id,
                author_user_id=user.id,
                author_email=user.email,
                body=payload.body,
            )
        )
        self.session.commit()
        return self._comment_response(comment)

    def list_note_comments(self, card_id: uuid.UUID) -> NoteCommentListResponse:
        if self.repository.get_published_card(card_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Published card not found",
            )
        comments = self.repository.list_note_comments(card_id)
        return NoteCommentListResponse(
            items=[self._note_comment_response(item) for item in comments],
            total=len(comments),
        )

    def add_note_comment(
        self,
        card_id: uuid.UUID,
        payload: NoteSuggestionCommentCreateRequest,
        user: User,
    ) -> NoteCommentResponse:
        if self.repository.get_published_card(card_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Published card not found",
            )
        comment = self.repository.create_note_comment(
            NoteComment(
                card_id=card_id,
                author_user_id=user.id,
                author_email=user.email,
                body=payload.body,
            )
        )
        self.session.commit()
        return self._note_comment_response(comment)

    def review(
        self,
        suggestion_id: uuid.UUID,
        payload: NoteSuggestionReviewRequest,
        *,
        reviewed_by: str,
    ) -> NoteSuggestionResponse:
        try:
            suggestion = self.repository.get(suggestion_id, for_update=True)
            if suggestion is None:
                self._raise_not_found()
            if suggestion.status != NoteSuggestionStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Suggestion has already been reviewed",
                )
            # FIX 1: publish BEFORE committing status so that if publish raises,
            # the suggestion stays PENDING and is retryable.
            resulting_id = payload.resulting_card_version_id
            if (
                resulting_id is None
                and payload.status == NoteSuggestionStatus.ACCEPTED
            ):
                resulting_id = self._publish_from_suggestion(suggestion, reviewed_by)
            suggestion.status = payload.status
            suggestion.reviewed_by = reviewed_by
            suggestion.review_comment = payload.review_comment
            suggestion.reviewed_at = datetime.now(UTC)
            suggestion.resulting_card_version_id = resulting_id
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suggestion review could not be completed",
            ) from exc
        return self.get(suggestion_id)

    def _publish_from_suggestion(
        self, suggestion: NoteSuggestion, reviewed_by: str
    ) -> uuid.UUID | None:
        """Aceite de sugestão de card: cria versão publicada + release nos decks.

        ADR-0007: sugestão aceita publica direto (sem segunda revisão).
        ponytail: campos do Anki mapeados por heurística; sequencia serviços
        existentes (Card/Deck) em vez de reimplementar versão/release.
        """
        # FIX 2: DELETE suggestions have no content to publish.
        if suggestion.suggestion_type == NoteSuggestionType.DELETE:
            return None
        if suggestion.card_id is None:
            return None
        card = self.repository.get_published_card(suggestion.card_id)
        if card is None or card.current_version is None:
            return None
        base = card.current_version
        fields = suggestion.fields or {}
        card_id = card.id
        suggestion_type_label = suggestion.suggestion_type.value
        change_reason = suggestion.comment or "Sugestão aceita"

        # Native cards (uploaded from Anki) carry anki_fields keyed by the real
        # Anki field names — the deck sync serves those. Preserve them and apply
        # the edit by field name. Legacy cards use the 4-field model.
        if base.anki_fields:
            new_version_id = self._create_native_version(
                card, base, fields, change_reason, reviewed_by
            )
        else:
            new_version_id = self._create_legacy_version(
                card, base, fields, change_reason, reviewed_by
            )
        if new_version_id is None:
            return None

        deck_ids = self.repository.decks_with_active_card(card_id)
        # close the autobegun read so the sub-services can session.begin();
        # expire_all so add_card reloads the card's (now newer) current_version
        # instead of a cached relationship from before the version was published.
        self.session.commit()
        self.session.expire_all()

        deck_service = DeckService(DeckRepository(self.session))
        for deck_id in deck_ids:
            deck_service.add_card(deck_id, card_id)
            self.session.commit()
            self.session.expire_all()
            deck_service.publish_release(
                deck_id,
                ReleasePublishRequest(
                    description=f"Sugestão aceita: {suggestion_type_label}"
                ),
            )
            self.session.commit()
            self.session.expire_all()
        return new_version_id

    def _create_native_version(
        self,
        card: object,
        base: CardVersion,
        fields: dict,
        change_reason: str,
        reviewed_by: str,
    ) -> uuid.UUID | None:
        """New published version preserving anki_fields, applying the edit."""
        new_anki = dict(base.anki_fields)
        changed = False
        for name, value in fields.items():
            new_value = value.get("new", "") if isinstance(value, dict) else value
            if name in new_anki and new_anki[name] != new_value:
                new_anki[name] = new_value
                changed = True
        if not changed:
            return None  # edited field absent on the note, or no real change
        content_hash = self._native_content_hash(
            card.card_kind,
            base.note_type,
            base.template_name,
            new_anki,
            base.anki_template,
            base.anki_tags or [],
        )
        if content_hash in self.repository.card_version_hashes(card.id):
            return None
        version = self.repository.add_card_version(
            CardVersion(
                card_id=card.id,
                version_number=self.repository.next_card_version_number(card.id),
                front_text=base.front_text,
                back_text=base.back_text,
                answer_text=base.answer_text,
                explanation_text=base.explanation_text,
                note_type=base.note_type,
                template_name=base.template_name,
                anki_fields=new_anki,
                anki_template=base.anki_template,
                anki_tags=base.anki_tags,
                source_note_id=base.source_note_id,
                source_note_guid=base.source_note_guid,
                source_deck_path=base.source_deck_path,
                change_reason=change_reason,
                created_by=reviewed_by,
                status=CardVersionStatus.PUBLISHED,
                content_hash=content_hash,
            )
        )
        card.current_version_id = version.id
        card.status = CardStatus.PUBLISHED
        self.session.commit()
        return version.id

    def _create_legacy_version(
        self,
        card: object,
        base: CardVersion,
        fields: dict,
        change_reason: str,
        reviewed_by: str,
    ) -> uuid.UUID | None:
        """New published version for legacy 4-field cards via CardService."""

        def suggested(*names: str) -> str | None:
            for name in names:
                if name in fields:
                    value = fields[name]
                    return value.get("new", "") if isinstance(value, dict) else value
            return None

        new_fields = {
            "front_text": suggested("Front", "Text", "front_text") or base.front_text,
            "back_text": suggested("Back", "Extra", "back_text") or base.back_text,
            "answer_text": suggested("Answer", "answer_text") or base.answer_text,
            "explanation_text": suggested("Explanation", "explanation_text")
            or base.explanation_text,
        }
        if all(new_fields[key] == getattr(base, key) for key in new_fields):
            return None
        content_hash = calculate_content_hash(card_kind=card.card_kind, **new_fields)
        if content_hash in self.repository.card_version_hashes(card.id):
            return None
        card_id = card.id
        self.session.commit()
        card_service = CardService(CardRepository(self.session))
        version_response = card_service.create_version(
            card_id,
            CardVersionCreateRequest(
                change_reason=change_reason,
                created_by=reviewed_by,
                **new_fields,
            ),
        )
        new_version_id = version_response.card_version_id
        card_service.approve_version(card_id, new_version_id)
        self.session.commit()
        self.session.expire_all()
        card_service.publish_version(card_id, new_version_id)
        self.session.commit()
        self.session.expire_all()
        return new_version_id

    @staticmethod
    def _native_content_hash(
        card_kind,
        note_type,
        template_name,
        anki_fields: dict,
        anki_template,
        anki_tags: list,
    ) -> str:
        # ponytail: mirror DeckService._upload_content_hash so a suggestion-built
        # native version dedups against upload-built ones. base.anki_template is
        # already the stored model_dump(mode="json") dict.
        raw = json.dumps(
            {
                "card_kind": card_kind.value,
                "fields": anki_fields,
                "note_type": note_type,
                "tags": anki_tags,
                "template": anki_template,
                "template_name": template_name,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _response(suggestion: NoteSuggestion) -> NoteSuggestionResponse:
        version = suggestion.card_version
        return NoteSuggestionResponse(
            suggestion_id=suggestion.id,
            deck_id=suggestion.deck_id,
            card_id=suggestion.card_id,
            public_id=suggestion.card.public_id if suggestion.card else None,
            card_version_id=suggestion.card_version_id,
            version_number=version.version_number if version else None,
            submitted_by_user_id=suggestion.submitted_by_user_id,
            submitted_by_email=suggestion.submitted_by_email,
            suggestion_type=suggestion.suggestion_type,
            status=suggestion.status,
            fields=suggestion.fields,
            added_tags=suggestion.added_tags,
            removed_tags=suggestion.removed_tags,
            comment=suggestion.comment,
            source=suggestion.source,
            reviewed_by=suggestion.reviewed_by,
            review_comment=suggestion.review_comment,
            reviewed_at=NoteSuggestionService._as_utc(suggestion.reviewed_at),
            resulting_card_version_id=suggestion.resulting_card_version_id,
            created_at=NoteSuggestionService._as_utc(suggestion.created_at),
            updated_at=NoteSuggestionService._as_utc(suggestion.updated_at),
        )

    @staticmethod
    def _comment_response(
        comment: NoteSuggestionComment,
    ) -> NoteSuggestionCommentResponse:
        return NoteSuggestionCommentResponse(
            comment_id=comment.id,
            suggestion_id=comment.suggestion_id,
            author_user_id=comment.author_user_id,
            author_email=comment.author_email,
            body=comment.body,
            created_at=NoteSuggestionService._as_utc(comment.created_at),
        )

    @staticmethod
    def _note_comment_response(comment: NoteComment) -> NoteCommentResponse:
        return NoteCommentResponse(
            comment_id=comment.id,
            card_id=comment.card_id,
            author_user_id=comment.author_user_id,
            author_email=comment.author_email,
            body=comment.body,
            created_at=NoteSuggestionService._as_utc(comment.created_at),
        )

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _raise_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found",
        )
