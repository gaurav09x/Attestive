from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_today(timezone_name: str | None) -> date:
    """Current calendar day in the student's timezone (UTC when unknown)."""
    try:
        tz = ZoneInfo(timezone_name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
