"""Roadmap agent.

The agent does **not** choose the learning sequence: modules are selected from
curated curriculum by measured weak skills. The model writes the short plan note
that explains the prioritisation to the student. Output is schema-validated and
length-capped; any failure returns None and the service writes a deterministic
rationale instead.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field, ValidationError

from app.ai.provider import get_provider
from app.core.config import settings

logger = logging.getLogger(__name__)


class RoadmapInsight(BaseModel):
    rationale: str = Field(min_length=20, max_length=600)


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"rationale": {"type": "string"}},
    "required": ["rationale"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are the roadmap agent inside Attestive, a learning platform. "
    "Write a concise, encouraging plan note (2-3 sentences, at most 90 words) for a student. "
    "Be specific about the skills they should strengthen and why the order helps. "
    "Never claim they are job-ready, never invent their scores, and never mention being an AI. "
    'Return only JSON shaped exactly like {"rationale": "..."}'
)


async def write_plan_note(
    *,
    subject_name: str,
    target_level: str,
    weak_skills: list[str],
    module_titles: list[str],
    weekly_minutes: int,
    estimated_weeks: int,
) -> str | None:
    if not settings.AI_ROADMAP_ENABLED:
        return None
    provider = get_provider()
    if provider is None:
        return None

    prompt = (
        f"Subject: {subject_name}\n"
        f"Target level: {target_level}\n"
        f"Skills needing work: {', '.join(weak_skills) if weak_skills else 'none identified; build breadth'}\n"
        f"Planned modules, in order: {'; '.join(module_titles)}\n"
        f"Study budget: {weekly_minutes} minutes per week for about {estimated_weeks} weeks.\n"
        "Explain this plan to the student in 2-3 sentences."
    )

    try:
        raw = await provider.complete_json(
            SYSTEM_PROMPT, prompt, format_schema=RESPONSE_SCHEMA
        )
        if not raw:
            return None
        insight = RoadmapInsight.model_validate(raw)
        return insight.rationale.strip()
    except (ValidationError, TypeError) as exc:
        logger.info("Roadmap agent returned invalid output: %s", exc)
        return None
