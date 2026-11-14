from __future__ import annotations

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.gamification import XPTransaction
from app.models.learning import LearningActivity
from app.models.user import LearningPreference, User, UserProfile
from tests.conftest import auth_headers, register

API = "/api/v1"

ONBOARDING = {
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


async def test_catalog_lists_seeded_subjects(client: AsyncClient) -> None:
    response = await client.get(f"{API}/catalog/subjects")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    slugs = {item["slug"] for item in body["items"]}
    assert {"python", "sql", "dsa"} <= slugs

    skills = await client.get(f"{API}/catalog/subjects/python/skills")
    assert skills.status_code == 200
    assert len(skills.json()) == 8


async def test_onboarding_persists_profile_preferences_and_skills(client: AsyncClient) -> None:
    payload = await register(client)
    response = await client.post(
        f"{API}/users/me/onboarding", headers=auth_headers(payload), json=ONBOARDING
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["onboarding_completed"] is True
    assert {subject["slug"] for subject in body["interests"]} == {"python", "sql"}
    assert len(body["skills"]) == 15  # 8 Python + 7 SQL skills, self-reported
    assert all(skill["source"] == "self_report" for skill in body["skills"])


async def test_onboarding_rejects_unknown_subject(client: AsyncClient) -> None:
    payload = await register(client)
    response = await client.post(
        f"{API}/users/me/onboarding",
        headers=auth_headers(payload),
        json={**ONBOARDING, "subject_slugs": ["python", "astrophysics"]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_subject"


async def test_fresh_dashboard_has_real_zeros(client: AsyncClient) -> None:
    payload = await register(client)
    await client.post(f"{API}/users/me/onboarding", headers=auth_headers(payload), json=ONBOARDING)

    response = await client.get(f"{API}/dashboard", headers=auth_headers(payload))
    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["total_learning_minutes"] == 0
    assert body["stats"]["skills_acquired"] == 0
    assert body["user"]["streak_days"] == 0
    assert body["level"]["level"] == 1
    assert body["weekly_goal"]["target_minutes"] == 600
    assert body["current_path"] is None
    assert len(body["activity_series"]) == 7
    assert all(day["minutes"] == 0 for day in body["activity_series"])


async def test_dashboard_reflects_recorded_activity(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    payload = await register(client)
    headers = auth_headers(payload)
    await client.post(f"{API}/users/me/onboarding", headers=headers, json=ONBOARDING)

    today = datetime.now(timezone.utc).date()
    async with session_factory() as session:
        user = (await session.execute(select(User))).scalar_one()
        session.add_all(
            [
                LearningActivity(
                    user_id=user.id,
                    kind="lesson",
                    minutes=45,
                    xp_awarded=40,
                    occurred_on=today,
                ),
                LearningActivity(
                    user_id=user.id,
                    kind="tutor",
                    minutes=25,
                    xp_awarded=10,
                    occurred_on=today - timedelta(days=1),
                ),
            ]
        )
        session.add(
            XPTransaction(user_id=user.id, amount=600, reason="test_seed", source_type="test")
        )
        user.xp_total = 600
        await session.commit()

    response = await client.get(f"{API}/dashboard", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["total_learning_minutes"] == 70
    assert body["user"]["streak_days"] == 2
    assert body["level"]["level"] == 2
    assert body["weekly_goal"]["completed_minutes"] >= 0
    assert sum(day["minutes"] for day in body["activity_series"]) == 70


async def test_profile_update_and_validation(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    payload = await register(client)
    headers = auth_headers(payload)

    response = await client.patch(
        f"{API}/users/me",
        headers=headers,
        json={"headline": "Learning backend engineering", "weekly_minutes_goal": 420},
    )
    assert response.status_code == 200
    assert response.json()["profile"]["headline"] == "Learning backend engineering"

    invalid = await client.patch(
        f"{API}/users/me", headers=headers, json={"weekly_minutes_goal": 5}
    )
    assert invalid.status_code == 422

    async with session_factory() as session:
        profile = (await session.execute(select(UserProfile))).scalar_one()
        prefs = (await session.execute(select(LearningPreference))).scalars().all()
    assert profile.weekly_minutes_goal == 420
    assert prefs == []  # preferences are created during onboarding
