"""Attestive API entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import install_exception_handlers
from app.core.headers import SecurityHeadersMiddleware
from app.core.logging import RequestContextMiddleware, configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging("DEBUG" if settings.DEBUG else "INFO")
    settings.validate_for_runtime()
    logger.info("Starting %s v%s (%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    if settings.AI_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        logger.warning(
            "AI_PROVIDER=openai but OPENAI_API_KEY is unset: the tutor will report 503 "
            "ai_unavailable until a hosted model credential is configured."
        )
    if settings.ENVIRONMENT != "development" and not settings.email_configured:
        logger.warning(
            "Email transport is %s: verification and password-reset links will not reach "
            "users. Set EMAIL_DELIVERY to resend, sendgrid or smtp.",
            settings.EMAIL_DELIVERY,
        )
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1 FROM users LIMIT 1"))
    except Exception:
        logger.warning(
            "Database schema not found. Run `python -m app.cli init` from backend/ "
            "before using the API."
        )
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    # Swagger UI and the schema are a development aid; on a public deployment they
    # expose the full route and model inventory to anyone who asks.
    docs_enabled = settings.ENVIRONMENT != "production"
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Attestive: an adaptive learning platform. Phase 1 exposes authentication, "
            "onboarding, the subject catalogue and the student dashboard."
        ),
        docs_url="/docs" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    # Order matters: the last middleware added is the outermost. Security headers
    # must cover rate-limit rejections too, and CORS must cover them so a browser
    # can read the 429 body.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    install_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        body = {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "api": settings.API_V1_PREFIX,
        }
        if docs_enabled:
            body["docs"] = "/docs"
        return body

    return app


app = create_app()
