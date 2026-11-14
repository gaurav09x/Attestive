"""Hosted (OpenAI-compatible) model provider: payloads, parsing and selection."""

from __future__ import annotations

import pytest

from app.ai import provider as provider_module
from app.ai.provider import OpenAICompatibleProvider, get_provider
from app.core.config import settings


def _provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://api.example.com/v1/",
        model="glm-4-flash",
        api_key="test-key",
    )


@pytest.mark.asyncio
async def test_complete_text_builds_openai_request(monkeypatch) -> None:
    captured: dict = {}

    async def fake_post(url: str, payload: dict, headers: dict, timeout: float):
        captured.update(url=url, payload=payload, headers=headers, timeout=timeout)
        return 200, {"choices": [{"message": {"content": "  Explanation here  "}}]}

    monkeypatch.setattr(provider_module, "_post_json", fake_post)
    reply = await _provider().complete_text("You are a tutor.", "Explain loops.")

    assert reply == "Explanation here"
    assert captured["url"] == "https://api.example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "glm-4-flash"
    assert captured["payload"]["messages"][0] == {
        "role": "system",
        "content": "You are a tutor.",
    }
    assert captured["payload"]["messages"][1]["content"] == "Explain loops."
    assert "response_format" not in captured["payload"]


@pytest.mark.asyncio
async def test_complete_json_parses_and_unwraps_fences(monkeypatch) -> None:
    async def fake_post(url: str, payload: dict, headers: dict, timeout: float):
        assert payload["response_format"] == {"type": "json_object"}
        return 200, {
            "choices": [{"message": {"content": '```json\n{"rationale": "because"}\n```'}}]
        }

    monkeypatch.setattr(provider_module, "_post_json", fake_post)
    parsed = await _provider().complete_json("sys", "plan", format_schema={"type": "object"})
    assert parsed == {"rationale": "because"}


@pytest.mark.asyncio
async def test_provider_failures_return_none(monkeypatch, caplog) -> None:
    async def rejected(url: str, payload: dict, headers: dict, timeout: float):
        return 429, {"error": {"message": "rate limited"}}

    monkeypatch.setattr(provider_module, "_post_json", rejected)
    assert await _provider().complete_text("sys", "prompt") is None

    async def malformed(url: str, payload: dict, headers: dict, timeout: float):
        return 200, {"choices": [{"message": {"content": "not json"}}]}

    monkeypatch.setattr(provider_module, "_post_json", malformed)
    assert await _provider().complete_json("sys", "prompt") is None

    async def empty(url: str, payload: dict, headers: dict, timeout: float):
        return 200, {"choices": []}

    monkeypatch.setattr(provider_module, "_post_json", empty)
    assert await _provider().complete_text("sys", "prompt") is None


@pytest.mark.asyncio
async def test_available_requires_a_key() -> None:
    without_key = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1", model="m", api_key=""
    )
    assert await without_key.available() is False


def test_get_provider_selects_adapter(monkeypatch) -> None:
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    assert isinstance(get_provider(), OpenAICompatibleProvider)

    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    assert get_provider() is not None
    assert get_provider().name == "ollama"  # type: ignore[union-attr]

    monkeypatch.setattr(settings, "AI_PROVIDER", "disabled")
    assert get_provider() is None


@pytest.mark.asyncio
async def test_tutor_status_names_a_hosted_provider(monkeypatch) -> None:
    from app.services import tutor_service

    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    status = await tutor_service.tutor_status()
    assert status.available is False
    assert "OPENAI_BASE_URL" in status.message or "OPENAI_API_KEY" in status.message
