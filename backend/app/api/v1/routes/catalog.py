from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import not_found
from app.db.session import get_session
from app.models.catalog import Skill, Subject
from app.schemas.auth import SkillRead, SubjectRead
from app.schemas.common import Page

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/subjects", response_model=Page[SubjectRead])
async def list_subjects(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[SubjectRead]:
    # The catalogue is public curated content; a short shared cache is safe.
    response.headers["Cache-Control"] = "public, max-age=300"
    total = (
        await session.execute(
            select(func.count()).select_from(Subject).where(Subject.is_active.is_(True))
        )
    ).scalar_one()
    subjects = (
        await session.execute(
            select(Subject)
            .where(Subject.is_active.is_(True))
            .order_by(Subject.name)
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return Page[SubjectRead](
        items=[SubjectRead.model_validate(subject) for subject in subjects],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.get("/subjects/{slug}/skills", response_model=list[SkillRead])
async def list_subject_skills(
    slug: str,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SkillRead]:
    response.headers["Cache-Control"] = "public, max-age=300"
    subject = (
        await session.execute(select(Subject).where(Subject.slug == slug))
    ).scalar_one_or_none()
    if subject is None:
        raise not_found("Subject")
    skills = (
        await session.execute(
            select(Skill).where(Skill.subject_id == subject.id).order_by(Skill.name)
        )
    ).scalars().all()
    return [SkillRead.model_validate(skill) for skill in skills]
