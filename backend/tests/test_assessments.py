from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.assessment import Question
from tests.conftest import auth_headers, onboard

API = "/api/v1"


async def _python_assessment(client: AsyncClient, headers: dict) -> dict:
    overview = await client.get(f"{API}/assessments", headers=headers)
    assert overview.status_code == 200, overview.text
    subjects = overview.json()["subjects"]
    python = next(item for item in subjects if item["subject_slug"] == "python")
    assert python["assessment_id"], "Python diagnostic should be seeded"
    assert python["question_count"] == 6
    return python


async def _correct_responses(
    session_factory: async_sessionmaker[AsyncSession], assessment_id: str
) -> list[dict]:
    async with session_factory() as session:
        questions = (
            await session.execute(
                select(Question)
                .where(Question.assessment_id == uuid.UUID(assessment_id))
                .order_by(Question.position)
            )
        ).scalars().all()
        payload = []
        for question in questions:
            key = question.correct_answer or {}
            if question.kind == "multiple_choice":
                response = {"index": key["index"]}
            elif question.kind == "short_answer":
                response = {"text": key["accepted"][0]}
            else:
                response = {"text": key["sample_answer"]}
            payload.append({"question_id": str(question.id), "response": response})
        return payload


async def test_diagnostic_is_available_and_hides_answer_keys(client: AsyncClient) -> None:
    auth = await onboard(client)
    headers = auth_headers(auth)
    python = await _python_assessment(client, headers)

    started = await client.post(
        f"{API}/assessments/{python['assessment_id']}/attempts", headers=headers
    )
    assert started.status_code == 201, started.text
    attempt = started.json()
    assert attempt["total_questions"] == 6
    assert attempt["answered_count"] == 0
    assert attempt["status"] == "in_progress"

    for question in attempt["questions"]:
        assert "correct_answer" not in question
        assert "explanation" not in question
        assert question["prompt"]

    resumed = await client.post(
        f"{API}/assessments/{python['assessment_id']}/attempts", headers=headers
    )
    assert resumed.json()["id"] == attempt["id"]


async def test_submit_rejects_unanswered_questions(client: AsyncClient) -> None:
    auth = await onboard(client)
    headers = auth_headers(auth)
    python = await _python_assessment(client, headers)
    attempt = (
        await client.post(
            f"{API}/assessments/{python['assessment_id']}/attempts", headers=headers
        )
    ).json()

    response = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/submit",
        headers=headers,
        json={"responses": []},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unanswered_questions"


async def test_perfect_attempt_updates_proficiency_and_creates_roadmap(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    auth = await onboard(client)
    headers = auth_headers(auth)
    python = await _python_assessment(client, headers)
    attempt = (
        await client.post(
            f"{API}/assessments/{python['assessment_id']}/attempts", headers=headers
        )
    ).json()

    responses = await _correct_responses(session_factory, python["assessment_id"])
    submitted = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/submit",
        headers=headers,
        json={"responses": responses},
    )
    assert submitted.status_code == 200, submitted.text
    result = submitted.json()
    assert result["score_percent"] == 100
    assert result["correct_count"] == 6
    assert result["weak_skills"] == []
    assert result["xp_awarded"] == 120
    assert result["roadmap_id"]

    # Proficiency moved from the 20% self-report seed to high-confidence evidence.
    skill_results = {item["slug"]: item for item in result["skill_results"]}
    assert skill_results["data-structures"]["proficiency"] >= 80
    assert skill_results["data-structures"]["confidence"] == 35

    review = await client.get(
        f"{API}/assessments/attempts/{attempt['id']}/review", headers=headers
    )
    assert review.status_code == 200
    review_body = review.json()
    assert len(review_body["questions"]) == 6
    assert all(item["is_correct"] for item in review_body["questions"])
    assert all(item["explanation"] for item in review_body["questions"])
    assert review_body["questions"][0]["correct_answer"]

    roadmaps = await client.get(f"{API}/roadmaps", headers=headers)
    assert roadmaps.status_code == 200
    paths = roadmaps.json()["items"]
    python_path = next(path for path in paths if path["subject_slug"] == "python")
    assert python_path["items_total"] >= 3
    assert python_path["generated_by"] == "deterministic"
    assert python_path["rationale"]
    assert python_path["items"][-1]["is_project"] is True

    dashboard = (await client.get(f"{API}/dashboard", headers=headers)).json()
    assert dashboard["current_path"]["id"] == python_path["id"]
    assert dashboard["stats"]["total_learning_minutes"] >= 1
    assert dashboard["level"]["xp_total"] == 120


