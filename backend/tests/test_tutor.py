"""Tutor API tests.

The model is faked throughout: these tests assert the platform's own rules
(ownership, hint levels, persistence, honest failure) and never call a live LLM.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.ai import teaching_agent
from app.services import tutor_service
from tests.conftest import auth_headers, onboard

API = "/api/v1"


class FakeProvider:
    name = "ollama"
    model = "fake-tutor:1b"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def available(self) -> bool:
        return True

    async def list_models(self) -> list[str]:
        return [self.model]

    def has_model(self, installed: list[str]) -> bool:
        return self.model in installed

    async def complete_text(self, system: str, prompt: str, timeout: int | None = None) -> str:
        self.prompts.append(prompt)
        return (
            "A Python list is an ordered, mutable sequence. `xs = [1, 2]` then "
            "`xs.append(3)` updates that same object in place. What do you expect "
            "`len(xs)` to be after the call?"
        )

    async def complete_json(self, *args, **kwargs):  # pragma: no cover - unused
        return None


@pytest.fixture
def fake_provider(monkeypatch) -> FakeProvider:
    provider = FakeProvider()
    monkeypatch.setattr(teaching_agent, "get_provider", lambda: provider)
    monkeypatch.setattr(tutor_service, "get_provider", lambda: provider)
    return provider


async def _python_subject_id(client: AsyncClient) -> str:
    response = await client.get(f"{API}/catalog/subjects?limit=50")
    assert response.status_code == 200, response.text
    return next(item["id"] for item in response.json()["items"] if item["slug"] == "python")


async def _conversation(client: AsyncClient, headers: dict) -> dict:
    response = await client.post(
        f"{API}/tutor/conversations",
        headers=headers,
        json={"subject_id": await _python_subject_id(client), "topic": "List basics"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_tutor_status_reports_ready_model(client: AsyncClient, fake_provider) -> None:
    headers = auth_headers(await onboard(client))

    response = await client.get(f"{API}/tutor/status", headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["available"] is True
    assert body["provider"] == "ollama"
    assert body["model"] == "fake-tutor:1b"
    assert "ready" in body["message"]


async def test_conversation_and_message_flow(client: AsyncClient, fake_provider) -> None:
    headers = auth_headers(await onboard(client))
    conversation = await _conversation(client, headers)
    assert conversation["message_count"] == 0
    assert conversation["subject_slug"] == "python"
    assert conversation["title"] == "List basics"

    response = await client.post(
        f"{API}/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "What is a Python list?", "mode": "explain"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert [message["role"] for message in body["messages"]] == ["user", "assistant"]
    assert body["messages"][0]["provider"] == "student"
    assert body["messages"][1]["provider"] == "ollama:fake-tutor:1b"
    assert body["messages"][1]["sources"], "reply should cite retrieved curriculum"
    assert body["suggestions"]
    assert body["conversation"]["message_count"] == 2

    detail = await client.get(
        f"{API}/tutor/conversations/{conversation['id']}", headers=headers
    )
    assert detail.status_code == 200
    assert detail.json()["message_count"] == 2

    listing = await client.get(f"{API}/tutor/conversations", headers=headers)
    assert [item["id"] for item in listing.json()["items"]] == [conversation["id"]]

    # The prompt really carried the student's context, not just their message.
    prompt = fake_provider.prompts[-1]
    assert "Python Programming" in prompt
    assert "What is a Python list?" in prompt
    assert "Relevant curriculum:" in prompt


async def test_hint_mode_escalates_one_level_at_a_time(
    client: AsyncClient, fake_provider
) -> None:
    headers = auth_headers(await onboard(client))
    conversation = await _conversation(client, headers)

    first = await client.post(
        f"{API}/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "How do I remove duplicates from a list?", "mode": "hint"},
    )
    second = await client.post(
        f"{API}/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "Still stuck, another hint?", "mode": "hint"},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["messages"][1]["hint_level"] == 1
    assert second.json()["messages"][1]["hint_level"] == 2


async def test_conversations_are_private(client: AsyncClient, fake_provider) -> None:
    owner = await onboard(client, email="ada@example.com")
    conversation = await _conversation(client, auth_headers(owner))

    other = await onboard(client, email="grace@example.com")
    headers = auth_headers(other)

    read = await client.get(
        f"{API}/tutor/conversations/{conversation['id']}", headers=headers
    )
    write = await client.post(
        f"{API}/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "Let me read this conversation."},
    )
    listing = await client.get(f"{API}/tutor/conversations", headers=headers)

    assert read.status_code == 404
    assert write.status_code == 404
    assert listing.json()["items"] == []


async def test_tutor_reports_unavailable_instead_of_inventing_reply(
    client: AsyncClient, fake_provider, monkeypatch
) -> None:
    headers = auth_headers(await onboard(client))
    conversation = await _conversation(client, headers)

    monkeypatch.setattr(teaching_agent, "get_provider", lambda: None)
    monkeypatch.setattr(tutor_service, "get_provider", lambda: None)

    status = await client.get(f"{API}/tutor/status", headers=headers)
    assert status.json()["available"] is False

    response = await client.post(
        f"{API}/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "Teach me something useful."},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_unavailable"

    detail = await client.get(
        f"{API}/tutor/conversations/{conversation['id']}", headers=headers
    )
    assert detail.json()["messages"] == [], "a failed reply must not be stored"


async def test_message_validation_and_delete(client: AsyncClient, fake_provider) -> None:
    headers = auth_headers(await onboard(client))
    conversation = await _conversation(client, headers)
    url = f"{API}/tutor/conversations/{conversation['id']}"

    too_short = await client.post(
        f"{url}/messages", headers=headers, json={"content": "a"}
    )
    assert too_short.status_code == 422

    removed = await client.delete(url, headers=headers)
    assert removed.status_code == 204

    gone = await client.get(url, headers=headers)
    assert gone.status_code == 404


async def test_tutor_requires_authentication(client: AsyncClient) -> None:
    response = await client.get(f"{API}/tutor/conversations")
    assert response.status_code == 401
