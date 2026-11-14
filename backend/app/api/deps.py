from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import TokenError, decode_token
from app.db.session import get_session
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError("not_authenticated", "Sign in to continue.", 401)
    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = uuid.UUID(str(payload["sub"]))
    except (TokenError, ValueError) as exc:
        raise AppError("invalid_token", "Your session is invalid or has expired.", 401) from exc

    user = await session.get(User, user_id)
    if user is None:
        raise AppError("invalid_token", "Your session is invalid or has expired.", 401)
    if not user.is_active:
        raise AppError("account_disabled", "This account has been disabled.", 403)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def require_trusted_origin(request: Request) -> None:
    """Cookie-authenticated endpoints must reject foreign browser origins."""
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        raise AppError("invalid_origin", "Request origin is not allowed.", 403)
