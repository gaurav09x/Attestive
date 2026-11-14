"""Subject / skill / course catalogue. Curated content, not per-user state."""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import CourseLevel, LessonKind


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="engineering", nullable=False)
    accent: Mapped[str] = mapped_column(String(20), default="blue", nullable=False)
    icon: Mapped[str] = mapped_column(String(40), default="code", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    skills: Mapped[list["Skill"]] = relationship(back_populates="subject")
    courses: Mapped[list["Course"]] = relationship(back_populates="subject")


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("subject_id", "slug", name="subject_skill_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    subject: Mapped[Subject] = relationship(back_populates="skills")


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(20), default=CourseLevel.BEGINNER.value, nullable=False)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False)

    subject: Mapped[Subject] = relationship(back_populates="courses")
    modules: Mapped[list["Module"]] = relationship(
        back_populates="course", order_by="Module.position", cascade="all, delete-orphan"
    )


class Module(Base, TimestampMixin):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("course_id", "position", name="course_module_position"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    is_project: Mapped[bool] = mapped_column(default=False, nullable=False)
    # Skill slugs covered by this module; used by the roadmap planner to target gaps.
    skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="module", order_by="Lesson.position", cascade="all, delete-orphan"
    )


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("module_id", "position", name="module_lesson_position"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default=LessonKind.READING.value, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    module: Mapped[Module] = relationship(back_populates="lessons")
