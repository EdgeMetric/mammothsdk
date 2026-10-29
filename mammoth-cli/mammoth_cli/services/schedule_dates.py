"""Whether a stored schedule has ended, judged the way the server judges it."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _as_utc(value: Any) -> datetime | None:
    """``value`` (an ISO string, naive meaning UTC) as an aware datetime, or None."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def until_has_passed(schedule: dict[str, Any], now: datetime | None = None) -> bool:
    """Whether the schedule's ``until`` is no longer ahead.

    Mirrors the server's ``ExportScheduleSpec._until_is_ahead``: ``until`` must be after
    now, and after ``start_at`` when ``start_now`` is false. An unreadable value counts as
    not passed, so the server decides.

    Args:
        schedule: A schedule or send window as the server stores it.
        now: The time to judge against (defaults to the current UTC time).

    Returns:
        True when ``until`` is set and is not after the later of now and a pending start.
    """
    until = _as_utc(schedule.get("until"))
    if until is None:
        return False
    floor = now or datetime.now(UTC)
    start = _as_utc(schedule.get("start_at"))
    if schedule.get("start_now", True) is False and start is not None:
        floor = max(floor, start)
    return until <= floor
