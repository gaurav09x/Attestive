from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.config import settings

_PASSWORD_LETTER = re.compile(r"[A-Za-z]")
_PASSWORD_DIGIT = re.compile(r"\d")


def validate_password_strength(value: str) -> str:
    if len(value) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    if len(value) > 128:
        raise ValueError("Password must be at most 128 characters long")
    if not _PASSWORD_LETTER.search(value) or not _PASSWORD_DIGIT.search(value):
        raise ValueError("Password must contain both letters and numbers")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=2, max_length=120)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("full_name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Please enter your name")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    headline: str | None = None
    bio: str | None = None
    education_level: str | None = None
    experience_level: str | None = None
    career_goal: str | None = None
    target_role: str | None = None
    weekly_minutes_goal: int | None = None
    timezone: str = "UTC"
    onboarding_step: int = 0
    onboarding_completed_at: datetime | None = None


class PreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    learning_style: str
    session_minutes: int
    prefers_projects: bool
    prefers_theory_first: bool


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    xp_total: int
    is_verified: bool
    onboarding_completed: bool
    created_at: datetime
    profile: ProfileRead | None = None
    preferences: PreferencesRead | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    category: str
    accent: str
    icon: str


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    subject_id: uuid.UUID


class UserSkillRead(BaseModel):
    skill_id: uuid.UUID
    slug: str
    name: str
    proficiency: int
    confidence: int
    source: str
    last_assessed_at: datetime | None = None


class MeResponse(BaseModel):
    user: UserRead
    interests: list[SubjectRead]
    skills: list[UserSkillRead]


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    headline: str | None = Field(default=None, max_length=140)
    bio: str | None = Field(default=None, max_length=2000)
    target_role: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    weekly_minutes_goal: int | None = Field(default=None, ge=30, le=3000)

    @field_validator("full_name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Please enter your name")
        return cleaned


class OnboardingRequest(BaseModel):
    education_level: str
    experience_level: str
    learning_style: str
    session_minutes: int = Field(ge=10, le=180)
    weekly_minutes_goal: int = Field(ge=60, le=3000)
    career_goal: str
    target_role: str | None = Field(default=None, max_length=120)
    subject_slugs: list[str] = Field(min_length=1, max_length=5)
    prefers_projects: bool = True
    prefers_theory_first: bool = False
    timezone: str | None = Field(default=None, max_length=64)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)
