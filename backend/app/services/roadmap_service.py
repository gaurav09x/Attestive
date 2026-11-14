"""Roadmap generation and progress tracking.

Sequencing is evidence-based and deterministic: modules covering weak skills are
selected first from curated curriculum, then breadth is added, and a project is
placed at the end. The AI agent may write the plan note; it never chooses modules
or writes to the database itself.
"""

from __future__ import annotations

import logging
import math
import uuid

from sqlalchemy import case, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.roadmap_agent import write_plan_note
from app.core.config import settings
from app.core.errors import AppError, not_found
from app.core.time import utc_now
from app.models.catalog import Course, Module, Subject
from app.models.enums import ProgressStatus
from app.models.learning import LearningPath, LearningPathItem
from app.models.user import User
from app.schemas.roadmap import RoadmapItemRead, RoadmapRead
from app.services.achievements import evaluate_achievements
from app.services.gamification import award_xp, xp_for_action

logger = logging.getLogger(__name__)

DEFAULT_WEEKLY_MINUTES = 300
WEAK_SKILL_THRESHOLD = 75


def _target_level(average: float) -> str:
    if average < 0.4:
        return "beginner"
    if average < 0.7:
        return "intermediate"
    return "advanced"


def _select_modules(
    modules: list[Module], weak_slugs: set[str], prefers_projects: bool
) -> list[Module]:
    if not modules:
        return []

    selected = [module for module in modules if weak_slugs & set(module.skill_slugs or [])]
    if len(selected) < 3:
        for module in modules:
            if module not in selected:
                selected.append(module)
            if len(selected) >= 3:
                break

    if prefers_projects:
        has_project = any(module.is_project for module in selected)
        if not has_project and len(selected) < 6:
            project = next((module for module in modules if module.is_project), None)
            if project is not None:
                selected.append(project)
    else:
        without_projects = [module for module in selected if not module.is_project]
        if without_projects:
            selected = without_projects

    ordered = sorted(set(selected), key=modules.index)
    return ordered[:6]


def _deterministic_rationale(
    skill_names: list[str], module_count: int, weeks: int, weekly_minutes: int, has_project: bool
) -> str:
    if skill_names:
        focus = f"Your diagnostic showed the most room in {', '.join(skill_names[:3])}."
    else:
        focus = "Your diagnostic showed a broad baseline, so this path builds depth across the subject."
    ending = " It finishes with a project you can show." if has_project else ""
    return (
        f"{focus} The plan sequences {module_count} modules over about {weeks} "
        f"{'week' if weeks == 1 else 'weeks'} at {weekly_minutes} minutes per week, "
        f"with practice after each concept.{ending}"
    )


async def _load_modules(session: AsyncSession, subject_id: uuid.UUID) -> list[Module]:
    rows = (
        await session.execute(
            select(Module)
            .join(Course, Course.id == Module.course_id)
            .where(Course.subject_id == subject_id, Course.is_published.is_(True))
            .order_by(Course.title, Module.position)
        )
    ).scalars().all()
    return list(rows)


async def generate_roadmap(
    session: AsyncSession,
    user: User,
    subject: Subject,
    skill_updates: list,  # list[proficiency_service.SkillUpdate]
    average_score: float,
) -> LearningPath:
    modules = await _load_modules(session, subject.id)
    if not modules:
        raise AppError(
            "curriculum_unavailable",
            f"No published curriculum exists for {subject.name} yet.",
            409,
        )

    weak_names = [update.name for update in skill_updates if update.score < WEAK_SKILL_THRESHOLD]
    weak_slugs = {update.slug for update in skill_updates if update.score < WEAK_SKILL_THRESHOLD}
    prefers_projects = user.preferences.prefers_projects if user.preferences else True
    selected = _select_modules(modules, weak_slugs, prefers_projects)

    weekly_minutes = (user.profile.weekly_minutes_goal if user.profile else None) or DEFAULT_WEEKLY_MINUTES
    total_minutes = sum(module.estimated_minutes for module in selected)
    weeks = max(1, math.ceil(total_minutes / weekly_minutes))
    target_level = _target_level(average_score)
    has_project = any(module.is_project for module in selected)

    rationale = _deterministic_rationale(
        weak_names, len(selected), weeks, weekly_minutes, has_project
    )
    generated_by = "deterministic"

    note = await write_plan_note(
        subject_name=subject.name,
        target_level=target_level,
        weak_skills=weak_names,
        module_titles=[module.title for module in selected],
        weekly_minutes=weekly_minutes,
        estimated_weeks=weeks,
    )
    if note:
        rationale = note[:600]
        generated_by = f"openai:{settings.OPENAI_MODEL}"

    # Only one active path per subject: archive the previous plan.
    await session.execute(
        update(LearningPath)
        .where(
            LearningPath.user_id == user.id,
            LearningPath.subject_id == subject.id,
            LearningPath.status == "active",
        )
        .values(status="archived")
    )

    path = LearningPath(
        user_id=user.id,
        subject_id=subject.id,
        title=f"{subject.name} roadmap",
        rationale=rationale,
        target_level=target_level,
        status="active",
        estimated_weeks=weeks,
        generated_by=generated_by,
    )
    path.items = [
        LearningPathItem(
            course_id=module.course_id,
            title=module.title,
            objective=module.summary,
            position=position,
            estimated_minutes=module.estimated_minutes,
            is_project=module.is_project,
            status=ProgressStatus.NOT_STARTED.value,
        )
        for position, module in enumerate(selected, start=1)
    ]
    session.add(path)
    await session.flush()
    return path


