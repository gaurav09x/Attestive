"""Career development: role gap analysis, mock interviews and resume claims.

Readiness is computed only from measured skill evidence (`user_skills`). A resume
claim never raises a score; it is linked to evidence when one exists and is
labelled unverified otherwise. Interview answers are scored against the seeded
rubric and every point awarded or missed is stored with the response.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.career_agent import (
    DISCLAIMER,
    build_portfolio_briefs,
    build_recommendations,
    interview_feedback,
    readiness_label,
)
from app.core.errors import AppError, not_found
from app.core.time import local_today, utc_now
from app.models.career import (
    CareerRole,
    InterviewQuestion,
    InterviewResponse,
    MockInterview,
    ResumeSkill,
)
from app.models.catalog import Skill, Subject
from app.models.user import User, UserSkill
from app.schemas.career import (
    CareerRecommendation,
    CareerRoleDetail,
    CareerRoleListResponse,
    CareerRoleSummary,
    InterviewQuestionRead,
    MockInterviewDetail,
    MockInterviewListResponse,
    MockInterviewSummary,
    PortfolioBrief,
    ResumeSkillListResponse,
    ResumeSkillRead,
    ResumeSkillRequest,
    RoleSkillRead,
    StartInterviewRequest,
    SubmitAnswerRequest,
)
from app.services.achievements import evaluate_achievements
from app.services.gamification import award_xp, record_activity, xp_for_action

MAX_INTERVIEW_QUESTIONS = 5
CLOSE_GAP = 15
MIN_ANSWER_LENGTH = 20
READINESS_THRESHOLDS = {"interview_ready": 75, "developing": 50}


async def _load_role(session: AsyncSession, slug: str) -> CareerRole:
    role = (
        await session.execute(
            select(CareerRole).where(CareerRole.slug == slug, CareerRole.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if role is None:
        raise not_found("Career role")
    return role


async def _skill_index(
    session: AsyncSession,
) -> dict[tuple[str, str], tuple[Skill, Subject]]:
    rows = (
        await session.execute(
            select(Skill, Subject).join(Subject, Subject.id == Skill.subject_id)
        )
    ).all()
    return {(subject.slug, skill.slug): (skill, subject) for skill, subject in rows}


async def _proficiency(session: AsyncSession, user_id: uuid.UUID) -> dict[uuid.UUID, UserSkill]:
    rows = (
        await session.execute(select(UserSkill).where(UserSkill.user_id == user_id))
    ).scalars().all()
    return {row.skill_id: row for row in rows}


def _gap_rows(
    role: CareerRole,
    index: dict[tuple[str, str], tuple[Skill, Subject]],
    proficiency: dict[uuid.UUID, UserSkill],
) -> list[RoleSkillRead]:
    rows: list[RoleSkillRead] = []
    for requirement in role.skills or []:
        key = (requirement.get("subject_slug", ""), requirement.get("skill_slug", ""))
        found = index.get(key)
        if found is None:
            # Seeding validates references, so this only happens if a skill was
            # removed later. Skip rather than inventing a requirement.
            continue
        skill, subject = found
        evidence = proficiency.get(skill.id)
        current = int(evidence.proficiency) if evidence else 0
        confidence = int(evidence.confidence) if evidence else 0
        target = int(requirement.get("target", 60))
        gap = max(0, target - current)
        if current >= target:
            status = "met"
        elif gap <= CLOSE_GAP:
            status = "close"
        else:
            status = "missing"
        rows.append(
            RoleSkillRead(
                skill_id=skill.id,
                skill_slug=skill.slug,
                name=skill.name,
                subject_name=subject.name,
                target=target,
                importance=int(requirement.get("importance", 2)),
                proficiency=current,
                confidence=confidence,
                gap=gap,
                status=status,
                evidence_source=evidence.source if evidence else "no_evidence",
            )
        )
    return rows


def _readiness(rows: list[RoleSkillRead]) -> int:
    if not rows:
        return 0
    weighted = 0.0
    total = 0.0
    for row in rows:
        weight = max(1, row.importance)
        total += weight
        if row.target <= 0:
            weighted += weight
            continue
        weighted += weight * min(1.0, row.proficiency / row.target)
    return round(weighted / total * 100) if total else 0


def _summary(role: CareerRole, rows: list[RoleSkillRead]) -> CareerRoleSummary:
    score = _readiness(rows)
    return CareerRoleSummary(
        id=role.id,
        slug=role.slug,
        title=role.title,
        summary=role.summary,
        level=role.level,
        version=role.version,
        skill_count=len(rows),
        met_count=sum(1 for row in rows if row.status == "met"),
        readiness_score=score,
        readiness_label=readiness_label(score),
    )


async def list_roles(session: AsyncSession, user: User) -> CareerRoleListResponse:
    roles = (
        await session.execute(
            select(CareerRole).where(CareerRole.is_active.is_(True)).order_by(CareerRole.title)
        )
    ).scalars().all()
    index = await _skill_index(session)
    proficiency = await _proficiency(session, user.id)
    items = [_summary(role, _gap_rows(role, index, proficiency)) for role in roles]
    items.sort(key=lambda item: item.readiness_score, reverse=True)
    return CareerRoleListResponse(items=items, disclaimer=DISCLAIMER)


async def role_detail(session: AsyncSession, user: User, slug: str) -> CareerRoleDetail:
    role = await _load_role(session, slug)
    index = await _skill_index(session)
    rows = _gap_rows(role, index, await _proficiency(session, user.id))
    summary = _summary(role, rows)

    recommendations: list[CareerRecommendation] = build_recommendations(role.title, rows)
    briefs: list[PortfolioBrief] = build_portfolio_briefs(
        {
            "portfolio_briefs": role.portfolio_briefs,
        },
        rows,
    )
    strengths = [row.name for row in rows if row.status == "met"][:6]
    priorities = [
        row.name
        for row in sorted(rows, key=lambda row: (-row.importance, -row.gap))
        if row.status != "met"
    ][:6]

    return CareerRoleDetail(
        **summary.model_dump(),
        skills=rows,
        recommendations=recommendations,
        portfolio_briefs=briefs,
        strengths=strengths,
        priorities=priorities,
        generated_by="deterministic",
        disclaimer=DISCLAIMER,
    )


async def _questions_for_role(
    session: AsyncSession, role_id: uuid.UUID
) -> list[InterviewQuestion]:
    return list(
        (
            await session.execute(
                select(InterviewQuestion)
                .where(InterviewQuestion.role_id == role_id)
                .order_by(InterviewQuestion.position)
                .limit(MAX_INTERVIEW_QUESTIONS)
            )
        ).scalars()
    )


def _score_answer(rubric: list[dict], answer: str) -> tuple[float, list[str], str]:
    text = answer.lower()
    points = [point for point in rubric or [] if isinstance(point, dict)]
    if not points:
        return 0.0, [], "This question has no rubric, so no score could be awarded."

    matched: list[str] = []
    missed: list[str] = []
    for point in points:
        keywords = [str(keyword).lower() for keyword in point.get("keywords", [])]
        label = str(point.get("point", "Required point"))
        if any(keyword and keyword in text for keyword in keywords):
            matched.append(label)
        else:
            missed.append(label)

    score = round(len(matched) / len(points) * 100, 1)
    if len(answer.strip()) < MIN_ANSWER_LENGTH:
        score = 0.0
        return (
            score,
            [],
            "The answer was too short to assess. Describe the situation, your reasoning and the "
            "trade-off you chose.",
        )

    parts: list[str] = []
    if matched:
        parts.append("Covered: " + "; ".join(matched) + ".")
    if missed:
        parts.append("Not covered: " + "; ".join(missed) + ".")
    return score, matched, " ".join(parts) or "No rubric points were detected."


async def _owned_interview(
    session: AsyncSession, user: User, interview_id: uuid.UUID
) -> MockInterview:
    interview = (
        await session.execute(
            select(MockInterview)
            .options(selectinload(MockInterview.responses))
            .where(MockInterview.id == interview_id, MockInterview.user_id == user.id)
        )
    ).scalar_one_or_none()
    if interview is None:
        raise not_found("Interview")
    return interview


async def _interview_detail(
    session: AsyncSession, interview: MockInterview
) -> MockInterviewDetail:
    role = await session.get(CareerRole, interview.role_id)
    questions = await _questions_for_role(session, interview.role_id)
    responses = {response.question_id: response for response in interview.responses}
    skill_names = {
        skill.id: skill.name
        for skill in (
            await session.execute(
                select(Skill).where(
                    Skill.id.in_([question.skill_id for question in questions if question.skill_id])
                )
            )
        ).scalars().all()
    }

    items: list[InterviewQuestionRead] = []
    for question in questions:
        response = responses.get(question.id)
        items.append(
            InterviewQuestionRead(
                id=question.id,
                kind=question.kind,
                prompt=question.prompt,
                difficulty=question.difficulty,
                position=question.position,
                skill_name=skill_names.get(question.skill_id) if question.skill_id else None,
                answer=response.answer if response else None,
                score=response.score if response else None,
                matched_points=list(response.matched_points or []) if response else [],
                feedback=response.feedback if response else None,
                # Model answers are teaching material: they appear only after the
                # interview is completed so they cannot be copied mid-session.
                model_answer=question.model_answer if interview.status == "completed" else None,
            )
        )

    return MockInterviewDetail(
        id=interview.id,
        role_slug=role.slug if role else "unknown",
        role_title=role.title if role else "Unknown role",
        status=interview.status,
        overall_score=interview.overall_score,
        readiness=interview.readiness,
        feedback=list(interview.feedback or []),
        started_at=interview.started_at,
        completed_at=interview.completed_at,
        answered=len(responses),
        total=len(questions),
        questions=items,
        disclaimer=DISCLAIMER,
    )


async def start_interview(
    session: AsyncSession, user: User, payload: StartInterviewRequest
) -> MockInterviewDetail:
    role = await _load_role(session, payload.role_slug)
    questions = await _questions_for_role(session, role.id)
    if not questions:
        raise AppError(
            "no_interview_questions",
            "This role has no interview questions yet. Choose another role.",
            409,
        )

    # One resumable interview per role: restarting must not create a second
    # in-progress transcript that could both award XP.
    existing = (
        await session.execute(
            select(MockInterview)
            .options(selectinload(MockInterview.responses))
            .where(
                MockInterview.user_id == user.id,
                MockInterview.role_id == role.id,
                MockInterview.status == "in_progress",
            )
            .order_by(desc(MockInterview.started_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return await _interview_detail(session, existing)

    now = utc_now()
    interview = MockInterview(
        user_id=user.id,
        role_id=role.id,
        status="in_progress",
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(interview)
    await session.commit()
    # Re-load with `responses` eagerly: a freshly created instance has no loaded
    # collection, and touching it lazily in async context raises MissingGreenlet.
    interview = await _owned_interview(session, user, interview.id)
    return await _interview_detail(session, interview)


async def list_interviews(
    session: AsyncSession, user: User
) -> MockInterviewListResponse:
    rows = (
        await session.execute(
            select(MockInterview, CareerRole)
            .join(CareerRole, CareerRole.id == MockInterview.role_id)
            .where(MockInterview.user_id == user.id)
            .order_by(desc(MockInterview.started_at))
            .limit(20)
        )
    ).all()
    items: list[MockInterviewSummary] = []
    for interview, role in rows:
        total = len(await _questions_for_role(session, interview.role_id))
        answered = (
            await session.execute(
                select(InterviewResponse.id).where(
                    InterviewResponse.interview_id == interview.id
                )
            )
        ).all()
        items.append(
            MockInterviewSummary(
                id=interview.id,
                role_slug=role.slug,
                role_title=role.title,
                status=interview.status,
                overall_score=interview.overall_score,
                readiness=interview.readiness,
                feedback=list(interview.feedback or []),
                started_at=interview.started_at,
                completed_at=interview.completed_at,
                answered=len(answered),
                total=total,
            )
        )
    return MockInterviewListResponse(items=items)


async def get_interview(
    session: AsyncSession, user: User, interview_id: uuid.UUID
) -> MockInterviewDetail:
    interview = await _owned_interview(session, user, interview_id)
    return await _interview_detail(session, interview)


async def submit_answer(
    session: AsyncSession,
    user: User,
    interview_id: uuid.UUID,
    payload: SubmitAnswerRequest,
) -> MockInterviewDetail:
    interview = await _owned_interview(session, user, interview_id)
    if interview.status != "in_progress":
        raise AppError(
            "interview_completed",
            "This interview is already completed. Start a new one to practise again.",
            409,
        )

    question = await session.get(InterviewQuestion, payload.question_id)
    if question is None or question.role_id != interview.role_id:
        raise not_found("Interview question")

    answer = payload.answer.strip()
    score, matched, feedback = _score_answer(question.rubric, answer)

    response = next(
        (item for item in interview.responses if item.question_id == question.id), None
    )
    if response is None:
        response = InterviewResponse(
            interview_id=interview.id,
            question_id=question.id,
            answer=answer,
            score=score,
            matched_points=matched,
            feedback=feedback,
        )
        session.add(response)
        interview.responses.append(response)
    else:
        response.answer = answer
        response.score = score
        response.matched_points = matched
        response.feedback = feedback
        response.evaluated_at = utc_now()

    interview.updated_at = utc_now()
    await session.commit()
    return await _interview_detail(session, interview)


async def complete_interview(
    session: AsyncSession, user: User, interview_id: uuid.UUID
) -> MockInterviewDetail:
    interview = await _owned_interview(session, user, interview_id)
    if interview.status == "completed":
        return await _interview_detail(session, interview)

    questions = await _questions_for_role(session, interview.role_id)
    answered = {response.question_id for response in interview.responses}
    missing = [question.id for question in questions if question.id not in answered]
    if missing:
        raise AppError(
            "interview_incomplete",
            f"Answer every question before finishing ({len(missing)} remaining).",
            400,
        )

    scores = [float(response.score) for response in interview.responses]
    overall = round(sum(scores) / len(scores), 1) if scores else 0.0
    readiness = readiness_label(int(overall))

    weakest = sorted(
        zip(questions, interview.responses),
        key=lambda pair: pair[1].score,
    )
    weakest_labels: list[str] = []
    for question, _ in weakest[:3]:
        if question.skill_id is None:
            continue
        skill = await session.get(Skill, question.skill_id)
        if skill is not None:
            weakest_labels.append(skill.name)

    interview.overall_score = overall
    interview.readiness = readiness
    interview.feedback = interview_feedback(scores, readiness, weakest_labels)
    interview.status = "completed"
    interview.completed_at = utc_now()
    interview.updated_at = interview.completed_at

    xp_awarded = await award_xp(
        session,
        user,
        xp_for_action("mock_interview_completed"),
        "mock_interview_completed",
        "mock_interview",
        interview.id,
    )
    # Practice is a study event with no measured duration: the streak counts, the
    # study-time total is not inflated.
    record_activity(
        session,
        user_id=user.id,
        kind="review",
        minutes=0,
        xp_awarded=xp_awarded,
        day=local_today(user.profile.timezone if user.profile else None),
    )
    await evaluate_achievements(session, user)
    await session.commit()
    return await _interview_detail(session, interview)


def _resume_read(
    claim: ResumeSkill,
    skill: Skill | None,
    subject: Subject | None,
    evidence: UserSkill | None,
) -> ResumeSkillRead:
    verified = bool(
        evidence
        and evidence.source != "self_report"
        and evidence.confidence >= 40
    )
    if evidence is None:
        proof = "No measured evidence yet — this claim is unverified."
    elif verified:
        proof = (
            f"Backed by a {evidence.proficiency}% estimate from {evidence.source} "
            f"evidence ({evidence.confidence}% confidence)."
        )
    else:
        proof = (
            f"Only a {evidence.proficiency}% self-reported estimate exists "
            f"({evidence.confidence}% confidence) — treat as unverified."
        )
    return ResumeSkillRead(
        id=claim.id,
        label=claim.label,
        claimed_level=claim.claimed_level,
        skill_id=skill.id if skill else None,
        skill_slug=skill.slug if skill else None,
        skill_name=skill.name if skill else None,
        subject_name=subject.name if subject else None,
        measured_proficiency=evidence.proficiency if evidence else None,
        verified=verified,
        evidence=proof,
    )


async def list_resume_skills(
    session: AsyncSession, user: User
) -> ResumeSkillListResponse:
    claims = (
        await session.execute(
            select(ResumeSkill)
            .where(ResumeSkill.user_id == user.id)
            .order_by(desc(ResumeSkill.created_at))
        )
    ).scalars().all()

    items: list[ResumeSkillRead] = []
    for claim in claims:
        skill = await session.get(Skill, claim.skill_id) if claim.skill_id else None
        subject = await session.get(Subject, skill.subject_id) if skill else None
        evidence = (
            await session.execute(
                select(UserSkill).where(
                    UserSkill.user_id == user.id, UserSkill.skill_id == claim.skill_id
                )
            )
        ).scalar_one_or_none() if claim.skill_id else None
        items.append(_resume_read(claim, skill, subject, evidence))
    return ResumeSkillListResponse(items=items)


def _normalise(label: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", label.lower()).strip()


async def add_resume_skill(
    session: AsyncSession, user: User, payload: ResumeSkillRequest
) -> ResumeSkillRead:
    label = " ".join(payload.label.split())
    existing = (
        await session.execute(
            select(ResumeSkill).where(
                ResumeSkill.user_id == user.id,
                func.lower(ResumeSkill.label) == label.lower(),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AppError("resume_skill_exists", "That skill is already on your resume map.", 409)

    index = await _skill_index(session)
    wanted = _normalise(label)
    skill: Skill | None = None
    subject: Subject | None = None
    for (_, _), (candidate, candidate_subject) in index.items():
        if _normalise(candidate.name) == wanted or _normalise(candidate.slug) == wanted:
            skill, subject = candidate, candidate_subject
            break

    claim = ResumeSkill(
        user_id=user.id,
        skill_id=skill.id if skill else None,
        label=label,
        claimed_level=payload.claimed_level,
    )
    session.add(claim)
    await session.commit()
    await session.refresh(claim)

    evidence = (
        await session.execute(
            select(UserSkill).where(
                UserSkill.user_id == user.id, UserSkill.skill_id == claim.skill_id
            )
        )
    ).scalar_one_or_none() if claim.skill_id else None
    return _resume_read(claim, skill, subject, evidence)


async def delete_resume_skill(
    session: AsyncSession, user: User, claim_id: uuid.UUID
) -> None:
    claim = (
        await session.execute(
            select(ResumeSkill).where(
                ResumeSkill.id == claim_id, ResumeSkill.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if claim is None:
        raise not_found("Resume skill")
    await session.execute(delete(ResumeSkill).where(ResumeSkill.id == claim.id))
    await session.commit()

