from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.auth import ProfileRead, PreferencesRead, SubjectRead


class LevelInfo(BaseModel):
    level: int
    xp_total: int
    xp_into_level: int
    xp_for_next_level: int
    progress_percent: int


class WeeklyGoal(BaseModel):
    target_minutes: int
    completed_minutes: int
    percent: int


class DashboardStats(BaseModel):
    total_learning_minutes: int
    lessons_completed: int
    skills_acquired: int
    active_paths: int


class DashboardUser(BaseModel):
    id: uuid.UUID
    first_name: str
    full_name: str
    initials: str
    career_goal: str | None = None
    experience_level: str | None = None
    streak_days: int
    subjects: list[SubjectRead]


class PathItemPreview(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    is_project: bool
    estimated_minutes: int
    position: int


class CurrentPath(BaseModel):
    id: uuid.UUID
    title: str
    subject_name: str
    subject_accent: str
    rationale: str
    estimated_weeks: int
    target_level: str
    items_total: int
    items_completed: int
    progress_percent: int
    next_item: PathItemPreview | None = None
    items: list[PathItemPreview]


class ActivityDay(BaseModel):
    day: date
    minutes: int
    xp: int


class SkillPreview(BaseModel):
    name: str
    proficiency: int
    subject_name: str


class AchievementPreview(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    xp_reward: int
    unlocked_at: datetime


class AssessmentPreview(BaseModel):
    id: uuid.UUID
    title: str
    kind: str
    level: str
    subject_name: str
    estimated_minutes: int


class RecommendationPreview(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    description: str
    reason: str
    target_url: str | None = None


class DashboardResponse(BaseModel):
    user: DashboardUser
    profile: ProfileRead | None
    preferences: PreferencesRead | None
    level: LevelInfo
    weekly_goal: WeeklyGoal
    stats: DashboardStats
    current_path: CurrentPath | None
    activity_series: list[ActivityDay]
    top_skills: list[SkillPreview]
    achievements: list[AchievementPreview]
    upcoming_assessments: list[AssessmentPreview]
    recommendations: list[RecommendationPreview]
