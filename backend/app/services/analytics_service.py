"""Progress analytics computed from the student's own rows.

Every series has an explicit range and honest empty state. Nothing is estimated
from page views: study time comes from `learning_activities`, proficiency from
assessment evidence, and scores from completed attempts.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import local_today
from app.models.assessment import Assessment, AssessmentAttempt
from app.models.catalog import Skill, Subject
from app.models.enums import AttemptStatus, ProgressStatus
from app.models.learning import LearningActivity, LearningPath, LearningPathItem, LessonProgress
from app.models.user import User, UserSkill
from app.schemas.analytics import (
    ActivityPoint,
    AnalyticsResponse,
    AnalyticsTotals,
    AssessmentPoint,
    StudyKind,
    SubjectInsight,
    WeakSkill,
)
from app.services.achievements import current_streak_days

RANGE_DAYS = 30
WEAK_SKILL_THRESHOLD = 60


async def build_analytics(session: AsyncSession, user: User) -> AnalyticsResponse:
    timezone_name = user.profile.timezone if user.profile else "UTC"
    today = local_today(timezone_name)
    start = today - timedelta(days=RANGE_DAYS - 1)

    day_rows = (
        await session.execute(
            select(
                LearningActivity.occurred_on,
                func.coalesce(func.sum(LearningActivity.minutes), 0),
                func.coalesce(func.sum(LearningActivity.xp_awarded), 0),
            )
            .where(
                LearningActivity.user_id == user.id,
                LearningActivity.occurred_on >= start,
            )
            .group_by(LearningActivity.occurred_on)
        )
    ).all()
    per_day = {day: (int(minutes), int(xp)) for day, minutes, xp in day_rows}

    activity = [
        ActivityPoint(
            day=start + timedelta(days=offset),
            minutes=per_day.get(start + timedelta(days=offset), (0, 0))[0],
            xp=per_day.get(start + timedelta(days=offset), (0, 0))[1],
        )
        for offset in range(RANGE_DAYS)
    ]
    range_minutes = sum(point.minutes for point in activity)
    range_xp = sum(point.xp for point in activity)

    study_by_kind = [
        StudyKind(kind=kind, minutes=int(minutes))
        for kind, minutes in (
            await session.execute(
                select(
                    LearningActivity.kind,
                    func.coalesce(func.sum(LearningActivity.minutes), 0),
                )
                .where(
                    LearningActivity.user_id == user.id,
                    LearningActivity.occurred_on >= start,
                )
                .group_by(LearningActivity.kind)
                .order_by(desc(func.coalesce(func.sum(LearningActivity.minutes), 0)))
            )
        ).all()
    ]

    skill_rows = (
        await session.execute(
            select(
                Subject.id,
                Subject.name,
                Subject.accent,
                func.avg(UserSkill.proficiency),
                func.count(UserSkill.id),
            )
            .join(Skill, Skill.subject_id == Subject.id)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user.id)
            .group_by(Subject.id)
        )
    ).all()
    subject_minutes = {
        subject_id: int(minutes)
        for subject_id, minutes in (
            await session.execute(
                select(
                    LearningActivity.subject_id,
                    func.coalesce(func.sum(LearningActivity.minutes), 0),
                )
                .where(
                    LearningActivity.user_id == user.id,
                    LearningActivity.occurred_on >= start,
                    LearningActivity.subject_id.is_not(None),
                )
                .group_by(LearningActivity.subject_id)
            )
        ).all()
    }
    subjects = sorted(
        [
            SubjectInsight(
                subject_id=subject_id,
                subject_name=name,
                accent=accent,
                average_proficiency=round(float(average or 0)),
                skills_tracked=int(tracked),
                minutes=subject_minutes.get(subject_id, 0),
            )
            for subject_id, name, accent, average, tracked in skill_rows
        ],
        key=lambda item: item.average_proficiency,
    )

    trend_rows = (
        await session.execute(
            select(
                AssessmentAttempt.id,
                Subject.name,
                AssessmentAttempt.score,
                AssessmentAttempt.completed_at,
            )
            .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
            .join(Subject, Subject.id == Assessment.subject_id)
            .where(
                AssessmentAttempt.user_id == user.id,
                AssessmentAttempt.status == AttemptStatus.COMPLETED.value,
                AssessmentAttempt.completed_at.is_not(None),
            )
            .order_by(desc(AssessmentAttempt.completed_at))
            .limit(10)
        )
    ).all()
    assessment_trend = [
        AssessmentPoint(
            attempt_id=attempt_id,
            subject_name=subject_name,
            score_percent=float(score or 0),
            completed_at=completed_at,
        )
        for attempt_id, subject_name, score, completed_at in reversed(trend_rows)
    ]

    weak_skills = [
        WeakSkill(
            skill_id=skill_id,
            name=name,
            subject_name=subject_name,
            proficiency=int(proficiency),
            confidence=int(confidence),
        )
        for skill_id, name, subject_name, proficiency, confidence in (
            await session.execute(
                select(
                    Skill.id,
                    Skill.name,
                    Subject.name,
                    UserSkill.proficiency,
                    UserSkill.confidence,
                )
                .join(UserSkill, UserSkill.skill_id == Skill.id)
                .join(Subject, Subject.id == Skill.subject_id)
                .where(
                    UserSkill.user_id == user.id,
                    UserSkill.proficiency < WEAK_SKILL_THRESHOLD,
                )
                .order_by(UserSkill.proficiency, desc(UserSkill.confidence))
                .limit(6)
            )
        ).all()
    ]

    assessments_completed = (
        await session.execute(
            select(func.count())
            .select_from(AssessmentAttempt)
            .where(
                AssessmentAttempt.user_id == user.id,
                AssessmentAttempt.status == AttemptStatus.COMPLETED.value,
            )
        )
    ).scalar_one()
    roadmap_items_completed = (
        await session.execute(
            select(func.count())
            .select_from(LearningPathItem)
            .join(LearningPath, LearningPath.id == LearningPathItem.path_id)
            .where(
                LearningPath.user_id == user.id,
                LearningPathItem.status == ProgressStatus.COMPLETED.value,
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

    suggestions = [
        (
            f"{skill.name} ({skill.subject_name}) is at {skill.proficiency}%. "
            f"Ask the tutor for a worked example, then retake the {skill.subject_name} diagnostic."
        )
        for skill in weak_skills[:3]
    ]
    if not suggestions and not subjects:
        suggestions = [
            "Take a diagnostic for one of your subjects. Every insight on this page is "
            "computed from assessment evidence and recorded study time."
        ]

    return AnalyticsResponse(
        range_days=RANGE_DAYS,
        totals=AnalyticsTotals(
            minutes=range_minutes,
            xp=range_xp,
            streak_days=await current_streak_days(session, user.id, today),
            assessments_completed=int(assessments_completed),
            roadmap_items_completed=int(roadmap_items_completed),
            lessons_completed=int(lessons_completed),
        ),
        activity=activity,
        study_by_kind=study_by_kind,
        subjects=subjects,
        assessment_trend=assessment_trend,
        weak_skills=weak_skills,
        revision_suggestions=suggestions,
    )
