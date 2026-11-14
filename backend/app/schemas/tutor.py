from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TutorMode = Literal["explain", "hint", "example", "check"]
TutorLevel = Literal["auto", "beginner", "intermediate", "advanced"]


class TutorStatusRead(BaseModel):
    available: bool
    provider: str
    model: str | None = None
    message: str


class CreateConversationRequest(BaseModel):
    subject_id: uuid.UUID | None = None
    topic: str | None = Field(default=None, max_length=160)
    level: TutorLevel = "auto"


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str
    subject_id: uuid.UUID | None = None
    subject_name: str | None = None
    subject_slug: str | None = None
    accent: str | None = None
    level: str
    status: str
    message_count: int
    last_message_preview: str
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    mode: str
    hint_level: int
    provider: str
    sources: list[str] = Field(default_factory=list)
    created_at: datetime


class ConversationRead(ConversationSummary):
    messages: list[MessageRead] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    items: list[ConversationSummary]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=2, max_length=2000)
    mode: TutorMode = "explain"


class SendMessageResponse(BaseModel):
    conversation: ConversationSummary
    messages: list[MessageRead]
    suggestions: list[str] = Field(default_factory=list)
