"""``until_has_passed`` judges an ``until`` the way the server's ``_until_is_ahead`` does."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from mammoth_cli.services.schedule_dates import until_has_passed

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("schedule", "passed"),
    [
        ({}, False),
        ({"until": "2026-10-30T00:00:00"}, False),
        ({"until": "2026-10-28T00:00:00"}, True),
        ({"until": "2026-10-29T12:00:00"}, True),
        ({"until": "2026-10-29T12:00:00+00:00"}, True),
        ({"until": "not a date"}, False),
        ({"until": 5}, False),
        # A pending start (start_now false) is the floor when it is later than now: an
        # until before it has passed, though it is still ahead of now.
        (
            {"until": "2026-11-05T00:00:00", "start_now": False, "start_at": "2026-12-01T00:00:00"},
            True,
        ),
        (
            {"until": "2026-11-05T00:00:00", "start_now": False, "start_at": "2026-11-01T00:00:00"},
            False,
        ),
        # With start_now true the start is ignored.
        (
            {"until": "2026-11-05T00:00:00", "start_now": True, "start_at": "2026-12-01T00:00:00"},
            False,
        ),
        # A start already in the past does not lower the floor below now.
        (
            {"until": "2026-10-28T00:00:00", "start_now": False, "start_at": "2026-01-01T00:00:00"},
            True,
        ),
    ],
)
def test_until_has_passed(schedule: dict[str, Any], passed: bool) -> None:
    assert until_has_passed(schedule, NOW) is passed
