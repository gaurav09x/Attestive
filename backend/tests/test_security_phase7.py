"""Phase 7: security headers, rate limiting, lockout, verification and reset."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.services import auth_service

from tests.conftest import auth_headers, register


@pytest.mark.asyncio
async def test_security_headers_on_api_responses(client) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_cors_preflight_allows_every_method_the_frontend_uses(client) -> None:
    # The diagnostic page saves answers with PUT. A method missing from the CORS
    # allowlist fails its preflight, and the browser surfaces that as a network
    # error ("Cannot reach the Attestive API") rather than a 4xx.
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        response = await client.options(
            "/api/v1/assessments/attempts/x/responses/y",
            headers={
                "Origin": settings.FRONTEND_ORIGIN,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200, method
        assert method in response.headers["access-control-allow-methods"]


@pytest.mark.asyncio
async def test_rate_limit_returns_envelope_and_retry_after(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_PER_MINUTE", 1)
    first = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "WrongPass1"}
    )
    second = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "WrongPass1"}
    )
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"
    assert int(second.headers["retry-after"]) >= 1
    assert first.status_code in {401, 429}


@pytest.mark.asyncio
async def test_account_lockout_after_repeated_failures(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "MAX_FAILED_LOGINS", 3)
    monkeypatch.setattr(settings, "LOCKOUT_MINUTES", 15)
    await register(client, email="locked@example.com", password="CorrectHorse9")

    for _ in range(3):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "locked@example.com", "password": "WrongHorse9"},
        )
        assert response.status_code == 401, response.text

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": "locked@example.com", "password": "CorrectHorse9"},
    )
    assert blocked.status_code == 423
    assert blocked.json()["error"]["code"] == "account_locked"


@pytest.mark.asyncio
async def test_email_verification_flow(client) -> None:
    payload = await register(client, email="verify@example.com")
    headers = auth_headers(payload)
    assert payload["user"]["is_verified"] is False

    async with client.session_factory() as session:  # type: ignore[attr-defined]
        user = (
            await session.execute(select(User).where(User.email == "verify@example.com"))
        ).scalar_one()
        raw_token = await auth_service.issue_email_token(
            session, user, auth_service.VERIFY_EMAIL
        )

    verified = await client.post(
        "/api/v1/auth/verify-email", json={"token": raw_token}
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["verified"] is True

    # A token is single-use.
    replay = await client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert replay.status_code == 400
    assert replay.json()["error"]["code"] == "invalid_token"

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["user"]["is_verified"] is True


@pytest.mark.asyncio
async def test_password_reset_flow_revokes_sessions(client) -> None:
    await register(client, email="reset@example.com", password="CorrectHorse9")
    raw_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert raw_refresh

    # Unknown addresses get the same response as known ones.
    unknown = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "ghost@example.com"}
    )
    assert unknown.status_code == 202
    known = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "reset@example.com"}
    )
    assert known.status_code == 202
    assert "If an account exists" in known.json()["message"]

    async with client.session_factory() as session:  # type: ignore[attr-defined]
        user = (
            await session.execute(select(User).where(User.email == "reset@example.com"))
        ).scalar_one()
        raw_token = await auth_service.issue_email_token(
            session, user, auth_service.RESET_PASSWORD
        )

    reused = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "CorrectHorse9"},
    )
    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "password_reused"

    changed = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "BrandNewPass7"},
    )
    assert changed.status_code == 204, changed.text

    # The old password no longer works; the new one does.
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "CorrectHorse9"},
    )
    assert old_login.status_code == 401
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "BrandNewPass7"},
    )
    assert new_login.status_code == 200, new_login.text

    # The refresh token issued before the reset was revoked server-side.
    revoked = await client.post(
        "/api/v1/auth/refresh",
        cookies={settings.REFRESH_COOKIE_NAME: raw_refresh},
    )
    assert revoked.status_code == 401
