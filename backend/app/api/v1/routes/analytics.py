from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.analytics import AnalyticsResponse
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsResponse)
async def overview(user: CurrentUser, session: DbSession) -> AnalyticsResponse:
    return await analytics_service.build_analytics(session, user)
