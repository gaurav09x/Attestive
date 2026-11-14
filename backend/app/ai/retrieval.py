"""Curriculum retrieval for tutor context.

The curated catalogue is small (six subjects, a few dozen modules), so retrieval
scores module text against the student's question directly in the database. This
keeps every tutor reply grounded in material the platform actually ships, with
no extra service to run. Embedding-based retrieval (ChromaDB) remains the plan
for a larger corpus; the interface here is what it would replace.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Course, Module

_WORD = re.compile(r"[a-z0-9+#]{3,}")

# Words that appear in almost every question and would match everything.
_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "can",
    "does",
    "explain",
    "for",
    "how",
    "into",
    "its",
    "just",
    "like",
    "more",
    "not",
    "please",
    "should",
    "some",
    "than",
    "that",
    "the",
    "then",
    "there",
    "they",
    "this",
    "use",
    "using",
    "want",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
    "would",
    "you",
}


@dataclass(frozen=True)
class RetrievedMaterial:
    title: str
    body: str


def _tokens(text: str) -> set[str]:
    return {word for word in _WORD.findall(text.lower()) if word not in _STOPWORDS}


async def retrieve_material(
    session: AsyncSession,
    subject_id: uuid.UUID | None,
    query: str,
    limit: int = 4,
) -> list[RetrievedMaterial]:
    """Modules whose text best matches the question, in curriculum order.

    A module always stays eligible, so a question that shares no vocabulary with
    the catalogue still yields grounded context instead of an empty prompt.
    """
    if subject_id is None:
        return []

    rows = (
        await session.execute(
            select(Module, Course)
            .join(Course, Course.id == Module.course_id)
            .where(Course.subject_id == subject_id, Course.is_published.is_(True))
            .order_by(Course.title, Module.position)
        )
    ).all()
    if not rows:
        return []

    query_tokens = _tokens(query)
    scored: list[tuple[int, int, Module, Course]] = []
    for module, course in rows:
        haystack = " ".join(
            [
                module.title,
                module.summary,
                " ".join(module.skill_slugs or []),
                course.title,
                course.summary,
            ]
        )
        scored.append((len(query_tokens & _tokens(haystack)), module.position, module, course))

    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    relevant = [entry for entry in scored if entry[0] > 0][:limit] or scored[:limit]
    return [
        RetrievedMaterial(title=f"{course.title} — {module.title}", body=module.summary)
        for _overlap, _position, module, course in relevant
    ]
