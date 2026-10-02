"""Timestamps from the backend are naive UTC; show them with an explicit offset."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def local_time(stamp: Any) -> str | None:
    """A timestamp (UTC if it has no offset) as ISO in this machine's timezone."""
    if not isinstance(stamp, str):
        return None
    try:
        moment = datetime.fromisoformat(stamp)
    except ValueError:
        return stamp
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone().isoformat(timespec="seconds")
