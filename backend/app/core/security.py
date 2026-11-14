"""Password hashing and JWT primitives.

Passwords are hashed with Argon2id (via pwdlib). Access tokens are short-lived
JWTs sent in the Authorization header; refresh tokens are long-lived JWTs whose
SHA-256 hash is stored server-side so they can be rotated and revoked.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_password_hash = PasswordHash.recommended()

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired or of the wrong type."""


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:  # malformed/legacy hash must never 500 the login endpoint
        return False


def verify_and_update_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Verify a password and return a re-hashed value when the params changed."""
    try:
        return _password_hash.verify_and_update(password, password_hash)
    except Exception:  # malformed/legacy hash must never 500 the login endpoint
        return False, None


def _create_token(
    subject: str, token_type: TokenType, expires_delta: timedelta, extra: dict[str, Any] | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str) -> tuple[str, int]:
    """Return (token, lifetime_in_seconds)."""
    lifetime = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, "access", lifetime), int(lifetime.total_seconds())


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    lifetime = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = _create_token(subject, "refresh", lifetime)
    return token, datetime.now(timezone.utc) + lifetime


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:  # expired, bad signature, malformed
        raise TokenError("Invalid or expired token") from exc
    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")
    if not payload.get("sub"):
        raise TokenError("Token is missing a subject")
    return payload


def token_fingerprint(token: str) -> str:
    """Store only a fingerprint of refresh tokens, never the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
