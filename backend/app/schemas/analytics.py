from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class AnalyticsTotals(BaseModel):
    minutes: int
    xp: int
    streak_days: int
    assessments_completed: int
    roadmap_items_completed: int
    lessons_completed: int


class ActivityPoint(BaseModel):
    day: date
    minutes: int
    xp: int


class StudyKind(BaseModel):
    kind: str
    minutes: int


class SubjectInsight(BaseModel):
    subject_id: uuid.UUID
    subject_name: str
    accent: str
    average_proficiency: int
    skills_tracked: int
    minutes: int


class AssessmentPoint(BaseModel):
    attempt_id: uuid.UUID
    subject_name: str
    score_percent: float
    completed_at: datetime


class WeakSkill(BaseModel):
    skill_id: uuid.UUID
    name: str
    subject_name: str
    proficiency: int
    confidence: int


class AnalyticsResponse(BaseModel):
    range_days: int
    totals: AnalyticsTotals
    activity: list[ActivityPoint] = Field(default_factory=list)
    study_by_kind: list[StudyKind] = Field(default_factory=list)
    subjects: list[SubjectInsight] = Field(default_factory=list)
    assessment_trend: list[AssessmentPoint] = Field(default_factory=list)
    weak_skills: list[WeakSkill] = Field(default_factory=list)
    revision_suggestions: list[str] = Field(default_factory=list)
