from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.mailer import password_reset_email, send_email, verification_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_fingerprint,
    verify_and_update_password,
    verify_password,
)
from app.db.base import utcnow
from app.models.auth_tokens import EmailToken
from app.models.user import RefreshToken, User, UserProfile
from app.schemas.auth import RegisterRequest

VERIFY_EMAIL = "verify_email"
RESET_PASSWORD = "reset_password"
INVALID_LINK_MESSAGE = "This link is invalid or has already been used."


@dataclass(slots=True)
class IssuedTokens:
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_at: datetime


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(func.lower(User.email) == email.lower()))
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, data: RegisterRequest) -> User:
    if await get_user_by_email(session, data.email):
        raise AppError("email_taken", "An account with this email already exists.", 409)

    user = User(
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    user.profile = UserProfile(timezone="UTC")
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:  # concurrent signup for the same address
        await session.rollback()
        raise AppError("email_taken", "An account with this email already exists.", 409) from exc
    await session.refresh(user)
    return user


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(session, email)
    now = datetime.now(timezone.utc)

    if user is not None and user.locked_until is not None:
        locked_until = _as_utc(user.locked_until)
        if locked_until > now:
            minutes = max(1, int((locked_until - now).total_seconds() // 60) + 1)
            raise AppError(
                "account_locked",
                f"Too many failed sign-in attempts. Try again in {minutes} minute(s) "
                "or reset your password.",
                423,
            )
        # The cooling window has passed; clear it before evaluating this attempt.
        user.locked_until = None

    verified, updated_hash = (
        verify_and_update_password(password, user.password_hash) if user else (False, None)
    )
    if user is None or not verified:
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
                user.failed_login_attempts = 0
            await session.commit()
        # Same message and status for unknown email and wrong password.
        raise AppError("invalid_credentials", "Incorrect email or password.", 401)
    if not user.is_active:
        raise AppError("account_disabled", "This account has been disabled.", 403)

    if updated_hash:
        user.password_hash = updated_hash
    user.last_login_at = now
    user.failed_login_attempts = 0
    user.locked_until = None
    await session.commit()
    await session.refresh(user)
    return user


async def issue_email_token(session: AsyncSession, user: User, purpose: str) -> str:
    lifetime = (
        timedelta(hours=settings.VERIFY_TOKEN_TTL_HOURS)
        if purpose == VERIFY_EMAIL
        else timedelta(minutes=settings.RESET_TOKEN_TTL_MINUTES)
    )
    raw_token = secrets.token_urlsafe(32)
    session.add(
        EmailToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=token_fingerprint(raw_token),
            expires_at=utcnow() + lifetime,
        )
    )
    await session.commit()
    return raw_token


async def send_verification(session: AsyncSession, user: User) -> bool:
    raw_token = await issue_email_token(session, user, VERIFY_EMAIL)
    return await send_email(verification_email(user.email, raw_token))


async def _consume_token(session: AsyncSession, raw_token: str, purpose: str) -> EmailToken:
    record = (
        await session.execute(
            select(EmailToken).where(
                EmailToken.token_hash == token_fingerprint(raw_token),
                EmailToken.purpose == purpose,
            )
        )
    ).scalar_one_or_none()
    if record is None or record.used_at is not None:
        raise AppError("invalid_token", INVALID_LINK_MESSAGE, 400)
    if _as_utc(record.expires_at) <= datetime.now(timezone.utc):
        raise AppError(
            "token_expired", "This link has expired. Request a new one.", 400
        )
    record.used_at = utcnow()
    return record


async def verify_email(session: AsyncSession, raw_token: str) -> None:
    record = await _consume_token(session, raw_token, VERIFY_EMAIL)
    user = await session.get(User, record.user_id)
    if user is None:
        raise AppError("invalid_token", INVALID_LINK_MESSAGE, 400)
    user.is_verified = True
    await session.commit()


async def request_password_reset(session: AsyncSession, email: str) -> None:
    """Always silent: an unknown address must not reveal whether it has an account."""
    user = await get_user_by_email(session, email)
    if user is None or not user.is_active:
        return
    raw_token = await issue_email_token(session, user, RESET_PASSWORD)
    await send_email(password_reset_email(user.email, raw_token))


async def reset_password(session: AsyncSession, raw_token: str, new_password: str) -> None:
    record = await _consume_token(session, raw_token, RESET_PASSWORD)
    user = await session.get(User, record.user_id)
    if user is None:
        raise AppError("invalid_token", INVALID_LINK_MESSAGE, 400)
    if not user.is_active:
        raise AppError("account_disabled", "This account has been disabled.", 403)
    if verify_password(new_password, user.password_hash):
        raise AppError("password_reused", "Choose a password you have not used before.", 400)

    user.password_hash = hash_password(new_password)
    user.password_changed_at = utcnow()
    user.failed_login_attempts = 0
    user.locked_until = None
    await session.commit()
    await _revoke_all_for_user(session, user.id)


async def issue_tokens(
    session: AsyncSession, user: User, user_agent: str | None = None
) -> IssuedTokens:
    access_token, expires_in = create_access_token(str(user.id))
    refresh_token, refresh_expires_at = create_refresh_token(str(user.id))

    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_fingerprint(refresh_token),
            expires_at=refresh_expires_at,
            user_agent=(user_agent or "")[:255] or None,
        )
    )
    await session.commit()
    return IssuedTokens(
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_expires_at,
    )


async def _revoke_all_for_user(session: AsyncSession, user_id) -> None:  # type: ignore[no-untyped-def]
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
    )
    now = utcnow()
    for token in result.scalars():
        token.revoked_at = now
    await session.commit()


async def rotate_refresh_token(
    session: AsyncSession, raw_token: str, user_agent: str | None = None
) -> tuple[User, IssuedTokens]:
    payload = decode_token(raw_token, "refresh")  # raises TokenError
    record = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_fingerprint(raw_token))
        )
    ).scalar_one_or_none()

    if record is None:
        raise AppError("invalid_refresh_token", "Your session has expired. Please sign in again.", 401)

    now = datetime.now(timezone.utc)
    if record.revoked_at is not None:
        # Replay of a rotated token: assume compromise and drop every session.
        await _revoke_all_for_user(session, record.user_id)
        raise AppError("invalid_refresh_token", "Your session has expired. Please sign in again.", 401)

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise AppError("invalid_refresh_token", "Your session has expired. Please sign in again.", 401)

    record.revoked_at = now
    user = await session.get(User, record.user_id)
    if user is None or not user.is_active:
        await session.commit()
        raise AppError("account_disabled", "This account is no longer available.", 403)

    tokens = await issue_tokens(session, user, user_agent)
    del payload
    return user, tokens


async def revoke_refresh_token(session: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    record = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_fingerprint(raw_token))
        )
    ).scalar_one_or_none()
    if record and record.revoked_at is None:
        record.revoked_at = utcnow()
        await session.commit()


async def change_password(session: AsyncSession, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        raise AppError("invalid_credentials", "Your current password is incorrect.", 400)
    if verify_password(new, user.password_hash):
        raise AppError("password_reused", "Choose a password you have not used before.", 400)
    user.password_hash = hash_password(new)
    user.password_changed_at = utcnow()
    await session.commit()
    await _revoke_all_for_user(session, user.id)
