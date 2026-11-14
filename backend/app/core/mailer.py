"""Email delivery with pluggable transports.

`EMAIL_DELIVERY` selects the transport:

* ``console``  — development only; logs the message. Outside development the body
  (which contains a single-use link) is suppressed instead of logged.
* ``disabled`` — creates no delivery and says so.
* ``resend``   — HTTPS POST to Resend's transactional API.
* ``sendgrid`` — HTTPS POST to SendGrid's v3 mail send API.
* ``smtp``     — stdlib SMTP, optionally STARTTLS, no extra dependency.

Every transport returns False on failure and logs the reason. Callers treat
delivery as best effort: account creation and password-reset requests must not
fail because email is down, but a failure is never reported as a send.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MIMEMessage
from email.utils import parseaddr

import httpx

from app.core.config import settings

logger = logging.getLogger("attestive.mail")

RESEND_ENDPOINT = "https://api.resend.com/emails"
SENDGRID_ENDPOINT = "https://api.sendgrid.com/v3/mail/send"

HTTP_PROVIDERS = {"resend", "sendgrid"}
PROVIDERS = HTTP_PROVIDERS | {"smtp"}


@dataclass(slots=True)
class EmailMessage:
    to: str
    subject: str
    body: str


def has_provider() -> bool:
    """True when a transport that can actually reach a mailbox is configured."""
    return settings.EMAIL_DELIVERY in PROVIDERS


async def _post_json(url: str, payload: dict, api_key: str) -> tuple[int, str]:
    """Single HTTPS call. Kept separate so tests can stub the network boundary."""
    async with httpx.AsyncClient(timeout=settings.EMAIL_TIMEOUT_SECONDS) as client:
        response = await client.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
    return response.status_code, response.text[:400]


async def _send_resend(message: EmailMessage) -> bool:
    payload = {
        "from": settings.EMAIL_FROM,
        "to": [message.to],
        "subject": message.subject,
        "text": message.body,
    }
    status, body = await _post_json(RESEND_ENDPOINT, payload, settings.EMAIL_API_KEY or "")
    if 200 <= status < 300:
        return True
    logger.error("Resend rejected '%s' for %s: HTTP %s %s", message.subject, message.to, status, body)
    return False


async def _send_sendgrid(message: EmailMessage) -> bool:
    payload = {
        "personalizations": [{"to": [{"email": message.to}]}],
        "from": {"email": parseaddr(settings.EMAIL_FROM)[1] or settings.EMAIL_FROM},
        "subject": message.subject,
        "content": [{"type": "text/plain", "value": message.body}],
    }
    status, body = await _post_json(SENDGRID_ENDPOINT, payload, settings.EMAIL_API_KEY or "")
    if 200 <= status < 300:
        return True
    logger.error(
        "SendGrid rejected '%s' for %s: HTTP %s %s", message.subject, message.to, status, body
    )
    return False


def _send_smtp_sync(message: EmailMessage) -> None:
    mime = MIMEMessage()
    mime["From"] = settings.EMAIL_FROM
    mime["To"] = message.to
    mime["Subject"] = message.subject
    mime.set_content(message.body)

    with smtplib.SMTP(
        settings.SMTP_HOST or "localhost",
        settings.SMTP_PORT,
        timeout=settings.EMAIL_TIMEOUT_SECONDS,
    ) as client:
        client.ehlo()
        if settings.SMTP_STARTTLS:
            client.starttls()
            client.ehlo()
        if settings.SMTP_USERNAME:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        client.send_message(mime)


async def _send_smtp(message: EmailMessage) -> bool:
    try:
        # smtplib is blocking; keep the event loop free.
        await asyncio.to_thread(_send_smtp_sync, message)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("SMTP delivery of '%s' to %s failed: %s", message.subject, message.to, exc)
        return False


async def send_email(message: EmailMessage) -> bool:
    """Return True only when the message was handed to a transport that can deliver."""
    transport = settings.EMAIL_DELIVERY

    if transport == "disabled":
        logger.warning(
            "Email delivery is disabled; '%s' for %s was not sent.",
            message.subject,
            message.to,
        )
        return False

    if transport == "console":
        if settings.ENVIRONMENT == "development":
            logger.info(
                "EMAIL (console transport)\nTo: %s\nSubject: %s\n\n%s",
                message.to,
                message.subject,
                message.body,
            )
            return True
        # A reset link in a production log is a credential leak. Metadata only.
        logger.warning(
            "EMAIL (console transport, body suppressed outside development) to %s: %s. "
            "Configure a real provider (EMAIL_DELIVERY=resend|sendgrid|smtp).",
            message.to,
            message.subject,
        )
        return False

    if transport == "resend":
        return await _send_resend(message)
    if transport == "sendgrid":
        return await _send_sendgrid(message)
    if transport == "smtp":
        return await _send_smtp(message)

    logger.error("Unknown EMAIL_DELIVERY value %r; message was not sent.", transport)
    return False


def verification_email(to: str, token: str) -> EmailMessage:
    link = f"{settings.APP_BASE_URL.rstrip('/')}/verify-email?token={token}"
    return EmailMessage(
        to=to,
        subject="Verify your Attestive email",
        body=(
            "Confirm your email address to secure your account.\n\n"
            f"{link}\n\n"
            f"This link expires in {settings.VERIFY_TOKEN_TTL_HOURS} hours. "
            "If you did not create an account, ignore this message."
        ),
    )


def password_reset_email(to: str, token: str) -> EmailMessage:
    link = f"{settings.APP_BASE_URL.rstrip('/')}/reset-password?token={token}"
    return EmailMessage(
        to=to,
        subject="Reset your Attestive password",
        body=(
            "Use this link to choose a new password.\n\n"
            f"{link}\n\n"
            f"This link expires in {settings.RESET_TOKEN_TTL_MINUTES} minutes and can be used "
            "once. If you did not request a reset, ignore this message — your password is "
            "unchanged."
        ),
    )