async def test_wrong_answers_create_weak_skills_and_targeted_roadmap(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    auth = await onboard(client)
    headers = auth_headers(auth)
    python = await _python_assessment(client, headers)
    attempt = (
        await client.post(
            f"{API}/assessments/{python['assessment_id']}/attempts", headers=headers
        )
    ).json()

    async with session_factory() as session:
        questions = (
            await session.execute(
                select(Question)
                .where(Question.assessment_id == uuid.UUID(python["assessment_id"]))
                .order_by(Question.position)
            )
        ).scalars().all()
        responses = []
        for question in questions:
            if question.kind == "multiple_choice":
                wrong_index = 0 if (question.correct_answer or {}).get("index") != 0 else 1
                responses.append(
                    {"question_id": str(question.id), "response": {"index": wrong_index}}
                )
            else:
                responses.append(
                    {
                        "question_id": str(question.id),
                        "response": {"text": "I am not sure about this concept."},
                    }
                )

    submitted = await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/submit",
        headers=headers,
        json={"responses": responses},
    )
    assert submitted.status_code == 200, submitted.text
    result = submitted.json()
    assert result["score_percent"] == 0
    assert result["weak_skills"]
    assert result["xp_awarded"] == 80
    assert result["roadmap_id"]

    roadmaps = (await client.get(f"{API}/roadmaps", headers=headers)).json()["items"]
    python_path = next(path for path in roadmaps if path["subject_slug"] == "python")
    assert python_path["items_total"] >= 3
    assert python_path["title"] == "Python Programming roadmap"
    assert any(skill in python_path["rationale"] for skill in result["weak_skills"])


async def test_attempts_are_isolated_between_students(client: AsyncClient) -> None:
    owner = await onboard(client)
    python = await _python_assessment(client, auth_headers(owner))
    attempt = (
        await client.post(
            f"{API}/assessments/{python['assessment_id']}/attempts",
            headers=auth_headers(owner),
        )
    ).json()

    intruder = await onboard(client, email="intruder@example.com")
    other_headers = auth_headers(intruder)

    assert (
        await client.get(f"{API}/assessments/attempts/{attempt['id']}", headers=other_headers)
    ).status_code == 404
    assert (
        await client.post(
            f"{API}/assessments/attempts/{attempt['id']}/submit",
            headers=other_headers,
            json={"responses": []},
        )
    ).status_code == 404


async def test_roadmap_item_completion_is_idempotent(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    auth = await onboard(client)
    headers = auth_headers(auth)
    python = await _python_assessment(client, headers)
    attempt = (
        await client.post(
            f"{API}/assessments/{python['assessment_id']}/attempts", headers=headers
        )
    ).json()
    responses = await _correct_responses(session_factory, python["assessment_id"])
    await client.post(
        f"{API}/assessments/attempts/{attempt['id']}/submit",
        headers=headers,
        json={"responses": responses},
    )

    path = (await client.get(f"{API}/roadmaps", headers=headers)).json()["items"][0]
    first_item = path["items"][0]
    xp_before = (await client.get(f"{API}/auth/me", headers=headers)).json()["user"]["xp_total"]

    completed = await client.patch(
        f"{API}/roadmaps/{path['id']}/items/{first_item['id']}",
        headers=headers,
        json={"status": "completed"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["items"][0]["status"] == "completed"
    xp_after = (await client.get(f"{API}/auth/me", headers=headers)).json()["user"]["xp_total"]
    assert xp_after == xp_before + 40

    duplicate = await client.patch(
        f"{API}/roadmaps/{path['id']}/items/{first_item['id']}",
        headers=headers,
        json={"status": "completed"},
    )
    assert duplicate.status_code == 200
    xp_duplicate = (await client.get(f"{API}/auth/me", headers=headers)).json()["user"]["xp_total"]
    assert xp_duplicate == xp_after
