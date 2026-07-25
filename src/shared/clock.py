"""UTC time helpers used for timestamps and audit metadata."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime | None = None) -> str:
    """Return an ISO-8601 UTC string with a stable ``Z`` suffix."""

    timestamp = value or utc_now()
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    normalized = timestamp.astimezone(timezone.utc)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")
