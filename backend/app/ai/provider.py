"""Model provider abstraction.

One small interface for the agents in `app.ai`: plain-text completion for the
tutor and JSON completion for the roadmap agent. Every call is best-effort — a
missing provider, an unreachable model or malformed output returns None so the
callers can fall back or report the AI as unavailable instead of inventing
content.

Two adapters are implemented: local Ollama (development) and any
OpenAI-compatible hosted chat-completions API (production), selected with
`AI_PROVIDER`. The SDK is not used; the HTTP shape is small and `httpx` is
already a dependency.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelProvider(Protocol):
    name: str
    model: str

    async def available(self) -> bool: ...

    async def list_models(self) -> list[str] | None: ...

    async def complete_text(
        self, system: str, prompt: str, timeout: int | None = None
    ) -> str | None: ...

    async def complete_json(
        self,
        system: str,
        prompt: str,
        timeout: int | None = None,
        format_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None: ...


class OllamaProvider:
    """Local Ollama chat completions, text or schema-constrained JSON."""

    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def available(self) -> bool:
        return (await self.list_models()) is not None

    async def list_models(self) -> list[str] | None:
        """Installed model names, or None when the provider cannot be reached."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Ollama unreachable: %s", exc)
            return None
        models = body.get("models")
        if not isinstance(models, list):
            return None
        return [
            entry["name"]
            for entry in models
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        ]

    def has_model(self, installed: list[str]) -> bool:
        base = self.model.split(":")[0]
        return any(
            name == self.model or name.split(":")[0] == base for name in installed
        )

    def _payload(
        self, system: str, prompt: str, *, json_format: dict[str, Any] | str | None,
        temperature: float, num_predict: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            # Thinking models otherwise spend the whole token budget on hidden
            # reasoning and return an empty message; this keeps the answer.
            "think": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if json_format:
            payload["format"] = json_format
        return payload

    async def complete_text(
        self, system: str, prompt: str, timeout: int | None = None
    ) -> str | None:
        payload = self._payload(
            system, prompt, json_format=None, temperature=0.4, num_predict=700
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout or settings.OLLAMA_TIMEOUT_SECONDS
            ) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Ollama text completion unavailable: %s", exc)
            return None
        content = body.get("message", {}).get("content", "")
        if not isinstance(content, str):
            return None
        text = content.strip()
        return text or None

    async def complete_json(
        self,
        system: str,
        prompt: str,
        timeout: int | None = None,
        format_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        payload = self._payload(
            system,
            prompt,
            json_format=format_schema or "json",
            temperature=0.2,
            num_predict=300,
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout or settings.ROADMAP_AI_TIMEOUT_SECONDS
            ) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
            content = body.get("message", {}).get("content", "")
            if not isinstance(content, str) or not content.strip():
                return None
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            # Expected when the configured model is not pulled; callers fall back.
            logger.info("Ollama JSON completion unavailable: %s", exc)
            return None


async def _post_json(
    url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float
) -> tuple[int, Any]:
    """One HTTPS call returning (status, parsed body or parsed error text).

    Kept at module level so tests can stub the network boundary without a live
    provider account.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload, headers=headers)
    try:
        body = response.json()
    except ValueError:
        body = response.text[:500]
    return response.status_code, body


class OpenAICompatibleProvider:
    """Hosted chat completions using the OpenAI request/response shape."""

    name = "openai"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.model = model or settings.OPENAI_MODEL
        self.api_key = api_key or settings.OPENAI_API_KEY or ""

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def available(self) -> bool:
        return bool(self.api_key) and (await self.list_models()) is not None

    async def list_models(self) -> list[str] | None:
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models", headers=self._headers
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Hosted model provider unreachable: %s", exc)
            return None
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            return None
        return [
            entry["id"]
            for entry in data
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        ]

    def _payload(
        self,
        system: str,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    async def _chat(
        self, payload: dict[str, Any], timeout: float
    ) -> str | None:
        status, body = await _post_json(
            f"{self.base_url}/chat/completions", payload, self._headers, timeout
        )
        if not 200 <= status < 300:
            logger.info("Hosted model rejected the request: HTTP %s %s", status, body)
            return None
        if not isinstance(body, dict):
            return None
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            return None
        text = content.strip()
        return text or None

    async def complete_text(
        self, system: str, prompt: str, timeout: int | None = None
    ) -> str | None:
        payload = self._payload(
            system, prompt, temperature=0.4, max_tokens=700, json_mode=False
        )
        return await self._chat(
            payload, timeout or settings.OPENAI_TIMEOUT_SECONDS
        )

    async def complete_json(
        self,
        system: str,
        prompt: str,
        timeout: int | None = None,
        format_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        del format_schema  # JSON mode is supported; per-field schemas are not portable
        payload = self._payload(
            system, prompt, temperature=0.2, max_tokens=400, json_mode=True
        )
        content = await self._chat(
            payload, timeout or settings.ROADMAP_AI_TIMEOUT_SECONDS
        )
        if not content:
            return None
        # Some providers wrap JSON in a fenced block despite JSON mode.
        if content.startswith("```"):
            content = content.strip("`")
            content = content.removeprefix("json").strip()
        try:
            parsed = json.loads(content)
        except ValueError:
            logger.info("Hosted model returned non-JSON output")
            return None
        return parsed if isinstance(parsed, dict) else None


def get_provider() -> ModelProvider | None:
    if settings.AI_PROVIDER == "disabled":
        return None
    if settings.AI_PROVIDER == "openai":
        return OpenAICompatibleProvider()
    return OllamaProvider()
