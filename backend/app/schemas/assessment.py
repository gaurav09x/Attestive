from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuestionPublic(BaseModel):
    id: uuid.UUID
    kind: str
    prompt: str
    options: list[str] | None = None
    position: int
    difficulty: int


class AttemptQuestion(QuestionPublic):
    saved_response: Any | None = None


class AssessmentSubjectSummary(BaseModel):
    subject_id: uuid.UUID
    subject_slug: str
    subject_name: str
    subject_description: str
    accent: str
    assessment_id: uuid.UUID | None = None
    title: str | None = None
    estimated_minutes: int | None = None
    question_count: int = 0
    in_progress_attempt_id: uuid.UUID | None = None
    last_attempt_id: uuid.UUID | None = None
    last_score: float | None = None
    last_completed_at: datetime | None = None


class AssessmentOverview(BaseModel):
    subjects: list[AssessmentSubjectSummary]


class AttemptRead(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    title: str
    subject_name: str
    subject_slug: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    questions: list[AttemptQuestion]
    answered_count: int
    total_questions: int


class ResponseInput(BaseModel):
    question_id: uuid.UUID
    response: dict[str, Any]


class SubmitRequest(BaseModel):
    responses: list[ResponseInput] = Field(default_factory=list, max_length=50)


class SavedResponse(BaseModel):
    question_id: uuid.UUID
    saved: bool = True


class SkillResult(BaseModel):
    skill_id: uuid.UUID
    slug: str
    name: str
    score: int
    proficiency: int
    confidence: int


class AttemptResult(BaseModel):
    attempt_id: uuid.UUID
    score_percent: int
    correct_count: int
    partial_count: int
    total_questions: int
    proficiency_estimate: int
    weak_skills: list[str]
    skill_results: list[SkillResult]
    roadmap_id: uuid.UUID | None = None
    xp_awarded: int
    generated_by: str | None = None
    achievements_unlocked: list[str] = Field(default_factory=list)


class ReviewQuestion(BaseModel):
    id: uuid.UUID
    prompt: str
    kind: str
    options: list[str] | None = None
    response: Any | None = None
    correct_answer: str | None = None
    is_correct: bool | None = None
    score: float | None = None
    feedback: str | None = None
    explanation: str | None = None
    skill_name: str | None = None


class AttemptReview(BaseModel):
    attempt_id: uuid.UUID
    title: str
    subject_name: str
    subject_slug: str
    score_percent: float | None = None
    proficiency_estimate: float | None = None
    weak_skills: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None
    roadmap_id: uuid.UUID | None = None
    skills: list[SkillResult] = Field(default_factory=list)
    questions: list[ReviewQuestion] = Field(default_factory=list)
