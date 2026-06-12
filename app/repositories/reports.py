import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Card, CardReport, CardVersion, ReviewTask
from app.models.enums import (
    CardReportStatus,
    CardStatus,
    CardVersionStatus,
    ReportType,
)


class ReportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_reportable_version(
        self, card_id: uuid.UUID, card_version_id: uuid.UUID
    ) -> CardVersion | None:
        return self.session.scalar(
            select(CardVersion)
            .join(Card, Card.id == CardVersion.card_id)
            .options(joinedload(CardVersion.card))
            .where(
                Card.id == card_id,
                Card.status == CardStatus.PUBLISHED,
                CardVersion.id == card_version_id,
                CardVersion.card_id == card_id,
                CardVersion.status == CardVersionStatus.PUBLISHED,
            )
        )

    def create_report(self, report: CardReport) -> CardReport:
        self.session.add(report)
        self.session.flush()
        return report

    def create_review_task(self, task: ReviewTask) -> ReviewTask:
        self.session.add(task)
        self.session.flush()
        return task

    def get_report(
        self,
        report_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> CardReport | None:
        statement = (
            select(CardReport)
            .options(
                joinedload(CardReport.card),
                joinedload(CardReport.card_version),
                joinedload(CardReport.review_task).joinedload(
                    ReviewTask.resulting_card_version
                ),
            )
            .where(CardReport.id == report_id)
        )
        if for_update:
            statement = statement.with_for_update(of=CardReport)
        return self.session.scalar(statement)

    def list_reports(
        self,
        *,
        page: int,
        page_size: int,
        status: CardReportStatus | None,
        report_type: ReportType | None,
    ) -> tuple[list[CardReport], int]:
        filters = []
        if status is not None:
            filters.append(CardReport.status == status)
        if report_type is not None:
            filters.append(CardReport.report_type == report_type)

        total = self.session.scalar(
            select(func.count()).select_from(CardReport).where(*filters)
        ) or 0
        statement = (
            select(CardReport)
            .options(
                joinedload(CardReport.card),
                joinedload(CardReport.card_version),
                selectinload(CardReport.review_task),
            )
            .where(*filters)
            .order_by(CardReport.created_at.desc(), CardReport.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def get_card_for_update(self, card_id: uuid.UUID) -> Card | None:
        return self.session.scalar(
            select(Card)
            .options(selectinload(Card.versions))
            .where(Card.id == card_id)
            .with_for_update(of=Card)
        )

    def next_version_number(self, card_id: uuid.UUID) -> int:
        current_max = self.session.scalar(
            select(func.max(CardVersion.version_number)).where(
                CardVersion.card_id == card_id
            )
        )
        return (current_max or 0) + 1

    def create_version(self, version: CardVersion) -> CardVersion:
        self.session.add(version)
        self.session.flush()
        return version
