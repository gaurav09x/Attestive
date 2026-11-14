"""Dashboard aggregation.

Everything returned here is derived from the student's own rows. New students
get zeros and explicit empty states, never invented progress.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment, AssessmentAttempt
from app.models.catalog import Skill, Subject
from app.models.enums import AttemptStatus, ProgressStatus
from app.models.gamification import (
    Achievement,
    LearningRecommendation,
    UserAchievement,
)
from app.models.learning import LearningActivity, LearningPath, LessonProgress
from app.models.user import User, UserSkill, UserSubjectInterest
from app.schemas.dashboard import (
    AchievementPreview,
    ActivityDay,
    AssessmentPreview,
    CurrentPath,
    DashboardResponse,
    DashboardStats,
    DashboardUser,
    LevelInfo,
    PathItemPreview,
    RecommendationPreview,
    SkillPreview,
    WeeklyGoal,
)
from app.services.achievements import current_streak_days
from app.services.gamification import level_progress

SKILL_ACQUIRED_THRESHOLD = 60


def _local_today(timezone_name: str | None) -> date:
    try:
        tz = ZoneInfo(timezone_name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


async def _current_path(session: AsyncSession, user_id) -> CurrentPath | None:  # type: ignore[no-untyped-def]
    path = (
        await session.execute(
            select(LearningPath)
            .options(selectinload(LearningPath.items))
            .where(LearningPath.user_id == user_id, LearningPath.status == "active")
            .order_by(desc(LearningPath.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if path is None:
        return None

    subject = await session.get(Subject, path.subject_id)
    items = sorted(path.items, key=lambda item: item.position)
    completed = sum(1 for item in items if item.status == ProgressStatus.COMPLETED.value)
    total = len(items)
    next_item = next(
        (item for item in items if item.status != ProgressStatus.COMPLETED.value), None
    )
    return CurrentPath(
        id=path.id,
        title=path.title,
        subject_name=subject.name if subject else "Learning",
        subject_accent=subject.accent if subject else "blue",
        rationale=path.rationale,
        estimated_weeks=path.estimated_weeks,
        target_level=path.target_level,
        items_total=total,
        items_completed=completed,
        progress_percent=round(completed / total * 100) if total else 0,
        next_item=(
            PathItemPreview(
                id=next_item.id,
                title=next_item.title,
                status=next_item.status,
                is_project=next_item.is_project,
                estimated_minutes=next_item.estimated_minutes,
                position=next_item.position,
            )
            if next_item
            else None
        ),
        items=[
            PathItemPreview(
                id=item.id,
                title=item.title,
                status=item.status,
                is_project=item.is_project,
                estimated_minutes=item.estimated_minutes,
                position=item.position,
            )
            for item in items[:8]
        ],
    )


async def build_dashboard(session: AsyncSession, user: User) -> DashboardResponse:
    timezone_name = user.profile.timezone if user.profile else "UTC"
    today = _local_today(timezone_name)
    week_start = today - timedelta(days=today.weekday())
    thirty_days_ago = today - timedelta(days=29)
    seven_days_ago = today - timedelta(days=6)

    total_minutes = (
        await session.execute(
            select(func.coalesce(func.sum(LearningActivity.minutes), 0)).where(
                LearningActivity.user_id == user.id
            )
        )
    ).scalar_one()

    weekly_minutes = (
        await session.execute(
            select(func.coalesce(func.sum(LearningActivity.minutes), 0)).where(
                LearningActivity.user_id == user.id,
                LearningActivity.occurred_on >= week_start,
            )
        )
    ).scalar_one()

    lessons_completed = (
        await session.execute(
            select(func.count())
            .select_from(LessonProgress)
            .where(
                LessonProgress.user_id == user.id,
                LessonProgress.status == ProgressStatus.COMPLETED.value,
            )
        )
    ).scalar_one()

    skills_acquired = (
        await session.execute(
            select(func.count())
            .select_from(UserSkill)
            .where(
                UserSkill.user_id == user.id,
                UserSkill.proficiency >= SKILL_ACQUIRED_THRESHOLD,
            )
        )
    ).scalar_one()

    active_paths = (
        await session.execute(
            select(func.count())
            .select_from(LearningPath)
            .where(LearningPath.user_id == user.id, LearningPath.status == "active")
        )
    ).scalar_one()

    activity_rows = (
        await session.execute(
            select(LearningActivity.occurred_on, LearningActivity.minutes, LearningActivity.xp_awarded)
            .where(
                LearningActivity.user_id == user.id,
                LearningActivity.occurred_on >= thirty_days_ago,
            )
        )
    ).all()
    per_day: dict[date, tuple[int, int]] = {}
    for day, minutes, xp in activity_rows:
        current_minutes, current_xp = per_day.get(day, (0, 0))
        per_day[day] = (current_minutes + int(minutes), current_xp + int(xp))

    activity_series = [
        ActivityDay(
            day=seven_days_ago + timedelta(days=offset),
            minutes=per_day.get(seven_days_ago + timedelta(days=offset), (0, 0))[0],
            xp=per_day.get(seven_days_ago + timedelta(days=offset), (0, 0))[1],
        )
        for offset in range(7)
    ]

    achievements = [
        AchievementPreview(
            code=achievement.code,
            name=achievement.name,
            description=achievement.description,
            icon=achievement.icon,
            xp_reward=achievement.xp_reward,
            unlocked_at=unlocked_at,
        )
        for achievement, unlocked_at in (
            await session.execute(
                select(Achievement, UserAchievement.unlocked_at)
                .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
                .where(UserAchievement.user_id == user.id)
                .order_by(desc(UserAchievement.unlocked_at))
                .limit(4)
            )
        ).all()
    ]

    top_skills = [
        SkillPreview(name=name, proficiency=proficiency, subject_name=subject_name)
        for name, proficiency, subject_name in (
            await session.execute(
                select(Skill.name, UserSkill.proficiency, Subject.name)
                .join(UserSkill, UserSkill.skill_id == Skill.id)
                .join(Subject, Subject.id == Skill.subject_id)
                .where(UserSkill.user_id == user.id, UserSkill.proficiency > 0)
                .order_by(desc(UserSkill.proficiency))
                .limit(5)
            )
        ).all()
    ]

    interests = (
        await session.execute(
            select(Subject)
            .join(UserSubjectInterest, UserSubjectInterest.subject_id == Subject.id)
            .where(UserSubjectInterest.user_id == user.id)
            .order_by(Subject.name)
        )
    ).scalars().all()
    interest_ids = [subject.id for subject in interests]

    upcoming = []
    if interest_ids:
        completed_attempts = select(AssessmentAttempt.assessment_id).where(
            AssessmentAttempt.user_id == user.id,
            AssessmentAttempt.status == AttemptStatus.COMPLETED.value,
        )
        upcoming = [
            AssessmentPreview(
                id=assessment.id,
                title=assessment.title,
                kind=assessment.kind,
                level=assessment.level,
                subject_name=subject_name,
                estimated_minutes=assessment.estimated_minutes,
            )
            for assessment, subject_name in (
                await session.execute(
                    select(Assessment, Subject.name)
                    .join(Subject, Subject.id == Assessment.subject_id)
                    .where(
                        Assessment.is_active.is_(True),
                        Assessment.subject_id.in_(interest_ids),
                        Assessment.id.not_in(completed_attempts),
                    )
                    .order_by(Assessment.estimated_minutes)
                    .limit(3)
                )
            ).all()
        ]

    recommendations = [
        RecommendationPreview(
            id=row.id,
            kind=row.kind,
            title=row.title,
            description=row.description,
            reason=row.reason,
            target_url=row.target_url,
        )
        for row in (
            await session.execute(
                select(LearningRecommendation)
                .where(
                    LearningRecommendation.user_id == user.id,
                    LearningRecommendation.is_dismissed.is_(False),
                )
                .order_by(desc(LearningRecommendation.priority), desc(LearningRecommendation.created_at))
                .limit(3)
            )
        ).scalars()
    ]

    level, xp_into, xp_needed = level_progress(user.xp_total)
    target_minutes = (user.profile.weekly_minutes_goal if user.profile else None) or 300

    return DashboardResponse(
        user=DashboardUser(
            id=user.id,
            first_name=user.full_name.split()[0],
            full_name=user.full_name,
            initials="".join(part[0].upper() for part in user.full_name.split()[:2]) or "S",
            career_goal=user.profile.career_goal if user.profile else None,
            experience_level=user.profile.experience_level if user.profile else None,
            streak_days=await current_streak_days(session, user.id, today),
            subjects=interests,
        ),
        profile=user.profile,
        preferences=user.preferences,
        level=LevelInfo(
            level=level,
            xp_total=user.xp_total,
            xp_into_level=xp_into,
            xp_for_next_level=xp_needed,
            progress_percent=min(100, round(xp_into / xp_needed * 100)) if xp_needed else 0,
        ),
        weekly_goal=WeeklyGoal(
            target_minutes=target_minutes,
            completed_minutes=int(weekly_minutes),
            percent=min(100, round(int(weekly_minutes) / target_minutes * 100))
            if target_minutes
            else 0,
        ),
        stats=DashboardStats(
            total_learning_minutes=int(total_minutes),
            lessons_completed=int(lessons_completed),
            skills_acquired=int(skills_acquired),
            active_paths=int(active_paths),
        ),
        current_path=await _current_path(session, user.id),
        activity_series=activity_series,
        top_skills=top_skills,
        achievements=achievements,
        upcoming_assessments=upcoming,
        recommendations=recommendations,
    )
