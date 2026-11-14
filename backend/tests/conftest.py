"""Test suite configuration: isolated SQLite database per test."""

from __future__ import annotations

import os

# Never call a live model from the test suite: roadmap notes fall back to the
# deterministic rationale, which is what these assertions describe.
os.environ["AI_ROADMAP_ENABLED"] = "false"
# Rate limiting is exercised explicitly by test_security_phase7; the functional
# suites must not compete for the auth budget of one shared test client.
os.environ["RATE_LIMIT_AUTH_PER_MINUTE"] = "10000"
os.environ["RATE_LIMIT_DEFAULT_PER_MINUTE"] = "10000"

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.seed import seed_catalog
from app.db.session import get_session
from app.main import app
from app.models import Base


@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await seed_catalog(session)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncClient]:
    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        http_client.session_factory = session_factory  # type: ignore[attr-defined]
        yield http_client
    app.dependency_overrides.clear()


async def register(
    client: AsyncClient, email: str = "ada@example.com", password: str = "CorrectHorse9"
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Ada Lovelace"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


ONBOARDING_PAYLOAD = {
    "education_level": "undergraduate",
    "experience_level": "beginner",
    "learning_style": "practical",
    "session_minutes": 30,
    "weekly_minutes_goal": 600,
    "career_goal": "backend_developer",
    "target_role": "Backend Engineer",
    "subject_slugs": ["python", "sql"],
    "prefers_projects": True,
    "prefers_theory_first": False,
}


async def onboard(client: AsyncClient, email: str = "ada@example.com") -> dict:
    payload = await register(client, email=email)
    response = await client.post(
        "/api/v1/users/me/onboarding",
        headers=auth_headers(payload),
        json=ONBOARDING_PAYLOAD,
    )
    assert response.status_code == 200, response.text
    return payload
