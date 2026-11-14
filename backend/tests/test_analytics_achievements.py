"""Phase 5 tests: analytics aggregation and idempotent achievement unlocks."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.time import utc_now
from app.models.learning import LearningActivity
from app.models.user import User, UserSkill
from app.services.achievements import evaluate_achievements
from tests.conftest import auth_headers, onboard

API = "/api/v1"


async def _complete_python_diagnostic(client: AsyncClient, headers: dict) -> dict:
    overview = await client.get(f"{API}/assessments", headers=headers)
    subject = next(
        item for item in overview.json()["subjects"] if item["subject_slug"] == "python"
    )
    attempt = await client.post(
        f"{API}/assessments/{subject['assessment_id']}/attempts", headers=headers
    )
    assert attempt.status_code == 201, attempt.text
    attempt_body = attempt.json()

    responses = []
    for question in attempt_body["questions"]:
        if question["kind"] == "multiple_choice":
            answer = {"index": 0}
        else:
            answer = {"text": "A list is an ordered mutable sequence of values."}
        responses.append({"question_id": question["id"], "response": answer})

    submit = await client.post(
        f"{API}/assessments/attempts/{attempt_body['id']}/submit",
        headers=headers,
        json={"responses": responses},
    )
    assert submit.status_code == 200, submit.text
    return submit.json()


async def test_analytics_empty_for_new_student(client: AsyncClient) -> None:
    headers = auth_headers(await onboard(client))

    response = await client.get(f"{API}/analytics/overview", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["range_days"] == 30
    assert len(body["activity"]) == 30
    assert body["totals"]["minutes"] == 0
    assert body["totals"]["assessments_completed"] == 0
    assert body["totals"]["streak_days"] == 0
    assert body["assessment_trend"] == []
    assert body["revision_suggestions"]


async def test_analytics_reflects_real_attempt_and_activity(client: AsyncClient) -> None:
    headers = auth_headers(await onboard(client))
    result = await _complete_python_diagnostic(client, headers)
    assert "achievements_unlocked" in result

    response = await client.get(f"{API}/analytics/overview", headers=headers)
    body = response.json()

    assert body["totals"]["assessments_completed"] == 1
    assert body["totals"]["minutes"] >= 1
    assert body["totals"]["streak_days"] == 1
    assert len(body["assessment_trend"]) == 1
    assert body["assessment_trend"][0]["subject_name"] == "Python Programming"
    assert body["study_by_kind"][0]["kind"] == "assessment"
    assert body["subjects"], "measured proficiency should produce subject insights"
    assert sum(point["minutes"] for point in body["activity"]) == body["totals"]["minutes"]


async def test_achievements_unlock_once(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    payload = await onboard(client)
    headers = auth_headers(payload)

    async with session_factory() as session:
        user = await session.get(User, uuid.UUID(payload["user"]["id"]))
        assert user is not None

        today = date.today()
        for offset in range(3):
            session.add(
                LearningActivity(
                    user_id=user.id,
                    kind="lesson",
                    minutes=20,
                    xp_awarded=0,
                    occurred_on=today - timedelta(days=offset),
                    occurred_at=utc_now(),
                )
            )

        skills = (
            await session.execute(
                select(UserSkill).where(UserSkill.user_id == user.id).limit(5)
            )
        ).scalars().all()
        assert len(skills) == 5, "onboarding seeds at least five self-reported skills"
        for skill in skills:
            skill.proficiency = 80
        await session.flush()

        unlocked = await evaluate_achievements(session, user, today=today)
        await session.commit()

        assert "streak_three" in unlocked
        assert "skill_builder" in unlocked
        assert "streak_seven" not in unlocked

        xp_after_first = user.xp_total
        assert xp_after_first >= 250  # 50 for the streak, 200 for five skills

        again = await evaluate_achievements(session, user, today=today)
        await session.commit()
        assert again == []
        assert user.xp_total == xp_after_first

    analytics = await client.get(f"{API}/analytics/overview", headers=headers)
    body = analytics.json()
    assert body["totals"]["streak_days"] == 3
    assert body["totals"]["minutes"] == 60

    dashboard = await client.get(f"{API}/dashboard", headers=headers)
    unlocked_codes = {item["code"] for item in dashboard.json()["achievements"]}
    assert {"streak_three", "skill_builder"} <= unlocked_codes
