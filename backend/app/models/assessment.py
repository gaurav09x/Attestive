"""Assessment schema. Generated and evaluated by the assessment agent in Phase 2."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow
from app.models.enums import AssessmentKind, AttemptStatus, QuestionKind


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    kind: Mapped[str] = mapped_column(
        String(20), default=AssessmentKind.DIAGNOSTIC.value, nullable=False
    )
    level: Mapped[str] = mapped_column(String(20), default="beginner", nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(32), default="system", nullable=False)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="assessment",
        order_by="Question.position",
        cascade="all, delete-orphan",
    )


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(
        String(24), default=QuestionKind.MULTIPLE_CHOICE.value, nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON)
    correct_answer: Mapped[dict | list | str | None] = mapped_column(JSON)
    explanation: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class AssessmentAttempt(Base, TimestampMixin):
    __tablename__ = "assessment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=AttemptStatus.IN_PROGRESS.value, nullable=False
    )
    score: Mapped[float | None] = mapped_column(Float)
    proficiency_estimate: Mapped[float | None] = mapped_column(Float)
    weak_skills: Mapped[list[str] | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    responses: Mapped[list["AssessmentResponse"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class AssessmentResponse(Base, TimestampMixin):
    __tablename__ = "assessment_responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    response: Mapped[dict | list | str | int | None] = mapped_column(JSON)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempt: Mapped[AssessmentAttempt] = relationship(back_populates="responses")
