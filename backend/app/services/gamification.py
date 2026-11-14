"""Level curve and XP award rules.

The curve is intentionally gentle early and steeper later:
level 1 costs 500 XP, each subsequent level costs 25% more than the previous.
"""

from __future__ import annotations

import math
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utc_now
from app.models.gamification import XPTransaction
from app.models.learning import LearningActivity

BASE_LEVEL_XP = 500
LEVEL_GROWTH = 1.25

XP_RULES: dict[str, int] = {
    "lesson_completed": 40,
    "assessment_completed": 80,
    "assessment_excellent": 120,
    "coding_exercise_solved": 100,
    "project_completed": 250,
    "daily_streak": 25,
    "tutor_session": 10,
    "mock_interview_completed": 120,
}


def level_progress(xp_total: int) -> tuple[int, int, int]:
    """Return (level, xp_into_level, xp_required_for_this_level)."""
    xp = max(0, int(xp_total))
    level = 1
    requirement = BASE_LEVEL_XP
    while xp >= requirement:
        xp -= requirement
        level += 1
        requirement = int(round(requirement * LEVEL_GROWTH))
    return level, xp, requirement


def level_percent(xp_total: int) -> int:
    level, into, req = level_progress(xp_total)
    del level
    if req <= 0:
        return 0
    return min(100, max(0, round(into / req * 100)))


def xp_for_action(action: str) -> int:
    return XP_RULES.get(action, 0)


def proficiency_from_self_report(experience_level: str) -> int:
    """Honest self-report seed: low confidence, refined by assessments later."""
    return {
        "none": 0,
        "beginner": 20,
        "intermediate": 45,
        "advanced": 65,
    }.get(experience_level, 0)


async def award_xp(
    session: AsyncSession,
    user,  # type: ignore[no-untyped-def]
    amount: int,
    reason: str,
    source_type: str | None = None,
    source_id: UUID | None = None,
) -> int:
    """Append to the XP ledger and update the cached total in one transaction.

    Idempotent per (source_type, source_id): replaying the same completion must not
    award XP twice.
    """
    if amount <= 0:
        return 0
    if source_type and source_id is not None:
        existing = (
            await session.execute(
                select(XPTransaction.id).where(
                    XPTransaction.user_id == user.id,
                    XPTransaction.source_type == source_type,
                    XPTransaction.source_id == source_id,
                )
            )
        ).first()
        if existing:
            return 0

    session.add(
        XPTransaction(
            user_id=user.id,
            amount=amount,
            reason=reason,
            source_type=source_type,
            source_id=source_id,
        )
    )
    user.xp_total += amount
    return amount


def record_activity(
    session: AsyncSession,
    *,
    user_id: UUID,
    kind: str,
    minutes: int,
    xp_awarded: int = 0,
    subject_id: UUID | None = None,
    day: date | None = None,
) -> LearningActivity:
    activity = LearningActivity(
        user_id=user_id,
        subject_id=subject_id,
        kind=kind,
        minutes=max(0, minutes),
        xp_awarded=max(0, xp_awarded),
        occurred_on=day or utc_now().date(),
    )
    session.add(activity)
    return activity


def proficiency_summary(values: list[int]) -> str:
    if not values:
        return "unknown"
    avg = sum(values) / len(values)
    if math.isnan(avg):
        return "unknown"
    if avg < 25:
        return "beginner"
    if avg < 55:
        return "developing"
    if avg < 80:
        return "proficient"
    return "advanced"
