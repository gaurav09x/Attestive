from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RoadmapItemRead(BaseModel):
    id: uuid.UUID
    title: str
    objective: str
    position: int
    status: str
    is_project: bool
    estimated_minutes: int
    completed_at: datetime | None = None


class RoadmapRead(BaseModel):
    id: uuid.UUID
    title: str
    subject_id: uuid.UUID
    subject_slug: str
    subject_name: str
    accent: str
    rationale: str
    target_level: str
    status: str
    estimated_weeks: int
    generated_by: str
    created_at: datetime
    items_total: int
    items_completed: int
    progress_percent: int
    items: list[RoadmapItemRead] = Field(default_factory=list)


class RoadmapListResponse(BaseModel):
    items: list[RoadmapRead]


class UpdateRoadmapItemRequest(BaseModel):
    status: str
