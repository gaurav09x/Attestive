"""Phase 6: career role maps, skill gaps, mock interviews and resume claims."""

from __future__ import annotations

import pytest

from sqlalchemy import select

from app.models.catalog import Skill
from app.models.user import User, UserSkill

from tests.conftest import auth_headers, onboard


@pytest.mark.asyncio
async def test_roles_list_and_gap_analysis(client) -> None:
    payload = await onboard(client)
    headers = auth_headers(payload)

    response = await client.get("/api/v1/career/roles", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["items"]) >= 6
    assert "does not guarantee employment" in body["disclaimer"]

    detail = await client.get("/api/v1/career/roles/backend_developer", headers=headers)
    assert detail.status_code == 200, detail.text
    role = detail.json()
    assert role["slug"] == "backend_developer"
    assert role["version"] == 1
    assert role["generated_by"] == "deterministic"
    assert len(role["skills"]) == 14
    assert role["skills"][0]["target"] > 0
    # A brand-new learner has self-reported priors only: no skill can be "met"
    # at the role target, and readiness must stay below 100.
    assert role["readiness_score"] < 100
    assert all(skill["status"] in {"met", "close", "missing"} for skill in role["skills"])
    assert role["recommendations"]
    assert role["portfolio_briefs"][0]["brief"]


@pytest.mark.asyncio
async def test_mock_interview_full_flow(client) -> None:
    payload = await onboard(client)
    headers = auth_headers(payload)

    start = await client.post(
        "/api/v1/career/interviews",
        headers=headers,
        json={"role_slug": "backend_developer"},
    )
    assert start.status_code == 201, start.text
    interview = start.json()
    assert interview["status"] == "in_progress"
    assert interview["total"] == 4
    assert all(question["answer"] is None for question in interview["questions"])
    interview_id = interview["id"]

    # Starting again resumes the same transcript instead of creating a duplicate.
    resumed = await client.post(
        "/api/v1/career/interviews",
        headers=headers,
        json={"role_slug": "backend_developer"},
    )
    assert resumed.status_code == 201
    assert resumed.json()["id"] == interview_id

    answers = [
        (
            "cursor keyset pagination with a stable sort key and a next cursor; "
            "offset pagination is slow at deep pages"
        ),
        (
            "read the explain analyze plan, add a composite index on user_id and created_at, "
            "and weigh write cost and selectivity"
        ),
        (
            "use a transaction so related writes commit atomically together; a long "
            "transaction holds locks and can block connections"
        ),
        (
            "a bug broke checkout, I read the logs to reproduce and debug it, then added a "
            "regression test to the release process"
        ),
    ]
    for question, answer in zip(interview["questions"], answers):
        response = await client.post(
            f"/api/v1/career/interviews/{interview_id}/responses",
            headers=headers,
            json={"question_id": question["id"], "answer": answer},
        )
        assert response.status_code == 200, response.text
        assert response.json()["questions"][0]["answer"] is not None

    premature = await client.post(
        f"/api/v1/career/interviews/{interview_id}/complete", headers=headers
    )
    # All four were answered, so completion is allowed and the rubric scores them.
    assert premature.status_code == 200, premature.text
    completed = premature.json()
    assert completed["status"] == "completed"
    assert completed["overall_score"] > 60
    assert completed["readiness"] in {"developing", "interview_ready"}
    assert completed["feedback"]
    # Model answers become visible only after completion.
    assert completed["questions"][0]["model_answer"]

    again = await client.post(
        f"/api/v1/career/interviews/{interview_id}/complete", headers=headers
    )
    assert again.status_code == 200
    assert again.json()["overall_score"] == completed["overall_score"]

    # Exactly one XP award and one achievement for the session.
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    # 120 XP for the interview + 150 for the achievement.
    assert me.json()["user"]["xp_total"] >= 270

    dashboard = await client.get("/api/v1/dashboard", headers=headers)
    codes = {item["code"] for item in dashboard.json()["achievements"]}
    assert "interview_ready" in codes


@pytest.mark.asyncio
async def test_interview_requires_all_answers(client) -> None:
    payload = await onboard(client)
    headers = auth_headers(payload)

    start = await client.post(
        "/api/v1/career/interviews",
        headers=headers,
        json={"role_slug": "software_engineer"},
    )
    assert start.status_code == 201
    interview = start.json()

    too_short = await client.post(
        f"/api/v1/career/interviews/{interview['id']}/responses",
        headers=headers,
        json={"question_id": interview["questions"][0]["id"], "answer": "no idea"},
    )
    assert too_short.status_code == 200
    assert too_short.json()["questions"][0]["score"] == 0

    finish = await client.post(
        f"/api/v1/career/interviews/{interview['id']}/complete", headers=headers
    )
    assert finish.status_code == 400
    assert finish.json()["error"]["code"] == "interview_incomplete"


@pytest.mark.asyncio
async def test_interview_ownership_and_resume_verify(client) -> None:
    owner = await onboard(client, email="owner@example.com")
    other = await onboard(client, email="other@example.com")

    start = await client.post(
        "/api/v1/career/interviews",
        headers=auth_headers(owner),
        json={"role_slug": "backend_developer"},
    )
    interview_id = start.json()["id"]

    forbidden = await client.get(
        f"/api/v1/career/interviews/{interview_id}", headers=auth_headers(other)
    )
    assert forbidden.status_code == 404

    claim = await client.post(
        "/api/v1/career/resume-skills",
        headers=auth_headers(owner),
        json={"label": "Testing", "claimed_level": "intermediate"},
    )
    assert claim.status_code == 201, claim.text
    body = claim.json()
    assert body["skill_slug"] == "testing"
    assert body["verified"] is False
    assert "unverified" in body["evidence"].lower() or "self-reported" in body["evidence"]

    # Record real evidence for the mapped skill, then the same claim is verified.
    async with client.session_factory() as session:  # type: ignore[attr-defined]
        user = (
            await session.execute(select(User).where(User.email == "owner@example.com"))
        ).scalar_one()
        skill = (
            await session.execute(select(Skill).where(Skill.slug == "testing"))
        ).scalar_one()
        # Onboarding created a self-reported prior for this skill; replace it with
        # real assessment evidence rather than inserting a duplicate.
        evidence = (
            await session.execute(
                select(UserSkill).where(
                    UserSkill.user_id == user.id, UserSkill.skill_id == skill.id
                )
            )
        ).scalar_one()
        evidence.proficiency = 72
        evidence.confidence = 80
        evidence.source = "assessment"
        await session.commit()

    listed = await client.get(
        "/api/v1/career/resume-skills", headers=auth_headers(owner)
    )
    assert listed.status_code == 200
    assert listed.json()["items"][0]["verified"] is True
    assert listed.json()["items"][0]["measured_proficiency"] == 72
