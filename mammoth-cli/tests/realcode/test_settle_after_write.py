"""A row-reducing write that removed nothing, or lacks a before-count, is never verified."""

from __future__ import annotations

from mammoth_cli.runtime.verify import with_verify


def test_a_row_reducing_write_that_removed_nothing_is_flagged_unchanged() -> None:
    check = {"rows_before": 50, "rows_after": 50, "expected_row_decrease": True}
    verify = with_verify({"status": "done", "row_check": check})["verify"]
    assert verify["changed"] is False
    assert verify["reason"] == "no rows removed (50 -> 50)"


def test_a_row_reducing_write_with_an_unread_before_count_is_flagged() -> None:
    check = {"rows_before": None, "rows_after": 50, "expected_row_decrease": True}
    verify = with_verify({"status": "done", "row_check": check})["verify"]
    assert verify["verified"] is False
    assert "before" in verify["reason"]