def _to_read(path: LearningPath, subject: Subject) -> RoadmapRead:
    items = sorted(path.items, key=lambda item: item.position)
    completed = sum(1 for item in items if item.status == ProgressStatus.COMPLETED.value)
    total = len(items)
    return RoadmapRead(
        id=path.id,
        title=path.title,
        subject_id=subject.id,
        subject_slug=subject.slug,
        subject_name=subject.name,
        accent=subject.accent,
        rationale=path.rationale,
        target_level=path.target_level,
        status=path.status,
        estimated_weeks=path.estimated_weeks,
        generated_by=path.generated_by,
        created_at=path.created_at,
        items_total=total,
        items_completed=completed,
        progress_percent=round(completed / total * 100) if total else 0,
        items=[
            RoadmapItemRead(
                id=item.id,
                title=item.title,
                objective=item.objective,
                position=item.position,
                status=item.status,
                is_project=item.is_project,
                estimated_minutes=item.estimated_minutes,
                completed_at=item.completed_at,
            )
            for item in items
        ],
    )


async def list_roadmaps(session: AsyncSession, user: User) -> list[RoadmapRead]:
    rows = (
        await session.execute(
            select(LearningPath, Subject)
            .join(Subject, Subject.id == LearningPath.subject_id)
            .options(selectinload(LearningPath.items))
            .where(LearningPath.user_id == user.id)
            .order_by(
                case((LearningPath.status == "active", 0), else_=1),
                desc(LearningPath.created_at),
            )
        )
    ).all()
    return [_to_read(path, subject) for path, subject in rows]


async def get_roadmap(session: AsyncSession, user: User, path_id: uuid.UUID) -> RoadmapRead:
    row = (
        await session.execute(
            select(LearningPath, Subject)
            .join(Subject, Subject.id == LearningPath.subject_id)
            .options(selectinload(LearningPath.items))
            .where(LearningPath.id == path_id, LearningPath.user_id == user.id)
        )
    ).first()
    if row is None:
        raise not_found("Roadmap")
    return _to_read(row[0], row[1])


async def update_item(
    session: AsyncSession,
    user: User,
    path_id: uuid.UUID,
    item_id: uuid.UUID,
    new_status: str,
) -> RoadmapRead:
    if new_status not in ("in_progress", "completed"):
        raise AppError(
            "invalid_status",
            "Status must be 'in_progress' or 'completed'.",
            422,
        )

    row = (
        await session.execute(
            select(LearningPath, Subject)
            .join(Subject, Subject.id == LearningPath.subject_id)
            .options(selectinload(LearningPath.items))
            .where(LearningPath.id == path_id, LearningPath.user_id == user.id)
        )
    ).first()
    if row is None:
        raise not_found("Roadmap")
    path, subject = row

    item = next((entry for entry in path.items if entry.id == item_id), None)
    if item is None:
        raise not_found("Roadmap item")

    if item.status == ProgressStatus.COMPLETED.value:
        # Idempotent: replaying a completion must not award XP twice.
        return _to_read(path, subject)

    if new_status == "completed":
        item.status = ProgressStatus.COMPLETED.value
        item.completed_at = utc_now()
        await award_xp(
            session,
            user,
            xp_for_action("lesson_completed"),
            "roadmap_item_completed",
            "path_item",
            item.id,
        )
        if all(entry.status == ProgressStatus.COMPLETED.value for entry in path.items):
            path.status = "completed"
        # A finished step can complete a milestone (for example a shipped project).
        await evaluate_achievements(session, user)
    elif item.status == ProgressStatus.NOT_STARTED.value:
        item.status = ProgressStatus.IN_PROGRESS.value

    await session.commit()
    return _to_read(path, subject)
