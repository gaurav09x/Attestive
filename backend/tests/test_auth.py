from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, register

API = "/api/v1"


async def test_register_login_and_profile(client: AsyncClient) -> None:
    payload = await register(client)
    assert payload["user"]["email"] == "ada@example.com"
    assert payload["user"]["onboarding_completed"] is False
    assert payload["user"]["xp_total"] == 0

    me = await client.get(f"{API}/auth/me", headers=auth_headers(payload))
    assert me.status_code == 200
    body = me.json()
    assert body["user"]["full_name"] == "Ada Lovelace"
    assert body["interests"] == []

    login = await client.post(
        f"{API}/auth/login", json={"email": "ada@example.com", "password": "CorrectHorse9"}
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == payload["user"]["id"]


async def test_duplicate_email_is_rejected(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(
        f"{API}/auth/register",
        json={"email": "ADA@example.com", "password": "AnotherPass1", "full_name": "Ada Again"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


@pytest.mark.parametrize("password", ["short", "alllettersonly", "1234567890"])
async def test_weak_passwords_rejected(client: AsyncClient, password: str) -> None:
    response = await client.post(
        f"{API}/auth/register",
        json={"email": "grace@example.com", "password": password, "full_name": "Grace Hopper"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_wrong_password_returns_401(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(
        f"{API}/auth/login", json={"email": "ada@example.com", "password": "WrongPass1"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_protected_route_requires_token(client: AsyncClient) -> None:
    response = await client.get(f"{API}/dashboard")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


async def test_refresh_rotation_and_replay_detection(client: AsyncClient) -> None:
    await register(client)
    original_cookie = client.cookies.get("sf_refresh")
    assert original_cookie

    refreshed = await client.post(f"{API}/auth/refresh")
    assert refreshed.status_code == 200
    rotated = client.cookies.get("sf_refresh")
    assert rotated and rotated != original_cookie

    # Replaying the rotated-away token revokes every session for that user.
    client.cookies.set("sf_refresh", original_cookie, path=f"{API}/auth")
    replay = await client.post(f"{API}/auth/refresh")
    assert replay.status_code == 401

    client.cookies.set("sf_refresh", rotated, path=f"{API}/auth")
    after_replay = await client.post(f"{API}/auth/refresh")
    assert after_replay.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    payload = await register(client)
    logout = await client.post(f"{API}/auth/logout", headers=auth_headers(payload))
    assert logout.status_code == 204
    assert (await client.post(f"{API}/auth/refresh")).status_code == 401


async def test_change_password_requires_current_password(client: AsyncClient) -> None:
    payload = await register(client)
    headers = auth_headers(payload)

    wrong = await client.post(
        f"{API}/users/me/password",
        headers=headers,
        json={"current_password": "NopeNope1", "new_password": "BrandNewPass1"},
    )
    assert wrong.status_code == 400

    changed = await client.post(
        f"{API}/users/me/password",
        headers=headers,
        json={"current_password": "CorrectHorse9", "new_password": "BrandNewPass1"},
    )
    assert changed.status_code == 200

    old_login = await client.post(
        f"{API}/auth/login", json={"email": "ada@example.com", "password": "CorrectHorse9"}
    )
    assert old_login.status_code == 401
    new_login = await client.post(
        f"{API}/auth/login", json={"email": "ada@example.com", "password": "BrandNewPass1"}
    )
    assert new_login.status_code == 200
