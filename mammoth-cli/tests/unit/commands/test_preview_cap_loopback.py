"""The preview cap note reads the draft's source list over the real SDK client (#356).

The server's source list carries ``has_more`` (set when a read stopped at its limit, so
``row_count`` is a floor). A source list that cannot be read must show as unchecked, not as
"not capped".
"""

# ruff: noqa: F811 -- the fixtures are imported and then named as test parameters

from __future__ import annotations

from mammoth_cli.services.draft_report import with_preview_cap
from mammoth_cli.services.sdk_service import SdkMammothService
from tests.unit.commands.loopback_service import (
    API,
    PROJECT,
    Recorder,
    server,  # noqa: F401
    service,  # noqa: F401
)

SOURCES = f"{API}/projects/{PROJECT}/connector-drafts/9/sources"
PREVIEW = {"columns": ["a"], "rows": [{"a": 1}] * 10, "row_count": 10}


def test_a_short_preview_of_a_bigger_source_is_marked_capped(
    service: SdkMammothService, server: Recorder
) -> None:
    server.answers[("GET", SOURCES)] = {
        "sources": [{"id": "s19", "row_count": 100, "has_more": True, "columns": []}]
    }

    out = with_preview_cap(service, 9, "s19", 100, PREVIEW)

    assert out["capped"] is True
    assert out["limit_applied"] == 10
    assert out["source_row_count"] == 100
    assert "cap_unchecked" not in out


def test_a_source_list_that_cannot_be_read_says_the_cap_was_not_checked(
    service: SdkMammothService, server: Recorder
) -> None:
    # No answer is set, so the loopback server refuses the read.
    out = with_preview_cap(service, 9, "s19", 100, PREVIEW)

    assert "capped" not in out
    assert out["cap_unchecked"]
    assert out["rows"] == PREVIEW["rows"]


def test_a_preview_that_met_its_limit_reads_nothing(
    service: SdkMammothService, server: Recorder
) -> None:
    assert with_preview_cap(service, 9, "s19", 10, PREVIEW) == PREVIEW
    assert server.requests == []
