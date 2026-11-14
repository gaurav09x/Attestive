from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RoleSkillRead(BaseModel):
    skill_id: uuid.UUID | None = None
    skill_slug: str
    name: str
    subject_name: str
    target: int
    importance: int
    proficiency: int
    confidence: int
    gap: int
    status: str  # met | close | missing
    evidence_source: str


class CareerRoleSummary(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    level: str
    version: int
    skill_count: int
    met_count: int
    readiness_score: int
    readiness_label: str


class CareerRecommendation(BaseModel):
    kind: str
    title: str
    description: str
    reason: str
    target_url: str | None = None


class PortfolioBrief(BaseModel):
    title: str
    brief: str
    skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class GapAnalysis(BaseModel):
    role_id: uuid.UUID
    role_slug: str
    role_title: str
    version: int
    readiness_score: int
    readiness_label: str
    met_count: int
    total_count: int
    skills: list[RoleSkillRead] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)


class CareerRoleDetail(CareerRoleSummary):
    skills: list[RoleSkillRead] = Field(default_factory=list)
    recommendations: list[CareerRecommendation] = Field(default_factory=list)
    portfolio_briefs: list[PortfolioBrief] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    generated_by: str
    disclaimer: str


class CareerRoleListResponse(BaseModel):
    items: list[CareerRoleSummary] = Field(default_factory=list)
    disclaimer: str


class StartInterviewRequest(BaseModel):
    role_slug: str = Field(min_length=2, max_length=60)


class InterviewQuestionRead(BaseModel):
    id: uuid.UUID
    kind: str
    prompt: str
    difficulty: int
    position: int
    skill_name: str | None = None
    answer: str | None = None
    score: float | None = None
    matched_points: list[str] = Field(default_factory=list)
    feedback: str | None = None
    model_answer: str | None = None


class MockInterviewSummary(BaseModel):
    id: uuid.UUID
    role_slug: str
    role_title: str
    status: str
    overall_score: float | None = None
    readiness: str | None = None
    feedback: list[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None
    answered: int
    total: int


class MockInterviewDetail(MockInterviewSummary):
    questions: list[InterviewQuestionRead] = Field(default_factory=list)
    disclaimer: str


class MockInterviewListResponse(BaseModel):
    items: list[MockInterviewSummary] = Field(default_factory=list)


class SubmitAnswerRequest(BaseModel):
    question_id: uuid.UUID
    answer: str = Field(min_length=1, max_length=6000)


class ResumeSkillRead(BaseModel):
    id: uuid.UUID
    label: str
    claimed_level: str
    skill_id: uuid.UUID | None = None
    skill_slug: str | None = None
    skill_name: str | None = None
    subject_name: str | None = None
    measured_proficiency: int | None = None
    verified: bool
    evidence: str


class ResumeSkillListResponse(BaseModel):
    items: list[ResumeSkillRead] = Field(default_factory=list)


class ResumeSkillRequest(BaseModel):
    label: str = Field(min_length=2, max_length=120)
    claimed_level: str = Field(default="unspecified", max_length=20)
