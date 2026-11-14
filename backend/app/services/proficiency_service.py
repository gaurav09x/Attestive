"""Evidence-based proficiency updates.

Proficiency is an estimate, not a verdict. A first assessment carries substantial
weight because it is the only evidence available; later evidence moves the
estimate less and confidence rises with each observation.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utc_now
from app.models.user import UserSkill

FIRST_EVIDENCE_WEIGHT = 0.85
SUBSEQUENT_EVIDENCE_WEIGHT = 0.45
CONFIDENCE_PER_ASSESSMENT = 25


@dataclass(slots=True)
class SkillEvidence:
    skill_id: object
    skill_slug: str
    skill_name: str
    score: float  # 0..1 for this skill in this attempt
    difficulty: int


@dataclass(slots=True)
class SkillUpdate:
    skill_id: object
    slug: str
    name: str
    score: float
    proficiency: int
    confidence: int


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, round(value)))


async def apply_evidence(
    session: AsyncSession, user_id, evidences: list[SkillEvidence]
) -> list[SkillUpdate]:  # type: ignore[no-untyped-def]
    """Aggregate per-question evidence per skill and persist new estimates."""
    if not evidences:
        return []

    grouped: dict[object, list[SkillEvidence]] = {}
    meta: dict[object, SkillEvidence] = {}
    for evidence in evidences:
        grouped.setdefault(evidence.skill_id, []).append(evidence)
        meta[evidence.skill_id] = evidence

    rows = (
        await session.execute(
            select(UserSkill).where(
                UserSkill.user_id == user_id,
                UserSkill.skill_id.in_(list(grouped.keys())),
            )
        )
    ).scalars().all()
    existing = {row.skill_id: row for row in rows}

    updates: list[SkillUpdate] = []
    now = utc_now()

    for skill_id, items in grouped.items():
        total_weight = sum(item.difficulty for item in items) or 1
        observed = sum(item.score * item.difficulty for item in items) / total_weight
        head = meta[skill_id]
        row = existing.get(skill_id)

        if row is None:
            row = UserSkill(
                user_id=user_id,
                skill_id=skill_id,
                proficiency=0,
                confidence=0,
                source="assessment",
            )
            session.add(row)
            prior_proficiency = 0
            prior_confidence = 0
            weight = FIRST_EVIDENCE_WEIGHT
        else:
            prior_proficiency = row.proficiency
            prior_confidence = row.confidence
            # A self-reported seed is a weak prior: the first real assessment
            # should be able to move it substantially.
            weight = (
                FIRST_EVIDENCE_WEIGHT
                if row.source == "self_report"
                else SUBSEQUENT_EVIDENCE_WEIGHT
            )

        new_proficiency = _clamp(
            prior_proficiency * (1 - weight) + observed * 100 * weight
        )
        row.proficiency = new_proficiency
        row.confidence = min(100, prior_confidence + CONFIDENCE_PER_ASSESSMENT)
        row.source = "assessment"
        row.last_assessed_at = now

        updates.append(
            SkillUpdate(
                skill_id=skill_id,
                slug=head.skill_slug,
                name=head.skill_name,
                score=round(observed * 100),
                proficiency=new_proficiency,
                confidence=row.confidence,
            )
        )

    await session.flush()
    return updates
