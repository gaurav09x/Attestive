"""Email transports: payload shape, failure handling and link contents."""

from __future__ import annotations

import logging

import pytest

from app.core import mailer
from app.core.config import Settings, settings
from app.core.mailer import EmailMessage, password_reset_email, send_email, verification_email

MESSAGE = EmailMessage(to="ada@example.com", subject="Hello", body="Body with a link")


@pytest.mark.asyncio
async def test_console_transport_logs_in_development(caplog) -> None:
    caplog.set_level(logging.INFO, logger="attestive.mail")
    assert settings.ENVIRONMENT == "development"
    assert await send_email(MESSAGE) is True
    assert "Body with a link" in caplog.text


@pytest.mark.asyncio
async def test_console_transport_suppresses_body_outside_development(
    caplog, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    caplog.set_level(logging.INFO, logger="attestive.mail")
    assert await send_email(MESSAGE) is False
    assert "Body with a link" not in caplog.text
    assert "body suppressed" in caplog.text


@pytest.mark.asyncio
async def test_disabled_transport_sends_nothing(caplog, monkeypatch) -> None:
    monkeypatch.setattr(settings, "EMAIL_DELIVERY", "disabled")
    caplog.set_level(logging.WARNING, logger="attestive.mail")
    assert await send_email(MESSAGE) is False
    assert "was not sent" in caplog.text


@pytest.mark.asyncio
async def test_resend_payload_and_failure(monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings, "EMAIL_DELIVERY", "resend")
    monkeypatch.setattr(settings, "EMAIL_API_KEY", "re_test_key")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Attestive <no-reply@example.com>")
    calls: list[tuple[str, dict, str]] = []

    async def fake_post(url: str, payload: dict, api_key: str) -> tuple[int, str]:
        calls.append((url, payload, api_key))
        return 200, ""

    monkeypatch.setattr(mailer, "_post_json", fake_post)
    assert await send_email(MESSAGE) is True
    url, payload, key = calls[0]
    assert url == mailer.RESEND_ENDPOINT
    assert key == "re_test_key"
    assert payload["to"] == ["ada@example.com"]
    assert payload["from"] == "Attestive <no-reply@example.com>"
    assert payload["text"] == "Body with a link"

    async def failing_post(url: str, payload: dict, api_key: str) -> tuple[int, str]:
        return 422, "invalid from address"

    monkeypatch.setattr(mailer, "_post_json", failing_post)
    caplog.set_level(logging.ERROR, logger="attestive.mail")
    assert await send_email(MESSAGE) is False
    assert "422" in caplog.text


@pytest.mark.asyncio
async def test_sendgrid_payload(monkeypatch) -> None:
    monkeypatch.setattr(settings, "EMAIL_DELIVERY", "sendgrid")
    monkeypatch.setattr(settings, "EMAIL_API_KEY", "SG.test")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Attestive <no-reply@example.com>")
    captured: dict = {}

    async def fake_post(url: str, payload: dict, api_key: str) -> tuple[int, str]:
        captured.update({"url": url, "payload": payload, "key": api_key})
        return 202, ""

    monkeypatch.setattr(mailer, "_post_json", fake_post)
    assert await send_email(MESSAGE) is True
    assert captured["url"] == mailer.SENDGRID_ENDPOINT
    payload = captured["payload"]
    assert payload["personalizations"][0]["to"][0]["email"] == "ada@example.com"
    assert payload["from"]["email"] == "no-reply@example.com"
    assert payload["content"][0]["value"] == "Body with a link"


@pytest.mark.asyncio
async def test_smtp_transport_builds_message(monkeypatch) -> None:
    monkeypatch.setattr(settings, "EMAIL_DELIVERY", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "apikey")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Attestive <no-reply@example.com>")

    class FakeSMTP:
        instances: list["FakeSMTP"] = []

        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.host = host
            self.port = port
            self.started_tls = False
            self.logged_in: tuple[str, str] | None = None
            self.message = None
            FakeSMTP.instances.append(self)

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *_args) -> bool:
            return False

        def ehlo(self) -> None:
            return None

        def starttls(self) -> None:
            self.started_tls = True

        def login(self, username: str, password: str) -> None:
            self.logged_in = (username, password)

        def send_message(self, message) -> None:  # type: ignore[no-untyped-def]
            self.message = message

    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    assert await send_email(MESSAGE) is True

    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.example.com", 587)
    assert smtp.started_tls is True
    assert smtp.logged_in == ("apikey", "secret")
    assert smtp.message["To"] == "ada@example.com"
    assert smtp.message["Subject"] == "Hello"
    assert "Body with a link" in smtp.message.get_content()


def test_links_carry_the_token() -> None:
    verify = verification_email("ada@example.com", "tok_verify")
    assert "/verify-email?token=tok_verify" in verify.body
    reset = password_reset_email("ada@example.com", "tok_reset")
    assert "/reset-password?token=tok_reset" in reset.body
    assert settings.APP_BASE_URL in reset.body


def test_production_requires_credentials_for_http_providers() -> None:
    production = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="x" * 48,
        COOKIE_SECURE=True,
        DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/attestive",
        APP_BASE_URL="https://attestive.example.com",
        EMAIL_DELIVERY="resend",
        EMAIL_API_KEY=None,
    )
    with pytest.raises(RuntimeError, match="EMAIL_API_KEY"):
        production.validate_for_runtime()

    smtp = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="x" * 48,
        COOKIE_SECURE=True,
        DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/attestive",
        APP_BASE_URL="https://attestive.example.com",
        EMAIL_DELIVERY="smtp",
        SMTP_HOST=None,
    )
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        smtp.validate_for_runtime()
