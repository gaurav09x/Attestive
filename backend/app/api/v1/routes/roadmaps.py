from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.roadmap import RoadmapListResponse, RoadmapRead, UpdateRoadmapItemRequest
from app.services import roadmap_service

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


@router.get("", response_model=RoadmapListResponse)
async def list_roadmaps(user: CurrentUser, session: DbSession) -> RoadmapListResponse:
    items = await roadmap_service.list_roadmaps(session, user)
    return RoadmapListResponse(items=items)


@router.get("/{path_id}", response_model=RoadmapRead)
async def get_roadmap(path_id: uuid.UUID, user: CurrentUser, session: DbSession) -> RoadmapRead:
    return await roadmap_service.get_roadmap(session, user, path_id)


@router.patch("/{path_id}/items/{item_id}", response_model=RoadmapRead)
async def update_item(
    path_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: UpdateRoadmapItemRequest,
    user: CurrentUser,
    session: DbSession,
) -> RoadmapRead:
    return await roadmap_service.update_item(session, user, path_id, item_id, payload.status)
