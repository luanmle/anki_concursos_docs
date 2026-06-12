import hashlib
import json
import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models import Card, CardVersion
from app.models.enums import CardStatus, CardVersionStatus
from app.repositories import CardRepository
from app.schemas import (
    CardCreateRequest,
    CardDetailResponse,
    CardListResponse,
    CardSummaryResponse,
    CardVersionCreateRequest,
    CardVersionResponse,
)


def calculate_content_hash(
    *,
    front_text: str,
    back_text: str,
    answer_text: str,
    explanation_text: str,
) -> str:
    canonical_content = json.dumps(
        {
            "answer_text": answer_text,
            "back_text": back_text,
            "explanation_text": explanation_text,
            "front_text": front_text,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()


class CardService:
    def __init__(self, repository: CardRepository) -> None:
        self.repository = repository
        self.session = repository.session

    def create_card(self, payload: CardCreateRequest) -> CardDetailResponse:
        try:
            with self.session.begin():
                self._validate_taxonomy(payload.discipline_id, payload.topic_id)
                if self.repository.get_by_canonical_key(payload.canonical_key):
                    self._raise_canonical_key_conflict()

                card = self.repository.create_card(
                    Card(
                        canonical_key=payload.canonical_key,
                        discipline_id=payload.discipline_id,
                        topic_id=payload.topic_id,
                        status=CardStatus.NEEDS_REVIEW,
                    )
                )
                version = self.repository.create_version(
                    CardVersion(
                        card_id=card.id,
                        version_number=1,
                        front_text=payload.front_text,
                        back_text=payload.back_text,
                        answer_text=payload.answer_text,
                        explanation_text=payload.explanation_text,
                        change_reason=payload.change_reason,
                        created_by=payload.created_by,
                        status=CardVersionStatus.NEEDS_REVIEW,
                        content_hash=calculate_content_hash(**self._content(payload)),
                    )
                )
                card.current_version_id = version.id
                self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            if "canonical" in str(exc).lower():
                self._raise_canonical_key_conflict()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Card could not be created due to a data conflict",
            ) from exc

        return self.get_card(card.id)

    def create_version(
        self, card_id: uuid.UUID, payload: CardVersionCreateRequest
    ) -> CardVersionResponse:
        try:
            with self.session.begin():
                card = self.repository.get_by_id(card_id, for_update=True)
                if card is None:
                    self._raise_card_not_found()

                content_hash = calculate_content_hash(**self._content(payload))
                if any(
                    version.content_hash == content_hash for version in card.versions
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="An identical card version already exists",
                    )

                version = self.repository.create_version(
                    CardVersion(
                        card_id=card.id,
                        version_number=self.repository.next_version_number(card.id),
                        front_text=payload.front_text,
                        back_text=payload.back_text,
                        answer_text=payload.answer_text,
                        explanation_text=payload.explanation_text,
                        change_reason=payload.change_reason,
                        created_by=payload.created_by,
                        status=CardVersionStatus.NEEDS_REVIEW,
                        content_hash=content_hash,
                    )
                )
                if (
                    card.current_version is None
                    or card.current_version.status != CardVersionStatus.PUBLISHED
                ):
                    card.status = CardStatus.NEEDS_REVIEW
                self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Card version could not be created due to a conflict",
            ) from exc

        return self._version_response(version)

    def approve_version(
        self, card_id: uuid.UUID, version_id: uuid.UUID
    ) -> CardDetailResponse:
        with self.session.begin():
            card = self.repository.get_by_id(card_id, for_update=True)
            if card is None:
                self._raise_card_not_found()
            version = self.repository.get_version(card.id, version_id)
            if version is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Card version not found",
                )
            if version.status == CardVersionStatus.PUBLISHED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Published version is already immutable",
                )
            version.status = CardVersionStatus.APPROVED
            card.current_version_id = version.id
            card.status = CardStatus.APPROVED
            self.session.flush()
        return self.get_card(card_id)

    def publish_version(
        self, card_id: uuid.UUID, version_id: uuid.UUID
    ) -> CardDetailResponse:
        with self.session.begin():
            card = self.repository.get_by_id(card_id, for_update=True)
            if card is None:
                self._raise_card_not_found()
            version = self.repository.get_version(card.id, version_id)
            if version is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Card version not found",
                )
            if version.status != CardVersionStatus.APPROVED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only an approved version can be published",
                )
            version.status = CardVersionStatus.PUBLISHED
            card.current_version_id = version.id
            card.status = CardStatus.PUBLISHED
            self.session.flush()
        return self.get_card(card_id)

    def get_card(self, card_id: uuid.UUID) -> CardDetailResponse:
        card = self.repository.get_by_id(card_id)
        if card is None:
            self._raise_card_not_found()
        return self._detail_response(card)

    def get_public_card(self, public_id: str) -> CardSummaryResponse:
        card = self.repository.get_by_public_id(public_id)
        if card is None:
            self._raise_card_not_found()
        return self._summary_response(card)

    def list_cards(
        self,
        *,
        page: int,
        page_size: int,
        discipline_id: uuid.UUID | None,
        topic_id: uuid.UUID | None,
        status_filter: CardStatus | None,
        public_id: str | None,
    ) -> CardListResponse:
        cards, total = self.repository.list_cards(
            page=page,
            page_size=page_size,
            discipline_id=discipline_id,
            topic_id=topic_id,
            status=status_filter,
            public_id=public_id,
        )
        return CardListResponse(
            items=[self._summary_response(card) for card in cards],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def _validate_taxonomy(
        self, discipline_id: uuid.UUID, topic_id: uuid.UUID
    ) -> None:
        if not self.repository.taxonomy_is_valid(discipline_id, topic_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Topic does not belong to the informed discipline",
            )

    @staticmethod
    def _content(
        payload: CardCreateRequest | CardVersionCreateRequest,
    ) -> dict[str, str]:
        return {
            "front_text": payload.front_text,
            "back_text": payload.back_text,
            "answer_text": payload.answer_text,
            "explanation_text": payload.explanation_text,
        }

    @staticmethod
    def _version_response(version: CardVersion) -> CardVersionResponse:
        return CardVersionResponse(
            card_version_id=version.id,
            version_number=version.version_number,
            front_text=version.front_text,
            back_text=version.back_text,
            answer_text=version.answer_text,
            explanation_text=version.explanation_text,
            change_reason=version.change_reason,
            created_by=version.created_by,
            status=version.status,
            content_hash=version.content_hash,
            created_at=version.created_at,
        )

    def _summary_response(self, card: Card) -> CardSummaryResponse:
        return CardSummaryResponse(
            card_id=card.id,
            public_id=card.public_id,
            canonical_key=card.canonical_key,
            discipline_id=card.discipline_id,
            topic_id=card.topic_id,
            status=card.status,
            current_version=(
                self._version_response(card.current_version)
                if card.current_version is not None
                else None
            ),
            created_at=card.created_at,
            updated_at=card.updated_at,
        )

    def _detail_response(self, card: Card) -> CardDetailResponse:
        summary = self._summary_response(card)
        return CardDetailResponse(
            **summary.model_dump(),
            versions=[
                self._version_response(version)
                for version in sorted(
                    card.versions,
                    key=lambda item: item.version_number,
                    reverse=True,
                )
            ],
        )

    @staticmethod
    def _raise_card_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    @staticmethod
    def _raise_canonical_key_conflict() -> None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="canonical_key already exists",
        )
