from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import (
    ChangePasswordRequest,
    MeResponse,
    OnboardingRequest,
    ProfileUpdateRequest,
    UserRead,
)
from app.schemas.common import MessageResponse
from app.services import auth_service
from app.services.profile_service import complete_onboarding, load_me, update_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeResponse)
async def get_me(user: CurrentUser, session: DbSession) -> MeResponse:
    return await load_me(session, user)


@router.patch("/me", response_model=UserRead)
async def patch_me(
    payload: ProfileUpdateRequest, user: CurrentUser, session: DbSession
) -> UserRead:
    updated = await update_profile(session, user, payload)
    return UserRead.model_validate(updated)


@router.post("/me/onboarding", response_model=MeResponse)
async def onboarding(
    payload: OnboardingRequest, user: CurrentUser, session: DbSession
) -> MeResponse:
    await complete_onboarding(session, user, payload)
    return await load_me(session, user)


@router.post("/me/password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePasswordRequest, user: CurrentUser, session: DbSession
) -> MessageResponse:
    await auth_service.change_password(session, user, payload.current_password, payload.new_password)
    return MessageResponse(message="Password updated. Other sessions have been signed out.")
