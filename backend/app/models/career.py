"""Career development: curated role maps, mock interviews and resume claims.

Role maps are versioned curated data (JSON skill requirements), not per-user
state. A mock interview snapshots which questions were answered; each answer is
scored against the question's rubric and stored with the matching evidence, so a
result can always be explained. A resume claim the student types is never
treated as evidence: `resume_skills` links the claim to a measured skill when
one exists and is labelled unverified otherwise.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow


class CareerRole(Base, TimestampMixin):
    """A target role with its required skills, kept as versioned curated data."""

    __tablename__ = "career_roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="entry", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # [{"subject_slug": "python", "skill_slug": "functions", "target": 65, "importance": 3}]
    skills: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    # [{"title": ..., "brief": ..., "skills": ["functions", "testing"]}]
    portfolio_briefs: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InterviewQuestion(Base, TimestampMixin):
    """Curated interview question with a rubric the evaluator scores against."""

    __tablename__ = "interview_questions"
    __table_args__ = (
        Index("ix_interview_questions_role_position", "role_id", "position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(String(24), default="conceptual", nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # [{"point": "...", "keywords": ["..."]}]
    rubric: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    model_answer: Mapped[str | None] = mapped_column(Text)


class MockInterview(Base, TimestampMixin):
    __tablename__ = "mock_interviews"
    __table_args__ = (
        Index("ix_mock_interviews_user_started", "user_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float)
    readiness: Mapped[str | None] = mapped_column(String(24))
    feedback: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    responses: Mapped[list["InterviewResponse"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan"
    )


class InterviewResponse(Base, TimestampMixin):
    __tablename__ = "interview_responses"
    __table_args__ = (
        UniqueConstraint("interview_id", "question_id", name="interview_question_once"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("mock_interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    matched_points: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    interview: Mapped[MockInterview] = relationship(back_populates="responses")


class ResumeSkill(Base, TimestampMixin):
    """A student-entered claim. Evidence lives in `user_skills`, never here."""

    __tablename__ = "resume_skills"
    __table_args__ = (UniqueConstraint("user_id", "label", name="user_resume_label"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="SET NULL"), index=True
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    claimed_level: Mapped[str] = mapped_column(String(20), default="unspecified", nullable=False)
