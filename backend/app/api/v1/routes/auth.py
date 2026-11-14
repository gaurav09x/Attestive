from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.api.deps import CurrentUser, DbSession, require_trusted_origin
from app.core.config import settings
from app.core.errors import AppError
from app.core.security import TokenError
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    UserRead,
    VerifyEmailRequest,
)
from app.services import auth_service
from app.services.profile_service import load_me

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_PATH = f"{settings.API_V1_PREFIX}/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


async def _auth_response(
    session, user: User, response: Response, user_agent: str | None
) -> AuthResponse:  # type: ignore[no-untyped-def]
    tokens = await auth_service.issue_tokens(session, user, user_agent)
    _set_refresh_cookie(response, tokens.refresh_token)
    await session.refresh(user)
    return AuthResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> AuthResponse:
    user = await auth_service.register_user(session, payload)
    # Best effort: a delivery failure must not roll back a created account. The
    # login response exposes `is_verified`, so the UI can offer a resend.
    await auth_service.send_verification(session, user)
    return await _auth_response(session, user, response, request.headers.get("user-agent"))


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> AuthResponse:
    user = await auth_service.authenticate(session, payload.email, payload.password)
    return await _auth_response(session, user, response, request.headers.get("user-agent"))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    response: Response,
    session: DbSession,
) -> AuthResponse:
    require_trusted_origin(request)
    raw = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw:
        raise AppError("no_session", "No active session. Please sign in.", 401)
    try:
        user, tokens = await auth_service.rotate_refresh_token(
            session, raw, request.headers.get("user-agent")
        )
    except TokenError as exc:
        _clear_refresh_cookie(response)
        raise AppError("invalid_refresh_token", "Your session has expired. Please sign in again.", 401) from exc
    except AppError:
        _clear_refresh_cookie(response)
        raise
    _set_refresh_cookie(response, tokens.refresh_token)
    await session.refresh(user)
    return AuthResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: DbSession) -> Response:
    require_trusted_origin(request)
    await auth_service.revoke_refresh_token(session, request.cookies.get(settings.REFRESH_COOKIE_NAME))
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, session: DbSession) -> dict:
    await auth_service.verify_email(session, payload.token)
    return {"verified": True}


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(user: CurrentUser, session: DbSession) -> dict:
    if user.is_verified:
        raise AppError("already_verified", "This email address is already verified.", 409)
    sent = await auth_service.send_verification(session, user)
    if sent:
        message = f"A verification link was sent to {user.email}."
    elif settings.EMAIL_DELIVERY == "console":
        message = (
            "A verification link was created. The console transport logs it in development; "
            "outside development the body is suppressed, so configure a real email provider."
        )
    else:
        message = (
            "A verification link was created but delivery failed. Check the API log for the "
            "provider response, then try again."
        )
    return {"sent": sent, "message": message}


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    payload: PasswordResetRequest, session: DbSession
) -> dict:
    await auth_service.request_password_reset(session, payload.email)
    # Deliberately identical for known and unknown addresses.
    if settings.email_configured:
        message = "If an account exists for that address, a reset link has been sent."
    else:
        message = (
            "If an account exists for that address, a reset link has been created. Email "
            "delivery is not configured on this deployment — in development the link is in "
            "the API log."
        )
    return {"message": message}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> Response:
    require_trusted_origin(request)
    await auth_service.reset_password(session, payload.token, payload.new_password)
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me")
async def me(user: CurrentUser, session: DbSession) -> dict:
    payload = await load_me(session, user)
    return payload.model_dump(mode="json")
