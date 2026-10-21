"""``view data get`` says ``truncated`` only when rows remain beyond the page it returned."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view.data_read import _close_last_page


def _page(*, offset: int, returned: int, total: int) -> dict[str, Any]:
    """A page of a 3-row view as ``_trim_rows`` leaves it for a full page of ``limit`` 2."""
    return {
        "rows_returned": returned,
        "rows_total_in_page": returned,
        "truncated": returned == 2,
        "more_rows_may_exist": "The page is full; read the next page with offset.",
        "paging": {"count": returned, "limit": 2, "offset": offset, "total": total},
    }


def test_a_full_page_that_ends_at_the_last_row_is_not_truncated() -> None:
    closed = _close_last_page(_page(offset=2, returned=2, total=3), 2)
    assert closed["truncated"] is False
    assert "more_rows_may_exist" not in closed


def test_a_full_page_with_rows_after_it_stays_truncated() -> None:
    kept = _close_last_page(_page(offset=1, returned=2, total=3), 1)
    assert kept["truncated"] is True
    assert "more_rows_may_exist" in kept
