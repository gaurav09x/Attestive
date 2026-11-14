"""Achievement evaluation and streak calculation.

Criteria live in `achievements.criteria` (seeded data), not in branching code, so
a new milestone is a seed change rather than a service change. Evaluation is
idempotent twice over: the unique (user, achievement) row and the XP ledger's
(source_type, source_id) key both refuse a second award.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import local_today
from app.models.career import MockInterview
from app.models.enums import ProgressStatus
from app.models.gamification import Achievement, UserAchievement
from app.models.learning import (
    LearningActivity,
    LearningPath,
    LearningPathItem,
    LessonProgress,
)
from app.models.user import User, UserSkill
from app.services.gamification import award_xp

SKILL_ACQUIRED_THRESHOLD = 60


async def current_streak_days(
    session: AsyncSession, user_id: UUID, today: date
) -> int:
    """Consecutive activity days counted backwards from today (or yesterday)."""
    days = (
        await session.execute(
            select(distinct(LearningActivity.occurred_on))
            .where(LearningActivity.user_id == user_id)
            .order_by(desc(LearningActivity.occurred_on))
            .limit(730)
        )
    ).scalars().all()
    if not days:
        return 0
    if days[0] == today:
        cursor = today
    elif days[0] == today - timedelta(days=1):
        cursor = days[0]
    else:
        return 0

    streak = 0
    for day in days:
        if day == cursor:
            streak += 1
            cursor -= timedelta(days=1)
        elif day < cursor:
            break
    return streak


async def _metrics(
    session: AsyncSession, user_id: UUID, today: date
) -> dict[str, int]:
    lessons_completed = (
        await session.execute(
            select(func.count())
            .select_from(LessonProgress)
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.status == ProgressStatus.COMPLETED.value,
            )
        )
    ).scalar_one()

    skills_acquired = (
        await session.execute(
            select(func.count())
            .select_from(UserSkill)
            .where(
                UserSkill.user_id == user_id,
                UserSkill.proficiency >= SKILL_ACQUIRED_THRESHOLD,
            )
        )
    ).scalar_one()

    projects_completed = (
        await session.execute(
            select(func.count())
            .select_from(LearningPathItem)
            .join(LearningPath, LearningPath.id == LearningPathItem.path_id)
            .where(
                LearningPath.user_id == user_id,
                LearningPathItem.is_project.is_(True),
                LearningPathItem.status == ProgressStatus.COMPLETED.value,
            )
        )
    ).scalar_one()

    mock_interviews_completed = (
        await session.execute(
            select(func.count())
            .select_from(MockInterview)
            .where(
                MockInterview.user_id == user_id,
                MockInterview.status == "completed",
            )
        )
    ).scalar_one()

    return {
        "lessons_completed": int(lessons_completed),
        "skills_acquired": int(skills_acquired),
        "projects_completed": int(projects_completed),
        "mock_interviews_completed": int(mock_interviews_completed),
        "streak_days": await current_streak_days(session, user_id, today),
        # No exercise runner exists yet (Phase 4), so this stays at zero rather
        # than counting attempts that were never executed.
        "coding_exercises_solved": 0,
    }


async def evaluate_achievements(
    session: AsyncSession, user: User, today: date | None = None
) -> list[str]:
    """Unlock newly earned achievements and return their codes."""
    if today is None:
        today = local_today(user.profile.timezone if user.profile else None)

    achievements = (
        await session.execute(
            select(Achievement).where(Achievement.is_active.is_(True))
        )
    ).scalars().all()
    if not achievements:
        return []

    # Callers evaluate inside the same transaction as their own writes; flush so
    # newly recorded evidence is visible to the metric queries.
    await session.flush()

    unlocked = set(
        (
            await session.execute(
                select(UserAchievement.achievement_id).where(
                    UserAchievement.user_id == user.id
                )
            )
        ).scalars()
    )
    metrics = await _metrics(session, user.id, today)

    newly_unlocked: list[str] = []
    for achievement in achievements:
        if achievement.id in unlocked:
            continue
        criteria = achievement.criteria or {}
        kind = criteria.get("type")
        try:
            threshold = int(criteria.get("threshold", 0) or 0)
        except (TypeError, ValueError):
            continue
        if not isinstance(kind, str) or threshold <= 0:
            continue
        if metrics.get(kind, 0) < threshold:
            continue

        session.add(
            UserAchievement(user_id=user.id, achievement_id=achievement.id)
        )
        await award_xp(
            session,
            user,
            achievement.xp_reward,
            f"achievement:{achievement.code}",
            "achievement",
            achievement.id,
        )
        newly_unlocked.append(achievement.code)

    return newly_unlocked
