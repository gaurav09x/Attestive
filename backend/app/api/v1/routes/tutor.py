from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.tutor import (
    ConversationListResponse,
    ConversationRead,
    CreateConversationRequest,
    SendMessageRequest,
    SendMessageResponse,
    TutorStatusRead,
)
from app.services import tutor_service

router = APIRouter(prefix="/tutor", tags=["tutor"])


@router.get("/status", response_model=TutorStatusRead)
async def get_status(_: CurrentUser) -> TutorStatusRead:
    return await tutor_service.tutor_status()


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user: CurrentUser, session: DbSession
) -> ConversationListResponse:
    return await tutor_service.list_conversations(session, user)


@router.post(
    "/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    payload: CreateConversationRequest, user: CurrentUser, session: DbSession
) -> ConversationRead:
    return await tutor_service.create_conversation(session, user, payload)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> ConversationRead:
    return await tutor_service.get_conversation(session, user, conversation_id)


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> None:
    await tutor_service.delete_conversation(session, user, conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages", response_model=SendMessageResponse
)
async def send_message(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    user: CurrentUser,
    session: DbSession,
) -> SendMessageResponse:
    return await tutor_service.send_message(session, user, conversation_id, payload)
