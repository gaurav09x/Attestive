"""Tutor conversations: authorisation, persistence and model orchestration.

The teaching agent only proposes prose. Nothing is stored unless the model was
reachable and returned usable text, so an offline provider produces a clear
`ai_unavailable` error instead of an invented lesson.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.provider import get_provider
from app.ai.retrieval import retrieve_material
from app.ai.teaching_agent import TutoringContext, compose_reply
from app.core.config import settings
from app.core.errors import AppError, not_found
from app.core.time import local_today, utc_now
from app.models.catalog import Skill, Subject
from app.models.enums import ProgressStatus
from app.models.learning import LearningPath, LearningPathItem
from app.models.tutor import ConversationMessage, TutorConversation
from app.models.user import User, UserSkill
from app.schemas.tutor import (
    ConversationListResponse,
    ConversationRead,
    ConversationSummary,
    CreateConversationRequest,
    MessageRead,
    SendMessageRequest,
    SendMessageResponse,
    TutorStatusRead,
)
from app.services.achievements import evaluate_achievements
from app.services.gamification import award_xp, record_activity, xp_for_action

DEFAULT_TOPIC = "Tutoring session"
MAX_HISTORY_MESSAGES = 10

SUGGESTIONS: dict[str, list[str]] = {
    "explain": [
        "Give me a concrete example",
        "Explain it more simply",
        "Quiz me on this",
    ],
    "hint": [
        "Give me a stronger hint",
        "Show the reasoning",
        "Let me try again",
    ],
    "example": [
        "Walk me through the tricky part",
        "Give me a practice problem",
        "Explain the underlying rule",
    ],
    "check": [
        "Check my answer",
        "Explain what I missed",
        "Give me another question",
    ],
}


async def tutor_status() -> TutorStatusRead:
    """Whether teaching is possible right now, and why it is not."""
    provider = get_provider()
    if provider is None:
        return TutorStatusRead(
            available=False,
            provider=settings.AI_PROVIDER,
            model=None,
            message=(
                "The AI provider is disabled (AI_PROVIDER=disabled). The tutor is unavailable; "
                "lessons and diagnostics still work."
            ),
        )

    model = getattr(provider, "model", None)
    installed = await provider.list_models()
    if installed is None:
        return TutorStatusRead(
            available=False,
            provider=provider.name,
            model=model,
            message=(
                f"Could not reach {provider.name} at the configured address. "
                "Check OPENAI_BASE_URL and OPENAI_API_KEY, then reload this page."
            ),
        )

    if model and installed:
        base = model.split(":")[0]
        has_model = any(name.split(":")[0] == base for name in installed)
        if not has_model:
            fix = (
                f"Set OPENAI_MODEL to a model your provider serves (it offers: "
                f"{', '.join(installed[:4])}{'…' if len(installed) > 4 else ''})."
            )
            return TutorStatusRead(
                available=False,
                provider=provider.name,
                model=model,
                message=f"{provider.name} is configured, but the model {model} is unavailable. {fix}",
            )

    return TutorStatusRead(
        available=True,
        provider=provider.name,
        model=model,
        message=(
            f"{provider.name} is ready with {model}." if model else f"{provider.name} is ready."
        ),
    )


def _message_read(message: ConversationMessage) -> MessageRead:
    return MessageRead(
        id=message.id,
        role=message.role,
        content=message.content,
        mode=message.mode,
        hint_level=message.hint_level,
        provider=message.provider,
        sources=list(message.sources or []),
        created_at=message.created_at,
    )


def _summary(
    conversation: TutorConversation,
    subject: Subject | None,
    messages: list[ConversationMessage],
) -> ConversationSummary:
    last = messages[-1].content if messages else ""
    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        subject_id=subject.id if subject else None,
        subject_name=subject.name if subject else None,
        subject_slug=subject.slug if subject else None,
        accent=subject.accent if subject else None,
        level=conversation.level,
        status=conversation.status,
        message_count=len(messages),
        last_message_preview=last[:140],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _detail(
    conversation: TutorConversation,
    subject: Subject | None,
    messages: list[ConversationMessage],
) -> ConversationRead:
    return ConversationRead(
        **_summary(conversation, subject, messages).model_dump(),
        messages=[_message_read(message) for message in messages],
    )


async def _resolve_level(
    session: AsyncSession,
    user: User,
    subject_id: uuid.UUID | None,
    requested: str,
) -> str:
    if requested != "auto":
        return requested

    statement = (
        select(UserSkill.proficiency)
        .join(Skill, Skill.id == UserSkill.skill_id)
        .where(UserSkill.user_id == user.id)
    )
    if subject_id is not None:
        statement = statement.where(Skill.subject_id == subject_id)
    scores = [row[0] for row in (await session.execute(statement)).all()]
    if not scores:
        return "beginner"
    average = sum(scores) / len(scores)
    if average < 40:
        return "beginner"
    if average < 70:
        return "intermediate"
    return "advanced"


async def create_conversation(
    session: AsyncSession, user: User, payload: CreateConversationRequest
) -> ConversationRead:
    subject: Subject | None = None
    if payload.subject_id is not None:
        subject = (
            await session.execute(
                select(Subject).where(
                    Subject.id == payload.subject_id, Subject.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()
        if subject is None:
            raise not_found("Subject")

    level = await _resolve_level(
        session, user, subject.id if subject else None, payload.level
    )
    title = (payload.topic or "").strip()
    if not title:
        title = f"{subject.name} tutoring" if subject else DEFAULT_TOPIC

    now = utc_now()
    conversation = TutorConversation(
        user_id=user.id,
        subject_id=subject.id if subject else None,
        title=title[:160],
        level=level,
        last_message_at=now,
        # Server defaults would not be loaded after INSERT; set them explicitly
        # so the response can be serialised without another round trip.
        created_at=now,
        updated_at=now,
    )
    session.add(conversation)
    await session.commit()
    return _detail(conversation, subject, [])


async def list_conversations(
    session: AsyncSession, user: User
) -> ConversationListResponse:
    rows = (
        await session.execute(
            select(TutorConversation, Subject)
            .outerjoin(Subject, Subject.id == TutorConversation.subject_id)
            .options(selectinload(TutorConversation.messages))
            .where(TutorConversation.user_id == user.id)
            .order_by(desc(TutorConversation.last_message_at))
            .limit(50)
        )
    ).all()
    return ConversationListResponse(
        items=[
            _summary(conversation, subject, list(conversation.messages))
            for conversation, subject in rows
        ]
    )


async def _owned_conversation(
    session: AsyncSession, user: User, conversation_id: uuid.UUID
) -> TutorConversation:
    conversation = (
        await session.execute(
            select(TutorConversation)
            .options(selectinload(TutorConversation.messages))
            .where(
                TutorConversation.id == conversation_id,
                TutorConversation.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if conversation is None:
        raise not_found("Conversation")
    return conversation


async def get_conversation(
    session: AsyncSession, user: User, conversation_id: uuid.UUID
) -> ConversationRead:
    conversation = await _owned_conversation(session, user, conversation_id)
    subject = (
        await session.get(Subject, conversation.subject_id)
        if conversation.subject_id
        else None
    )
    return _detail(conversation, subject, list(conversation.messages))


async def delete_conversation(
    session: AsyncSession, user: User, conversation_id: uuid.UUID
) -> None:
    conversation = await _owned_conversation(session, user, conversation_id)
    await session.execute(
        delete(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation.id
        )
    )
    await session.delete(conversation)
    await session.commit()


async def _build_context(
    session: AsyncSession,
    user: User,
    conversation: TutorConversation,
    subject: Subject | None,
    message: str,
) -> tuple[TutoringContext, list]:
    skill_statement = (
        select(Skill.name, UserSkill.proficiency)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == user.id)
        .order_by(desc(UserSkill.proficiency))
    )
    if subject is not None:
        skill_statement = skill_statement.where(Skill.subject_id == subject.id)
    skill_rows = (await session.execute(skill_statement)).all()

    strong_skills = [name for name, score in skill_rows if score >= 70][:3]
    weak_skills = [name for name, score in reversed(skill_rows) if score < 70][:3]

    next_step: str | None = None
    if subject is not None:
        row = (
            await session.execute(
                select(LearningPathItem.title, LearningPathItem.objective)
                .join(LearningPath, LearningPath.id == LearningPathItem.path_id)
                .where(
                    LearningPath.user_id == user.id,
                    LearningPath.subject_id == subject.id,
                    LearningPath.status == "active",
                    LearningPathItem.status != ProgressStatus.COMPLETED.value,
                )
                .order_by(LearningPathItem.position)
                .limit(1)
            )
        ).first()
        if row is not None:
            next_step = f"{row[0]} — {row[1]}"[:240]

    material = await retrieve_material(
        session, subject.id if subject else None, message
    )

    profile = user.profile
    preferences = user.preferences
    return TutoringContext(
        subject_name=subject.name if subject else "General programming",
        level=conversation.level,
        learning_style=preferences.learning_style if preferences else None,
        session_minutes=preferences.session_minutes if preferences else None,
        target_role=profile.target_role if profile else None,
        weak_skills=weak_skills,
        strong_skills=strong_skills,
        next_step=next_step,
        material=[f"{item.title}: {item.body}" for item in material],
        history=[(entry.role, entry.content) for entry in list(conversation.messages)[-MAX_HISTORY_MESSAGES:]],
    ), material


async def send_message(
    session: AsyncSession,
    user: User,
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
) -> SendMessageResponse:
    conversation = await _owned_conversation(session, user, conversation_id)

    status = await tutor_status()
    if not status.available:
        raise AppError("ai_unavailable", status.message, 503)

    content = payload.content.strip()
    if len(content) < 2:
        raise AppError(
            "invalid_message",
            "Write a little more so the tutor has something to work with.",
            422,
        )

    subject = (
        await session.get(Subject, conversation.subject_id)
        if conversation.subject_id
        else None
    )
    existing = list(conversation.messages)

    hint_level = 0
    if payload.mode == "hint":
        previous_hints = sum(
            1
            for entry in existing
            if entry.role == "assistant" and entry.mode == "hint"
        )
        hint_level = min(4, previous_hints + 1)

    context, material = await _build_context(
        session, user, conversation, subject, content
    )
    composed = await compose_reply(
        message=content, mode=payload.mode, hint_level=hint_level, context=context
    )
    if composed is None:
        raise AppError(
            "ai_unavailable",
            "The tutor could not produce a reply. Check that the model is installed and "
            "responsive, then try again.",
            503,
        )
    reply, provider_label = composed

    student_message = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=content,
        mode=payload.mode,
        provider="student",
    )
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply,
        mode=payload.mode,
        hint_level=hint_level,
        provider=provider_label,
        sources=[item.title for item in material],
    )
    session.add_all([student_message, assistant_message])

    default_titles = {DEFAULT_TOPIC}
    if subject is not None:
        default_titles.add(f"{subject.name} tutoring")
    if not existing and conversation.title in default_titles:
        conversation.title = content[:80]

    # A tutoring exchange is a study event, but it has no measured duration: the
    # activity records zero minutes so streaks are honest and study time is not
    # inflated. XP is awarded once per conversation.
    xp_awarded = await award_xp(
        session,
        user,
        xp_for_action("tutor_session"),
        "tutor_session",
        "tutor_conversation",
        conversation.id,
    )
    record_activity(
        session,
        user_id=user.id,
        kind="tutor",
        minutes=0,
        xp_awarded=xp_awarded,
        subject_id=conversation.subject_id,
        day=local_today(user.profile.timezone if user.profile else None),
    )
    await evaluate_achievements(session, user)

    now = utc_now()
    conversation.last_message_at = now
    conversation.updated_at = now
    await session.commit()

    history = existing + [student_message, assistant_message]
    return SendMessageResponse(
        conversation=_summary(conversation, subject, history),
        messages=[_message_read(student_message), _message_read(assistant_message)],
        suggestions=SUGGESTIONS.get(payload.mode, []),
    )
