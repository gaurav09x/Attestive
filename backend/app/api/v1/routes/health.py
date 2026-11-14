from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import engine
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    """Readiness probe.

    Returns 503 when the database is unreachable so a platform health check
    (Render, an ALB target group) takes the instance out of rotation instead of
    routing traffic to a process that cannot serve a single request.
    """
    database = "ok"
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:  # health must report, not raise
        database = "unavailable"
    healthy = database == "ok"
    return JSONResponse(
        status_code=200 if healthy else 503,
        headers={"Cache-Control": "no-store"},
        content={
            "status": "ok" if healthy else "degraded",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": database,
            "ai_provider": settings.AI_PROVIDER,
        },
    )
