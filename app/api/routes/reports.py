import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limit_public_reports
from app.core.security import AuthPrincipal, require_reviewer
from app.models.enums import CardReportStatus, ReportType
from app.repositories import ReportRepository
from app.schemas import (
    CardReportListResponse,
    CardReportResponse,
    ReportCreateRequest,
    ReportReviewRequest,
)
from app.services import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
admin_router = APIRouter(
    prefix="/admin/reports",
    tags=["admin-reports"],
    dependencies=[Depends(require_reviewer)],
)


def get_report_service(
    session: Session = Depends(get_db, use_cache=False),
) -> ReportService:
    return ReportService(ReportRepository(session))


@router.post(
    "",
    response_model=CardReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    payload: ReportCreateRequest,
    _rate_limit: None = Depends(limit_public_reports),
    service: ReportService = Depends(get_report_service),
) -> CardReportResponse:
    return service.create_report(payload)


@admin_router.get("", response_model=CardReportListResponse)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: CardReportStatus | None = Query(
        default=None, alias="status"
    ),
    report_type: ReportType | None = None,
    service: ReportService = Depends(get_report_service),
) -> CardReportListResponse:
    return service.list_reports(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        report_type=report_type,
    )


@admin_router.get("/{report_id}", response_model=CardReportResponse)
def get_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
) -> CardReportResponse:
    return service.get_report(report_id)


@admin_router.post(
    "/{report_id}/review",
    response_model=CardReportResponse,
)
def review_report(
    report_id: uuid.UUID,
    payload: ReportReviewRequest,
    principal: AuthPrincipal = Depends(require_reviewer),
    service: ReportService = Depends(get_report_service),
) -> CardReportResponse:
    return service.review_report(
        report_id,
        payload.model_copy(update={"reviewed_by": principal.email}),
    )
