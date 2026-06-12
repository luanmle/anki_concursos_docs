import math
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models import CardReport, CardVersion, ReviewTask
from app.models.enums import (
    CardReportStatus,
    CardVersionStatus,
    ReportType,
    ReviewDecision,
    ReviewTaskStatus,
)
from app.repositories import ReportRepository
from app.schemas import (
    CardReportListResponse,
    CardReportResponse,
    ReportCreateRequest,
    ReportReviewRequest,
)
from app.schemas.reports import ReviewTaskResponse
from app.services.cards import calculate_content_hash


class ReportService:
    def __init__(self, repository: ReportRepository) -> None:
        self.repository = repository
        self.session = repository.session

    def create_report(
        self, payload: ReportCreateRequest
    ) -> CardReportResponse:
        try:
            with self.session.begin():
                version = self.repository.get_reportable_version(
                    payload.card_id,
                    payload.card_version_id,
                )
                if version is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Published card version not found",
                    )
                report = self.repository.create_report(
                    CardReport(
                        card_id=payload.card_id,
                        card_version_id=payload.card_version_id,
                        user_id=payload.user_id,
                        report_type=payload.report_type,
                        message=payload.message,
                        status=CardReportStatus.OPEN,
                    )
                )
                self.repository.create_review_task(
                    ReviewTask(
                        report_id=report.id,
                        status=ReviewTaskStatus.PENDING,
                    )
                )
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Report could not be created due to a data conflict",
            ) from exc
        return self.get_report(report.id)

    def list_reports(
        self,
        *,
        page: int,
        page_size: int,
        status_filter: CardReportStatus | None,
        report_type: ReportType | None,
    ) -> CardReportListResponse:
        reports, total = self.repository.list_reports(
            page=page,
            page_size=page_size,
            status=status_filter,
            report_type=report_type,
        )
        return CardReportListResponse(
            items=[self._report_response(report) for report in reports],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def get_report(self, report_id: uuid.UUID) -> CardReportResponse:
        report = self.repository.get_report(report_id)
        if report is None:
            self._raise_report_not_found()
        return self._report_response(report)

    def review_report(
        self,
        report_id: uuid.UUID,
        payload: ReportReviewRequest,
    ) -> CardReportResponse:
        try:
            with self.session.begin():
                report = self.repository.get_report(report_id, for_update=True)
                if report is None:
                    self._raise_report_not_found()
                task = report.review_task
                if task.status == ReviewTaskStatus.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Report has already been reviewed",
                    )
                if (
                    report.report_type == ReportType.OUTDATED_LAW
                    and payload.decision
                    == ReviewDecision.CONVERTED_TO_NEW_VERSION
                    and not payload.evidence_reviewed
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "Outdated law reports require evidence review "
                            "before conversion"
                        ),
                    )

                resulting_version_id = None
                if (
                    payload.decision
                    == ReviewDecision.CONVERTED_TO_NEW_VERSION
                ):
                    proposed = payload.proposed_version
                    if proposed is None:
                        raise RuntimeError("Validated proposed version is missing")
                    card = self.repository.get_card_for_update(report.card_id)
                    if card is None:
                        raise RuntimeError("Reported card could not be reloaded")
                    content_hash = calculate_content_hash(
                        front_text=proposed.front_text,
                        back_text=proposed.back_text,
                        answer_text=proposed.answer_text,
                        explanation_text=proposed.explanation_text,
                    )
                    if any(
                        version.content_hash == content_hash
                        for version in card.versions
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="An identical card version already exists",
                        )
                    resulting_version = self.repository.create_version(
                        CardVersion(
                            card_id=card.id,
                            version_number=self.repository.next_version_number(
                                card.id
                            ),
                            front_text=proposed.front_text,
                            back_text=proposed.back_text,
                            answer_text=proposed.answer_text,
                            explanation_text=proposed.explanation_text,
                            change_reason=proposed.change_reason,
                            created_by=payload.reviewed_by,
                            status=CardVersionStatus.NEEDS_REVIEW,
                            content_hash=content_hash,
                        )
                    )
                    resulting_version_id = resulting_version.id
                    report.status = CardReportStatus.RESOLVED
                elif payload.decision == ReviewDecision.REJECTED:
                    report.status = CardReportStatus.REJECTED
                else:
                    report.status = CardReportStatus.DUPLICATE

                task.status = ReviewTaskStatus.COMPLETED
                task.assigned_to = payload.reviewed_by
                task.decision = payload.decision
                task.admin_comment = payload.admin_comment
                task.evidence_reviewed = payload.evidence_reviewed
                task.resulting_card_version_id = resulting_version_id
                task.reviewed_at = datetime.now(UTC)
                self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Report review could not be completed",
            ) from exc

        return self.get_report(report_id)

    @staticmethod
    def _report_response(report: CardReport) -> CardReportResponse:
        task = report.review_task
        return CardReportResponse(
            report_id=report.id,
            card_id=report.card_id,
            public_id=report.card.public_id,
            card_version_id=report.card_version_id,
            version_number=report.card_version.version_number,
            user_id=report.user_id,
            report_type=report.report_type,
            message=report.message,
            status=report.status,
            review_task=ReviewTaskResponse(
                review_task_id=task.id,
                status=task.status,
                assigned_to=task.assigned_to,
                decision=task.decision,
                admin_comment=task.admin_comment,
                evidence_reviewed=task.evidence_reviewed,
                resulting_card_version_id=task.resulting_card_version_id,
                reviewed_at=ReportService._as_utc(task.reviewed_at),
                created_at=ReportService._as_utc(task.created_at),
                updated_at=ReportService._as_utc(task.updated_at),
            ),
            created_at=ReportService._as_utc(report.created_at),
            updated_at=ReportService._as_utc(report.updated_at),
        )

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _raise_report_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
