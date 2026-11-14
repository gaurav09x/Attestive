"""Assessment lifecycle: start, autosave, score, update proficiency, review.

Answer keys never leave the server before submission. Every attempt is scoped to
the authenticated student, and completed attempts are immutable evidence.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, not_found
from app.core.time import local_today, utc_now
from app.models.assessment import (
    Assessment,
    AssessmentAttempt,
    AssessmentResponse,
    Question,
)
from app.models.catalog import Skill, Subject
from app.models.enums import AttemptStatus
from app.models.gamification import LearningRecommendation
from app.models.learning import LearningPath
from app.models.user import User, UserSkill
from app.schemas.assessment import (
    AssessmentOverview,
    AssessmentSubjectSummary,
    AttemptQuestion,
    AttemptRead,
    AttemptResult,
    AttemptReview,
    ReviewQuestion,
    SkillResult,
    SubmitRequest,
)
from app.services import proficiency_service, roadmap_service
from app.services.achievements import evaluate_achievements
from app.services.gamification import award_xp, record_activity

logger = logging.getLogger(__name__)

BASE_ASSESSMENT_XP = 80
EXCELLENT_ASSESSMENT_XP = 40
EXCELLENCE_THRESHOLD = 0.8


def _normalise_text(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def get_overview(session: AsyncSession, user: User) -> AssessmentOverview:
    from app.models.user import UserSubjectInterest

    interest_ids = (
        await session.execute(
            select(UserSubjectInterest.subject_id).where(UserSubjectInterest.user_id == user.id)
        )
    ).scalars().all()

    subject_stmt = select(Subject).where(Subject.is_active.is_(True))
    if interest_ids:
        subject_stmt = subject_stmt.where(Subject.id.in_(interest_ids))
    subjects = (await session.execute(subject_stmt.order_by(Subject.name))).scalars().all()

    summaries: list[AssessmentSubjectSummary] = []
    for subject in subjects:
        assessment = (
            await session.execute(
                select(Assessment)
                .where(
                    Assessment.subject_id == subject.id,
                    Assessment.kind == "diagnostic",
                    Assessment.is_active.is_(True),
                )
                .order_by(desc(Assessment.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()

        summary = AssessmentSubjectSummary(
            subject_id=subject.id,
            subject_slug=subject.slug,
            subject_name=subject.name,
            subject_description=subject.description,
            accent=subject.accent,
            assessment_id=assessment.id if assessment else None,
            title=assessment.title if assessment else None,
            estimated_minutes=assessment.estimated_minutes if assessment else None,
        )
        if assessment is not None:
            summary.question_count = (
                await session.execute(
                    select(func.count())
                    .select_from(Question)
                    .where(Question.assessment_id == assessment.id)
                )
            ).scalar_one()

            in_progress = (
                await session.execute(
                    select(AssessmentAttempt)
                    .where(
                        AssessmentAttempt.user_id == user.id,
                        AssessmentAttempt.assessment_id == assessment.id,
                        AssessmentAttempt.status == AttemptStatus.IN_PROGRESS.value,
                    )
                    .order_by(desc(AssessmentAttempt.started_at))
                    .limit(1)
                )
            ).scalar_one_or_none()
            if in_progress:
                summary.in_progress_attempt_id = in_progress.id

            completed = (
                await session.execute(
                    select(AssessmentAttempt)
                    .where(
                        AssessmentAttempt.user_id == user.id,
                        AssessmentAttempt.assessment_id == assessment.id,
                        AssessmentAttempt.status == AttemptStatus.COMPLETED.value,
                    )
                    .order_by(desc(AssessmentAttempt.completed_at))
                    .limit(1)
                )
            ).scalar_one_or_none()
            if completed:
                summary.last_attempt_id = completed.id
                summary.last_score = completed.score
                summary.last_completed_at = completed.completed_at

        summaries.append(summary)

    return AssessmentOverview(subjects=summaries)


async def _load_attempt(
    session: AsyncSession, user: User, attempt_id: uuid.UUID
) -> tuple[AssessmentAttempt, Assessment]:
    row = (
        await session.execute(
            select(AssessmentAttempt, Assessment)
            .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
            .where(AssessmentAttempt.id == attempt_id, AssessmentAttempt.user_id == user.id)
        )
    ).first()
    if row is None:
        raise not_found("Assessment attempt")
    return row[0], row[1]


async def _read_attempt(
    session: AsyncSession, user: User, attempt: AssessmentAttempt, assessment: Assessment
) -> AttemptRead:
    subject = await session.get(Subject, assessment.subject_id)
    questions = (
        await session.execute(
            select(Question)
            .where(Question.assessment_id == assessment.id)
            .order_by(Question.position)
        )
    ).scalars().all()
    responses = {
        row.question_id: row
        for row in (
            await session.execute(
                select(AssessmentResponse).where(AssessmentResponse.attempt_id == attempt.id)
            )
        ).scalars()
    }

    return AttemptRead(
        id=attempt.id,
        assessment_id=assessment.id,
        title=assessment.title,
        subject_name=subject.name if subject else "Subject",
        subject_slug=subject.slug if subject else "",
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        questions=[
            AttemptQuestion(
                id=question.id,
                kind=question.kind,
                prompt=question.prompt,
                options=question.options,
                position=question.position,
                difficulty=question.difficulty,
                saved_response=responses[question.id].response if question.id in responses else None,
            )
            for question in questions
        ],
        answered_count=sum(1 for question in questions if question.id in responses),
        total_questions=len(questions),
    )


async def start_attempt(
    session: AsyncSession, user: User, assessment_id: uuid.UUID
) -> AttemptRead:
    assessment = await session.get(Assessment, assessment_id)
    if assessment is None or not assessment.is_active:
        raise not_found("Assessment")

    existing = (
        await session.execute(
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.user_id == user.id,
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.status == AttemptStatus.IN_PROGRESS.value,
            )
            .order_by(desc(AssessmentAttempt.started_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = AssessmentAttempt(
            user_id=user.id,
            assessment_id=assessment.id,
            status=AttemptStatus.IN_PROGRESS.value,
            started_at=utc_now(),
        )
        session.add(existing)
        await session.commit()
        await session.refresh(existing)

    return await _read_attempt(session, user, existing, assessment)


async def get_attempt(
    session: AsyncSession, user: User, attempt_id: uuid.UUID
) -> AttemptRead:
    attempt, assessment = await _load_attempt(session, user, attempt_id)
    return await _read_attempt(session, user, attempt, assessment)


def _normalise_response(question: Question, payload: dict) -> dict:
    if question.kind == "multiple_choice":
        index = payload.get("index")
        options = question.options or []
        if not isinstance(index, int) or isinstance(index, bool):
            raise AppError("invalid_response", "Select one of the available options.", 422)
        if not 0 <= index < len(options):
            raise AppError("invalid_response", "Select one of the available options.", 422)
        return {"index": index}

    text = payload.get("text", "")
    if not isinstance(text, str):
        raise AppError("invalid_response", "Answer must be text.", 422)
    cleaned = text.strip()
    if not cleaned:
        raise AppError("invalid_response", "Answer cannot be empty.", 422)
    if len(cleaned) > 4000:
        raise AppError("invalid_response", "Answer must be under 4000 characters.", 422)
    return {"text": cleaned}


async def save_response(
    session: AsyncSession,
    user: User,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: dict,
) -> None:
    attempt, assessment = await _load_attempt(session, user, attempt_id)
    if attempt.status != AttemptStatus.IN_PROGRESS.value:
        raise AppError("attempt_completed", "This attempt has already been submitted.", 409)

    question = await session.get(Question, question_id)
    if question is None or question.assessment_id != assessment.id:
        raise not_found("Question")

    normalised = _normalise_response(question, payload)
    existing = (
        await session.execute(
            select(AssessmentResponse).where(
                AssessmentResponse.attempt_id == attempt.id,
                AssessmentResponse.question_id == question.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.response = normalised
        existing.evaluated_at = None
        existing.score = None
        existing.is_correct = None
    else:
        session.add(
            AssessmentResponse(
                attempt_id=attempt.id,
                question_id=question.id,
                response=normalised,
            )
        )
    await session.commit()


def _score_question(question: Question, response: dict) -> tuple[float | None, bool | None, str | None]:
    """Return (score 0..1, correct, feedback). None means 'not auto-gradable'."""
    key = question.correct_answer or {}

    if question.kind == "multiple_choice":
        chosen = response.get("index") if isinstance(response, dict) else None
        expected = key.get("index")
        if not isinstance(chosen, int):
            return 0.0, False, "No option was selected."
        is_correct = chosen == expected
        return (1.0 if is_correct else 0.0), is_correct, None

    if question.kind == "coding":
        return None, None, "Coding questions are graded in the Coding Lab (Phase 4)."

    text = response.get("text", "") if isinstance(response, dict) else ""
    normalised = _normalise_text(str(text))
    if not normalised:
        return 0.0, False, "Answer was empty."

    if question.kind == "short_answer":
        accepted = [ _normalise_text(item) for item in key.get("accepted", []) if item]
        if normalised in accepted:
            return 1.0, True, None
        keywords = [_normalise_text(item) for item in key.get("keywords", []) if item]
        if keywords:
            hits = sum(1 for keyword in keywords if keyword and keyword in normalised)
            ratio = hits / len(keywords)
            if ratio >= 0.999:
                return 1.0, True, None
            if ratio > 0:
                return 0.5, False, "Part of the idea is there, but a key term is missing."
        return 0.0, False, "The answer did not match the expected concept."

    if question.kind == "conceptual":
        key_points = key.get("key_points", [])
        if not key_points:
            return None, None, "This question has no grading rubric."
        covered = 0.0
        for point in key_points:
            words = [word for word in _normalise_text(point).split() if len(word) >= 4]
            if not words:
                continue
            if all(word in normalised for word in words):
                covered += 1
            elif any(word in normalised for word in words):
                covered += 0.5
        ratio = min(1.0, covered / len(key_points))
        feedback = f"Covered {covered:g} of {len(key_points)} expected ideas."
        return ratio, ratio >= 0.6, feedback

    return None, None, None


def _answer_text(question: Question) -> str | None:
    key = question.correct_answer or {}
    if question.kind == "multiple_choice":
        options = question.options or []
        index = key.get("index")
        if isinstance(index, int) and 0 <= index < len(options):
            return options[index]
        return None
    if question.kind == "short_answer":
        accepted = key.get("accepted") or []
        return accepted[0] if accepted else None
    if question.kind == "conceptual":
        return key.get("sample_answer") or "; ".join(key.get("key_points") or []) or None
    return None


async def _upsert_response(
    session: AsyncSession,
    attempt_id: uuid.UUID,
    question: Question,
    payload: dict,
) -> AssessmentResponse:
    normalised = _normalise_response(question, payload)
    existing = (
        await session.execute(
            select(AssessmentResponse).where(
                AssessmentResponse.attempt_id == attempt_id,
                AssessmentResponse.question_id == question.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.response = normalised
        return existing
    created = AssessmentResponse(
        attempt_id=attempt_id, question_id=question.id, response=normalised
    )
    session.add(created)
    await session.flush()
    return created


async def submit_attempt(
    session: AsyncSession,
    user: User,
    attempt_id: uuid.UUID,
    payload: SubmitRequest,
) -> AttemptResult:
    attempt, assessment = await _load_attempt(session, user, attempt_id)
    if attempt.status == AttemptStatus.COMPLETED.value:
        raise AppError("attempt_completed", "This attempt has already been submitted.", 409)

    questions = list(
        (
            await session.execute(
                select(Question)
                .where(Question.assessment_id == assessment.id)
                .order_by(Question.position)
            )
        ).scalars()
    )
    if not questions:
        raise AppError("empty_assessment", "This assessment has no questions yet.", 409)

    question_by_id = {question.id: question for question in questions}

    if payload.responses:
        for item in payload.responses:
            question = question_by_id.get(item.question_id)
            if question is None:
                raise AppError(
                    "unknown_question",
                    "A submitted answer does not belong to this assessment.",
                    422,
                )
            await _upsert_response(session, attempt.id, question, item.response)
        await session.flush()

    responses = {
        row.question_id: row
        for row in (
            await session.execute(
                select(AssessmentResponse).where(AssessmentResponse.attempt_id == attempt.id)
            )
        ).scalars()
    }
    missing = [question for question in questions if question.id not in responses]
    if missing:
        raise AppError(
            "unanswered_questions",
            "Answer every question before submitting.",
            422,
            [
                {
                    "field": "responses",
                    "message": f"{len(missing)} question(s) still unanswered.",
                }
            ],
        )

    now = utc_now()
    weighted_total = 0.0
    total_weight = 0.0
    correct_count = 0
    partial_count = 0
    evidences: list[proficiency_service.SkillEvidence] = []
    skill_meta: dict[uuid.UUID, Skill] = {}

    skill_ids = {question.skill_id for question in questions if question.skill_id}
    if skill_ids:
        for skill in (
            await session.execute(select(Skill).where(Skill.id.in_(skill_ids)))
        ).scalars():
            skill_meta[skill.id] = skill

    for question in questions:
        response = responses[question.id]
        score, is_correct, feedback = _score_question(question, response.response or {})
        response.score = score
        response.is_correct = is_correct
        response.feedback = feedback
        response.evaluated_at = now

        if score is None:
            continue
        total_weight += question.difficulty
        weighted_total += score * question.difficulty
        if score >= 0.999:
            correct_count += 1
        elif score > 0:
            partial_count += 1

        if question.skill_id and question.skill_id in skill_meta:
            skill = skill_meta[question.skill_id]
            evidences.append(
                proficiency_service.SkillEvidence(
                    skill_id=skill.id,
                    skill_slug=skill.slug,
                    skill_name=skill.name,
                    score=score,
                    difficulty=question.difficulty,
                )
            )

    average = weighted_total / total_weight if total_weight else 0.0
    skill_updates = await proficiency_service.apply_evidence(session, user.id, evidences)
    weak = [update for update in skill_updates if update.score < 60]

    attempt.status = AttemptStatus.COMPLETED.value
    attempt.score = round(average * 100, 2)
    attempt.proficiency_estimate = round(average * 100, 2)
    attempt.weak_skills = [update.name for update in weak]
    attempt.completed_at = now

    xp_amount = BASE_ASSESSMENT_XP + (
        EXCELLENT_ASSESSMENT_XP if average >= EXCELLENCE_THRESHOLD else 0
    )
    xp_awarded = await award_xp(
        session,
        user,
        xp_amount,
        "assessment_completed",
        "assessment_attempt",
        attempt.id,
    )

    elapsed_minutes = max(
        1,
        min(120, round((now - _as_utc(attempt.started_at)).total_seconds() / 60)),
    )
    subject = await session.get(Subject, assessment.subject_id)
    record_activity(
        session,
        user_id=user.id,
        kind="assessment",
        minutes=elapsed_minutes,
        xp_awarded=xp_awarded,
        subject_id=assessment.subject_id,
        day=local_today(user.profile.timezone if user.profile else None),
    )

    roadmap = None
    if subject is not None:
        try:
            roadmap = await roadmap_service.generate_roadmap(
                session,
                user,
                subject,
                skill_updates=skill_updates,
                average_score=average,
            )
            existing_recommendation = (
                await session.execute(
                    select(LearningRecommendation.id).where(
                        LearningRecommendation.user_id == user.id,
                        LearningRecommendation.target_url == f"/roadmap?subject={subject.slug}",
                        LearningRecommendation.is_dismissed.is_(False),
                    )
                )
            ).first()
            if existing_recommendation is None:
                session.add(
                    LearningRecommendation(
                        user_id=user.id,
                        kind="roadmap",
                        title=f"Start your {subject.name} roadmap",
                        description=(
                            "Your diagnostic is scored. The plan prioritises the skills that need work first."
                        ),
                        reason="Generated from your latest diagnostic results.",
                        target_url=f"/roadmap?subject={subject.slug}",
                        priority=10,
                    )
                )
        except AppError:
            logger.exception("Could not generate a roadmap after attempt %s", attempt.id)

    unlocked = await evaluate_achievements(session, user)

    await session.commit()

    return AttemptResult(
        attempt_id=attempt.id,
        score_percent=round(average * 100),
        correct_count=correct_count,
        partial_count=partial_count,
        total_questions=len(questions),
        proficiency_estimate=round(average * 100),
        weak_skills=[update.name for update in weak],
        skill_results=[
            SkillResult(
                skill_id=update.skill_id,
                slug=update.slug,
                name=update.name,
                score=update.score,
                proficiency=update.proficiency,
                confidence=update.confidence,
            )
            for update in skill_updates
        ],
        roadmap_id=roadmap.id if roadmap else None,
        xp_awarded=xp_awarded,
        generated_by=roadmap.generated_by if roadmap else None,
        achievements_unlocked=unlocked,
    )


async def get_review(
    session: AsyncSession, user: User, attempt_id: uuid.UUID
) -> AttemptReview:
    attempt, assessment = await _load_attempt(session, user, attempt_id)
    if attempt.status != AttemptStatus.COMPLETED.value:
        raise AppError("attempt_in_progress", "Submit this attempt before reviewing it.", 409)

    subject = await session.get(Subject, assessment.subject_id)
    questions = list(
        (
            await session.execute(
                select(Question)
                .where(Question.assessment_id == assessment.id)
                .order_by(Question.position)
            )
        ).scalars()
    )
    responses = {
        row.question_id: row
        for row in (
            await session.execute(
                select(AssessmentResponse).where(AssessmentResponse.attempt_id == attempt.id)
            )
        ).scalars()
    }
    skills = {
        skill.id: skill
        for skill in (
            await session.execute(
                select(Skill).where(
                    Skill.id.in_([q.skill_id for q in questions if q.skill_id])
                )
            )
        ).scalars()
    }

    roadmap = (
        await session.execute(
            select(LearningPath.id)
            .where(
                LearningPath.user_id == user.id,
                LearningPath.subject_id == assessment.subject_id,
                LearningPath.status.in_(["active", "completed"]),
            )
            .order_by(desc(LearningPath.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    per_skill: dict[uuid.UUID, list[float]] = {}
    for question in questions:
        response = responses.get(question.id)
        if question.skill_id and response is not None and response.score is not None:
            per_skill.setdefault(question.skill_id, []).append(response.score)

    user_skills = {
        row.skill_id: row
        for row in (
            await session.execute(
                select(UserSkill).where(
                    UserSkill.user_id == user.id,
                    UserSkill.skill_id.in_(list(per_skill.keys())),
                )
            )
        ).scalars()
    }
    skill_results = sorted(
        [
            SkillResult(
                skill_id=skill_id,
                slug=skills[skill_id].slug,
                name=skills[skill_id].name,
                score=round(sum(scores) / len(scores) * 100),
                proficiency=user_skills[skill_id].proficiency if skill_id in user_skills else 0,
                confidence=user_skills[skill_id].confidence if skill_id in user_skills else 0,
            )
            for skill_id, scores in per_skill.items()
            if skill_id in skills
        ],
        key=lambda item: item.score,
    )

    return AttemptReview(
        attempt_id=attempt.id,
        title=assessment.title,
        subject_name=subject.name if subject else "Subject",
        subject_slug=subject.slug if subject else "",
        score_percent=attempt.score,
        proficiency_estimate=attempt.proficiency_estimate,
        weak_skills=attempt.weak_skills or [],
        completed_at=attempt.completed_at,
        roadmap_id=roadmap,
        skills=skill_results,
        questions=[
            ReviewQuestion(
                id=question.id,
                prompt=question.prompt,
                kind=question.kind,
                options=question.options,
                response=responses[question.id].response if question.id in responses else None,
                correct_answer=_answer_text(question),
                is_correct=responses[question.id].is_correct if question.id in responses else None,
                score=responses[question.id].score if question.id in responses else None,
                feedback=responses[question.id].feedback if question.id in responses else None,
                explanation=question.explanation,
                skill_name=(
                    skills[question.skill_id].name
                    if question.skill_id and question.skill_id in skills
                    else None
                ),
            )
            for question in questions
        ],
    )
