import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _limit(
    request: Request,
    *,
    namespace: str,
    maximum: int,
    window_seconds: int,
    detail: str,
) -> None:
    now = time.monotonic()
    cutoff = now - window_seconds
    key = (namespace, _client_key(request))
    with _lock:
        attempts = _attempts[key]
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if len(attempts) >= maximum:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail,
                headers={"Retry-After": str(window_seconds)},
            )
        attempts.append(now)


def limit_public_reports(request: Request) -> None:
    settings = get_settings()
    _limit(
        request,
        namespace="public-reports",
        maximum=settings.public_report_rate_limit,
        window_seconds=settings.public_report_rate_window_seconds,
        detail="Too many reports submitted; try again later",
    )


def limit_login_attempts(request: Request) -> None:
    settings = get_settings()
    _limit(
        request,
        namespace="login",
        maximum=settings.login_rate_limit,
        window_seconds=settings.login_rate_window_seconds,
        detail="Too many login attempts; try again later",
    )
