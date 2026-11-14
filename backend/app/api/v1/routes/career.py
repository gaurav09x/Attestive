from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.career import (
    CareerRoleDetail,
    CareerRoleListResponse,
    MockInterviewDetail,
    MockInterviewListResponse,
    ResumeSkillListResponse,
    ResumeSkillRead,
    ResumeSkillRequest,
    StartInterviewRequest,
    SubmitAnswerRequest,
)
from app.services import career_service

router = APIRouter(prefix="/career", tags=["career"])


@router.get("/roles", response_model=CareerRoleListResponse)
async def list_roles(user: CurrentUser, session: DbSession) -> CareerRoleListResponse:
    return await career_service.list_roles(session, user)


@router.get("/roles/{slug}", response_model=CareerRoleDetail)
async def role_detail(slug: str, user: CurrentUser, session: DbSession) -> CareerRoleDetail:
    return await career_service.role_detail(session, user, slug)


@router.post(
    "/interviews", response_model=MockInterviewDetail, status_code=status.HTTP_201_CREATED
)
async def start_interview(
    payload: StartInterviewRequest, user: CurrentUser, session: DbSession
) -> MockInterviewDetail:
    return await career_service.start_interview(session, user, payload)


@router.get("/interviews", response_model=MockInterviewListResponse)
async def list_interviews(
    user: CurrentUser, session: DbSession
) -> MockInterviewListResponse:
    return await career_service.list_interviews(session, user)


@router.get("/interviews/{interview_id}", response_model=MockInterviewDetail)
async def get_interview(
    interview_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> MockInterviewDetail:
    return await career_service.get_interview(session, user, interview_id)


@router.post(
    "/interviews/{interview_id}/responses", response_model=MockInterviewDetail
)
async def submit_answer(
    interview_id: uuid.UUID,
    payload: SubmitAnswerRequest,
    user: CurrentUser,
    session: DbSession,
) -> MockInterviewDetail:
    return await career_service.submit_answer(session, user, interview_id, payload)


@router.post(
    "/interviews/{interview_id}/complete", response_model=MockInterviewDetail
)
async def complete_interview(
    interview_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> MockInterviewDetail:
    return await career_service.complete_interview(session, user, interview_id)


@router.get("/resume-skills", response_model=ResumeSkillListResponse)
async def list_resume_skills(
    user: CurrentUser, session: DbSession
) -> ResumeSkillListResponse:
    return await career_service.list_resume_skills(session, user)


@router.post(
    "/resume-skills", response_model=ResumeSkillRead, status_code=status.HTTP_201_CREATED
)
async def add_resume_skill(
    payload: ResumeSkillRequest, user: CurrentUser, session: DbSession
) -> ResumeSkillRead:
    return await career_service.add_resume_skill(session, user, payload)


@router.delete("/resume-skills/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume_skill(
    claim_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> None:
    await career_service.delete_resume_skill(session, user, claim_id)
