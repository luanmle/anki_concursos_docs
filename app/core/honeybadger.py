from __future__ import annotations

from typing import Any

from honeybadger import honeybadger

from app.core.config import Settings


def configure_honeybadger(settings: Settings) -> bool:
    api_key = (settings.honeybadger_api_key or "").strip()
    if not api_key:
        return False

    honeybadger.configure(
        api_key=api_key,
        environment=settings.app_env,
        development_environments=["development", "test", "local"],
        report_data=True,
        root_directory=".",
        package="anki-concursos",
    )
    return True


def notify_exception(
    exception: BaseException,
    *,
    context: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    fingerprint: str | None = None,
) -> None:
    try:
        honeybadger.notify(
            exception,
            context=context or {},
            tags=tags,
            fingerprint=fingerprint,
        )
    except Exception:
        return
