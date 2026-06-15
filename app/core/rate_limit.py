import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = threading.Lock()
_last_cleanup = 0.0


def _client_key(request: Request) -> str:
    settings = get_settings()
    forwarded_for = request.headers.get("X-Forwarded-For")
    if settings.trust_proxy_headers and forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _cleanup(now: float, window_seconds: int, maximum_keys: int) -> None:
    global _last_cleanup
    if now - _last_cleanup < window_seconds:
        return
    cutoff = now - window_seconds
    empty_keys = []
    for key, attempts in _attempts.items():
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if not attempts:
            empty_keys.append(key)
    for key in empty_keys:
        _attempts.pop(key, None)
    if len(_attempts) > maximum_keys:
        oldest_keys = sorted(
            _attempts,
            key=lambda key: _attempts[key][-1] if _attempts[key] else 0,
        )
        for key in oldest_keys[: len(_attempts) - maximum_keys]:
            _attempts.pop(key, None)
    _last_cleanup = now


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
        maximum_keys = get_settings().rate_limit_max_keys
        _cleanup(now, window_seconds, maximum_keys)
        if key not in _attempts and len(_attempts) >= maximum_keys:
            oldest_key = min(
                _attempts,
                key=lambda item: (
                    _attempts[item][-1] if _attempts[item] else 0
                ),
            )
            _attempts.pop(oldest_key, None)
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


def reset_rate_limits() -> None:
    global _last_cleanup
    with _lock:
        _attempts.clear()
        _last_cleanup = 0.0


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
