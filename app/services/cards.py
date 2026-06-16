import csv
import hashlib
import io
import json
import math
import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models import Card, CardVersion
from app.models.enums import CardStatus, CardVersionStatus
from app.repositories import CardRepository
from app.schemas import (
    CardCreateRequest,
    CardCsvImportRequest,
    CardCsvImportResponse,
    CardCsvImportRowResult,
    CardDetailResponse,
    CardListResponse,
    CardSummaryResponse,
    CardVersionCreateRequest,
    CardVersionResponse,
)

CSV_REQUIRED_CONTENT_COLUMNS = {
    "front_text",
    "back_text",
    "answer_text",
    "explanation_text",
}


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

    def import_csv(
        self,
        payload: CardCsvImportRequest,
        *,
        created_by: str,
    ) -> CardCsvImportResponse:
        rows = self._read_import_rows(payload)
        results: list[CardCsvImportRowResult] = []
        seen_hashes: set[str] = set()

        with self.session.begin():
            for row_number, row in rows:
                row_result = self._import_csv_row(
                    row_number,
                    row,
                    payload=payload,
                    created_by=created_by,
                    seen_hashes=seen_hashes,
                )
                results.append(row_result)

        created_status = "ready" if payload.dry_run else "created"
        return CardCsvImportResponse(
            dry_run=payload.dry_run,
            total_rows=len(rows),
            created=sum(1 for item in results if item.status == created_status),
            duplicates=sum(1 for item in results if item.status == "duplicate"),
            errors=sum(1 for item in results if item.status == "error"),
            items=results,
        )

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

    def _import_csv_row(
        self,
        row_number: int,
        row: dict[str, str],
        *,
        payload: CardCsvImportRequest,
        created_by: str,
        seen_hashes: set[str],
    ) -> CardCsvImportRowResult:
        try:
            discipline_id = self._resolve_import_discipline(row)
            topic_id = self._resolve_import_topic(row, discipline_id)
            content = self._import_row_content(row)
            content_hash = calculate_content_hash(**content)
            if content_hash in seen_hashes or self.repository.content_hash_exists(
                content_hash
            ):
                seen_hashes.add(content_hash)
                return CardCsvImportRowResult(
                    row_number=row_number,
                    status="duplicate",
                    message="Conteúdo idêntico já existe ou foi repetido no arquivo.",
                )
            seen_hashes.add(content_hash)

            if payload.dry_run:
                return CardCsvImportRowResult(
                    row_number=row_number,
                    status="ready",
                    message="Linha válida para importação.",
                )

            card = self.repository.create_card(
                Card(
                    canonical_key=self._canonical_key_for_import(content_hash),
                    discipline_id=discipline_id,
                    topic_id=topic_id,
                    status=CardStatus.NEEDS_REVIEW,
                )
            )
            version = self.repository.create_version(
                CardVersion(
                    card_id=card.id,
                    version_number=1,
                    front_text=content["front_text"],
                    back_text=content["back_text"],
                    answer_text=content["answer_text"],
                    explanation_text=content["explanation_text"],
                    change_reason=payload.default_change_reason,
                    created_by=created_by,
                    status=CardVersionStatus.NEEDS_REVIEW,
                    content_hash=content_hash,
                )
            )
            card.current_version_id = version.id
            self.session.flush()
            return CardCsvImportRowResult(
                row_number=row_number,
                status="created",
                message="Cartão criado com versão inicial em revisão.",
                public_id=card.public_id,
                card_id=card.id,
                card_version_id=version.id,
            )
        except ValueError as exc:
            return CardCsvImportRowResult(
                row_number=row_number,
                status="error",
                message=str(exc),
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
    def _read_import_rows(
        payload: CardCsvImportRequest,
    ) -> list[tuple[int, dict[str, str]]]:
        try:
            reader = csv.DictReader(
                io.StringIO(payload.csv_text),
                delimiter=payload.delimiter,
            )
        except csv.Error as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="CSV could not be parsed",
            ) from exc

        if not reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="CSV header is required",
            )

        columns = {
            column.strip().lstrip("\ufeff") for column in reader.fieldnames if column
        }
        missing = sorted(CSV_REQUIRED_CONTENT_COLUMNS - columns)
        has_taxonomy = (
            {"discipline_id", "topic_id"}.issubset(columns)
            or {"discipline", "topic"}.issubset(columns)
        )
        if missing or not has_taxonomy:
            required = sorted(CSV_REQUIRED_CONTENT_COLUMNS)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "CSV must include content columns "
                    f"{required} and either discipline/topic or "
                    "discipline_id/topic_id"
                ),
            )

        rows: list[tuple[int, dict[str, str]]] = []
        for index, raw_row in enumerate(reader, start=2):
            rows.append(
                (
                    index,
                    {
                        (key or "").strip().lstrip("\ufeff"): (value or "").strip()
                        for key, value in raw_row.items()
                    },
                )
            )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="CSV must include at least one data row",
            )
        return rows

    def _resolve_import_discipline(self, row: dict[str, str]) -> uuid.UUID:
        discipline_id = row.get("discipline_id", "")
        if discipline_id:
            try:
                return uuid.UUID(discipline_id)
            except ValueError as exc:
                raise ValueError("discipline_id inválido.") from exc

        discipline_name = row.get("discipline", "")
        if not discipline_name:
            raise ValueError("Informe discipline ou discipline_id.")
        discipline = self.repository.get_discipline_by_name(discipline_name)
        if discipline is None:
            raise ValueError(f"Disciplina não encontrada: {discipline_name}.")
        return discipline.id

    def _resolve_import_topic(
        self,
        row: dict[str, str],
        discipline_id: uuid.UUID,
    ) -> uuid.UUID:
        topic_id = row.get("topic_id", "")
        if topic_id:
            try:
                parsed_topic_id = uuid.UUID(topic_id)
            except ValueError as exc:
                raise ValueError("topic_id inválido.") from exc
            if not self.repository.taxonomy_is_valid(discipline_id, parsed_topic_id):
                raise ValueError(
                    "topic_id nao pertence a discipline_id informada."
                )
            return parsed_topic_id

        topic_name = row.get("topic", "")
        if not topic_name:
            raise ValueError("Informe topic ou topic_id.")
        topic = self.repository.get_topic_by_name(discipline_id, topic_name)
        if topic is None:
            raise ValueError(f"Assunto não encontrado: {topic_name}.")
        return topic.id

    @staticmethod
    def _import_row_content(row: dict[str, str]) -> dict[str, str]:
        content = {
            column: row.get(column, "").strip()
            for column in CSV_REQUIRED_CONTENT_COLUMNS
        }
        missing = [column for column, value in content.items() if not value]
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Campos obrigatórios vazios: {missing_list}.")
        return content

    @staticmethod
    def _canonical_key_for_import(content_hash: str) -> str:
        return f"csv-{re.sub(r'[^a-z0-9]', '', content_hash.lower())[:48]}"

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
