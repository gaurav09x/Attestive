"""Career composition: gap-driven recommendations and portfolio briefs.

This agent is deliberately deterministic. Recommendations and briefs are derived
from the role map and the student's measured proficiency, so the same evidence
always produces the same advice and nothing is invented when a model is offline.
`generated_by` records that provenance.
"""

from __future__ import annotations

from app.schemas.career import (
    CareerRecommendation,
    PortfolioBrief,
    RoleSkillRead,
)

READINESS_LABELS: tuple[tuple[int, str], ...] = (
    (75, "interview_ready"),
    (50, "developing"),
    (0, "foundation_building"),
)

DISCLAIMER = (
    "Attestive prepares you for a role; it does not guarantee employment, interviews or "
    "offers. Readiness is computed only from measured skill evidence and completed practice."
)


def readiness_label(score: int) -> str:
    for threshold, label in READINESS_LABELS:
        if score >= threshold:
            return label
    return "foundation_building"


def build_recommendations(
    role_title: str, skills: list[RoleSkillRead], limit: int = 6
) -> list[CareerRecommendation]:
    gaps = sorted(
        (skill for skill in skills if skill.status != "met"),
        key=lambda skill: (-skill.importance, -skill.gap, skill.name),
    )
    recommendations: list[CareerRecommendation] = []
    for skill in gaps[:limit]:
        recommendations.append(
            CareerRecommendation(
                kind="skill_gap",
                title=f"Raise {skill.name} from {skill.proficiency}% to {skill.target}%",
                description=(
                    f"{skill.name} ({skill.subject_name}) is {skill.gap} points below the "
                    f"{role_title} target. Ask the tutor for a worked example, then prove the "
                    "skill with a diagnostic retake."
                ),
                reason=(
                    f"Importance {skill.importance}/3 for this role; current evidence "
                    f"{skill.proficiency}% with {skill.confidence}% confidence."
                ),
                target_url="/tutor",
            )
        )

    if not recommendations:
        recommendations.append(
            CareerRecommendation(
                kind="interview_practice",
                title="Run a mock interview",
                description=(
                    f"Your measured skills meet every {role_title} target. Practise explaining "
                    "them under time pressure and review the rubric feedback."
                ),
                reason="Every required skill is at or above its target from measured evidence.",
                target_url="/career",
            )
        )
    return recommendations


def build_portfolio_briefs(
    role: dict, skills: list[RoleSkillRead]
) -> list[PortfolioBrief]:
    by_slug = {skill.skill_slug: skill for skill in skills}
    briefs: list[PortfolioBrief] = []
    for entry in role.get("portfolio_briefs") or []:
        missing = [
            slug
            for slug in entry.get("skills", [])
            if slug in by_slug and by_slug[slug].status != "met"
        ]
        briefs.append(
            PortfolioBrief(
                title=entry.get("title", "Portfolio project"),
                brief=entry.get("brief", ""),
                skills=list(entry.get("skills", [])),
                missing_skills=missing,
            )
        )
    return briefs


def interview_feedback(
    scores: list[float], readiness: str, weakest: list[str]
) -> list[str]:
    """Structured, rubric-based feedback that never promises an outcome."""
    feedback: list[str] = []
    if scores:
        best = max(scores)
        worst = min(scores)
        feedback.append(
            f"Answer scores ranged from {worst:.0f}% to {best:.0f}% with an average of "
            f"{sum(scores) / len(scores):.0f}%."
        )
    if readiness == "interview_ready":
        feedback.append(
            "Your answers covered the rubric points consistently. Keep rehearsing out loud and "
            "tighten the examples you give."
        )
    elif readiness == "developing":
        feedback.append(
            "You covered part of each rubric. Structure answers as situation, decision, trade-off "
            "and result so the interviewer can follow the reasoning."
        )
    else:
        feedback.append(
            "Several rubric points were missed. Review the model answers, then retake this "
            "interview once you have worked through the gap recommendations."
        )
    if weakest:
        feedback.append("Smallest coverage: " + ", ".join(weakest[:3]) + ".")
    feedback.append(DISCLAIMER)
    return feedback
