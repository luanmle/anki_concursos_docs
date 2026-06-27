from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.addon import router as addon_router
from app.api.routes.auth import (
    admin_router as admin_users_router,
)
from app.api.routes.auth import (
    router as auth_router,
)
from app.api.routes.cards import import_router as card_imports_router
from app.api.routes.cards import router as cards_router
from app.api.routes.decks import router as decks_router
from app.api.routes.health import router as health_router
from app.api.routes.reports import (
    admin_router as admin_reports_router,
)
from app.api.routes.reports import (
    router as reports_router,
)
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.suggestions import (
    addon_router as addon_suggestions_router,
)
from app.api.routes.suggestions import (
    admin_router as admin_note_suggestions_router,
)
from app.api.routes.suggestions import (
    community_router as community_note_suggestions_router,
)
from app.api.routes.taxonomy import router as taxonomy_router
from app.core.config import get_settings
from app.core.honeybadger import configure_honeybadger, notify_exception
from app.core.logging import configure_logging
from app.core.middleware import RequestBodyLimitMiddleware, RequestContextMiddleware

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_honeybadger(settings)
    yield


app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def handle_unexpected_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or request.headers.get(
        "X-Request-ID"
    )
    notify_exception(
        exc,
        context={
            "endpoint": request.url.path,
            "method": request.method,
            "request_id": request_id,
            "client_ip": request.client.host if request.client else None,
            "query_params": dict(request.query_params),
        },
        tags=["fastapi", "unhandled_exception"],
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={"X-Request-ID": request_id} if request_id else None,
    )


app.add_middleware(
    RequestBodyLimitMiddleware,
    maximum_bytes=settings.max_request_body_bytes,
)
app.add_middleware(RequestContextMiddleware)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=[
            "Content-Disposition",
            "X-Content-SHA256",
            "X-Release-Number",
            "X-Request-ID",
            "X-Row-Count",
        ],
    )
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(taxonomy_router)
app.include_router(subscriptions_router)
app.include_router(card_imports_router)
app.include_router(cards_router)
app.include_router(decks_router)
app.include_router(addon_router)
app.include_router(addon_suggestions_router)
app.include_router(reports_router)
app.include_router(admin_reports_router)
app.include_router(admin_note_suggestions_router)
app.include_router(community_note_suggestions_router)
