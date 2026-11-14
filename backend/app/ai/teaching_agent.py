"""Teaching agent.

Turns one student message plus measured context into a tutoring reply. The agent
proposes prose only: the tutor service validates and persists it, and any
failure returns None so the API reports the tutor as unavailable rather than
inventing teaching.

The flow mirrors the plan in `docs/PHASES.md` (retrieve → plan → generate →
check) but stops at prose generation: the model is not asked for JSON, because a
conversation reply should read like writing, and a small local model produces
valid free text far more reliably than valid JSON.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.ai.provider import get_provider

logger = logging.getLogger(__name__)

MAX_REPLY_CHARS = 4000

MODE_INSTRUCTIONS: dict[str, str] = {
    "explain": (
        "Explain the concept the student asked about. Use one concrete example, "
        "connect it to their measured level, and finish with a short question "
        "that checks their understanding."
    ),
    "hint": (
        "Give a hint, not the answer. Do not state the final solution or write "
        "the complete code. Reveal only one more step than the previous hint "
        "level did, then ask the student what they will try next."
    ),
    "example": (
        "Work through one concrete example end to end, naming each step. Keep it "
        "small enough to follow in a few minutes."
    ),
    "check": (
        "Ask the student two short questions that test the concept, and stop. Do "
        "not answer your own questions."
    ),
}

SYSTEM_PROMPT = (
    "You are the tutor inside Attestive, a learning platform for programming and "
    "data skills. Teach rather than answer: build understanding, use the student's "
    "own numbers when you mention difficulty, and never claim they are job-ready. "
    "Stay on the requested subject, do not invent platform features, scores or "
    "lesson names, and never mention being an AI model. Write plain prose or short "
    "markdown sections, at most 250 words. If the answer genuinely needs code, "
    "keep it under 15 lines and explain it."
)


@dataclass
class TutoringContext:
    subject_name: str
    level: str
    learning_style: str | None = None
    session_minutes: int | None = None
    target_role: str | None = None
    weak_skills: list[str] = field(default_factory=list)
    strong_skills: list[str] = field(default_factory=list)
    next_step: str | None = None
    material: list[str] = field(default_factory=list)
    history: list[tuple[str, str]] = field(default_factory=list)


def _build_prompt(message: str, mode: str, hint_level: int, context: TutoringContext) -> str:
    lines = [
        f"Subject: {context.subject_name}",
        f"Student level: {context.level}",
    ]
    if context.target_role:
        lines.append(f"Target role: {context.target_role}")
    if context.learning_style:
        lines.append(f"Learning style: {context.learning_style}")
    if context.session_minutes:
        lines.append(f"Typical session length: {context.session_minutes} minutes")
    if context.weak_skills:
        lines.append(f"Measured weak skills: {', '.join(context.weak_skills)}")
    if context.strong_skills:
        lines.append(f"Measured strong skills: {', '.join(context.strong_skills)}")
    if context.next_step:
        lines.append(f"Current roadmap step: {context.next_step}")
    if context.material:
        lines.append("Relevant curriculum:")
        lines.extend(f"- {item}" for item in context.material)

    if context.history:
        lines.append("Conversation so far:")
        lines.extend(f"{role}: {content}" for role, content in context.history[-10:])

    task = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["explain"])
    if mode == "hint":
        task = f"This is hint level {max(1, hint_level)} of at most 4. {task}"
    lines.append(f"Task: {task}")
    lines.append(f"Student message: {message}")
    return "\n".join(lines)


async def compose_reply(
    *,
    message: str,
    mode: str,
    hint_level: int,
    context: TutoringContext,
) -> tuple[str, str] | None:
    """Return (reply text, provider label) or None when no usable reply exists."""
    provider = get_provider()
    if provider is None:
        return None

    prompt = _build_prompt(message, mode, hint_level, context)
    # Each provider applies its own default timeout; a hosted API and a local
    # CPU model have very different reasonable budgets.
    text = await provider.complete_text(SYSTEM_PROMPT, prompt)
    if not text:
        return None

    reply = text.strip()[:MAX_REPLY_CHARS]
    if len(reply) < 20:
        # Too short to be teaching; treat as a failed generation.
        logger.info("Tutor reply discarded: %s characters", len(reply))
        return None
    return reply, f"{provider.name}:{provider.model}"
