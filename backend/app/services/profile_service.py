from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.db.base import utcnow
from app.models.catalog import Skill, Subject
from app.models.enums import (
    CareerGoal,
    EducationLevel,
    ExperienceLevel,
    LearningStyle,
)
from app.models.user import (
    LearningPreference,
    User,
    UserProfile,
    UserSkill,
    UserSubjectInterest,
)
from app.schemas.auth import MeResponse, OnboardingRequest, ProfileUpdateRequest, UserSkillRead
from app.services.gamification import proficiency_from_self_report


async def load_me(session: AsyncSession, user: User) -> MeResponse:
    await session.refresh(user)

    interests = (
        await session.execute(
            select(Subject)
            .join(UserSubjectInterest, UserSubjectInterest.subject_id == Subject.id)
            .where(UserSubjectInterest.user_id == user.id)
            .order_by(Subject.name)
        )
    ).scalars().all()

    skill_rows = (
        await session.execute(
            select(UserSkill, Skill)
            .join(Skill, Skill.id == UserSkill.skill_id)
            .where(UserSkill.user_id == user.id)
            .order_by(UserSkill.proficiency.desc(), Skill.name)
        )
    ).all()

    return MeResponse.model_validate(
        {
            "user": user,
            "interests": interests,
            "skills": [
                UserSkillRead(
                    skill_id=skill.id,
                    slug=skill.slug,
                    name=skill.name,
                    proficiency=us.proficiency,
                    confidence=us.confidence,
                    source=us.source,
                    last_assessed_at=us.last_assessed_at,
                )
                for us, skill in skill_rows
            ],
        }
    )


def _ensure_profile(user: User) -> UserProfile:
    if user.profile is None:
        user.profile = UserProfile(timezone="UTC")
    return user.profile


async def update_profile(session: AsyncSession, user: User, data: ProfileUpdateRequest) -> User:
    profile = _ensure_profile(user)
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.headline is not None:
        profile.headline = data.headline
    if data.bio is not None:
        profile.bio = data.bio
    if data.target_role is not None:
        profile.target_role = data.target_role
    if data.timezone is not None:
        profile.timezone = data.timezone
    if data.weekly_minutes_goal is not None:
        profile.weekly_minutes_goal = data.weekly_minutes_goal
    await session.commit()
    await session.refresh(user)
    return user


def _validate_enum(value: str, enum_type, label: str) -> str:  # type: ignore[no-untyped-def]
    try:
        return enum_type(value).value
    except ValueError as exc:
        raise AppError(
            "invalid_onboarding_value",
            f"{label} must be one of: {', '.join(item.value for item in enum_type)}.",
            422,
        ) from exc


async def complete_onboarding(session: AsyncSession, user: User, data: OnboardingRequest) -> None:
    education = _validate_enum(data.education_level, EducationLevel, "education_level")
    experience = _validate_enum(data.experience_level, ExperienceLevel, "experience_level")
    style = _validate_enum(data.learning_style, LearningStyle, "learning_style")
    career = _validate_enum(data.career_goal, CareerGoal, "career_goal")

    # Deduplicate while preserving the student's ordering.
    slugs = list(dict.fromkeys(slug.strip().lower() for slug in data.subject_slugs if slug.strip()))
    subjects = (
        await session.execute(select(Subject).where(Subject.slug.in_(slugs), Subject.is_active.is_(True)))
    ).scalars().all()
    found = {subject.slug for subject in subjects}
    missing = [slug for slug in slugs if slug not in found]
    if missing:
        raise AppError(
            "unknown_subject",
            "Some selected subjects are not available.",
            422,
            [{"field": "subject_slugs", "message": f"Unknown subject: {slug}"} for slug in missing],
        )

    profile = _ensure_profile(user)
    profile.education_level = education
    profile.experience_level = experience
    profile.career_goal = career
    profile.target_role = (data.target_role or "").strip() or None
    profile.weekly_minutes_goal = data.weekly_minutes_goal
    if data.timezone:
        profile.timezone = data.timezone
    profile.onboarding_completed_at = utcnow()
    profile.onboarding_step = 3

    if user.preferences is None:
        user.preferences = LearningPreference()
    user.preferences.learning_style = style
    user.preferences.session_minutes = data.session_minutes
    user.preferences.prefers_projects = data.prefers_projects
    user.preferences.prefers_theory_first = data.prefers_theory_first

    await session.execute(delete(UserSubjectInterest).where(UserSubjectInterest.user_id == user.id))
    session.add_all(
        [
            UserSubjectInterest(user_id=user.id, subject_id=subject.id)
            for subject in subjects
        ]
    )

    # Seed a low-confidence, self-reported proficiency for the chosen skills.
    existing_skill_ids = set(
        (await session.execute(select(UserSkill.skill_id).where(UserSkill.user_id == user.id)))
        .scalars()
        .all()
    )
    seeded = proficiency_from_self_report(experience)
    subject_ids = [subject.id for subject in subjects]
    skills = (
        await session.execute(select(Skill).where(Skill.subject_id.in_(subject_ids)))
    ).scalars().all()
    for skill in skills:
        if skill.id in existing_skill_ids:
            continue
        session.add(
            UserSkill(
                user_id=user.id,
                skill_id=skill.id,
                proficiency=seeded,
                confidence=10,
                source="self_report",
            )
        )

    await session.commit()
    await session.refresh(user)
