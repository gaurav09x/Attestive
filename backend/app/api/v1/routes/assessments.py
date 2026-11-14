from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.assessment import (
    AssessmentOverview,
    AttemptRead,
    AttemptResult,
    AttemptReview,
    SavedResponse,
    SubmitRequest,
)
from app.services import assessment_service

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=AssessmentOverview)
async def overview(user: CurrentUser, session: DbSession) -> AssessmentOverview:
    return await assessment_service.get_overview(session, user)


@router.post(
    "/{assessment_id}/attempts",
    response_model=AttemptRead,
    status_code=status.HTTP_201_CREATED,
)
async def start_attempt(
    assessment_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> AttemptRead:
    return await assessment_service.start_attempt(session, user, assessment_id)


@router.get("/attempts/{attempt_id}", response_model=AttemptRead)
async def attempt(
    attempt_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> AttemptRead:
    return await assessment_service.get_attempt(session, user, attempt_id)


@router.put(
    "/attempts/{attempt_id}/responses/{question_id}", response_model=SavedResponse
)
async def save_response(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: dict,
    user: CurrentUser,
    session: DbSession,
) -> SavedResponse:
    await assessment_service.save_response(session, user, attempt_id, question_id, payload)
    return SavedResponse(question_id=question_id, saved=True)


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptResult)
async def submit(
    attempt_id: uuid.UUID,
    payload: SubmitRequest,
    user: CurrentUser,
    session: DbSession,
) -> AttemptResult:
    return await assessment_service.submit_attempt(session, user, attempt_id, payload)


@router.get("/attempts/{attempt_id}/review", response_model=AttemptReview)
async def review(
    attempt_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> AttemptReview:
    return await assessment_service.get_review(session, user, attempt_id)
