"""Unit tests for the automatic write read-back block."""

from __future__ import annotations

import pytest

from mammoth_cli.runtime.verify import with_verify


def test_non_dict_data_passes_through_unchanged() -> None:
    assert with_verify(["a", "b"]) == ["a", "b"]
    assert with_verify(None) is None


def test_a_normal_result_is_verified_with_no_needs_user() -> None:
    result = with_verify({"status": "done"})
    assert result["verify"] == {
        "verified": True,
        "state": "done",
        "warnings": [],
        "needs_user": None,
    }


@pytest.mark.parametrize(
    ("data", "state"),
    [
        ({"has_error": True, "status": "done"}, "done"),
        ({"status": "ERROR"}, "ERROR"),
        ({"job": {"status": "failed"}}, "done"),
        ({"pipeline_state": "ref_error"}, "ref_error"),
        ({"bake_ok": False}, "done"),
    ],
)
def test_each_failure_signal_marks_unverified_and_sets_needs_user(
    data: dict[str, object], state: str
) -> None:
    result = with_verify(data)
    assert result["verify"]["verified"] is False
    assert result["verify"]["needs_user"] == f"The change failed: {state}."


def test_rows_after_zero_with_rows_before_positive_needs_user() -> None:
    result = with_verify({"status": "done", "row_check": {"rows_before": 20, "rows_after": 0}})
    assert result["verify"]["rows_before"] == 20
    assert result["verify"]["rows_after"] == 0
    assert result["verify"]["needs_user"] == "The change left the view with no rows (was 20)."


def test_rows_check_omitted_when_no_row_or_join_check_present() -> None:
    result = with_verify({"status": "done"})
    assert "rows_before" not in result["verify"]
    assert "rows_after" not in result["verify"]


def test_low_match_rate_needs_user() -> None:
    result = with_verify({"status": "done", "join_check": {"match_rate": 0.43}})
    assert result["verify"]["needs_user"] == (
        "Only 43% of rows found a match in the join; the user should confirm before "
        "building on it."
    )


def test_high_match_rate_needs_no_user() -> None:
    result = with_verify({"status": "done", "join_check": {"match_rate": 0.95}})
    assert result["verify"]["needs_user"] is None


def test_warnings_collected_from_every_check_dict() -> None:
    result = with_verify(
        {
            "status": "done",
            "join_check": {"notes": ["a key repeats"], "match_rate": 0.95},
            "deliverable_check": {"warnings": [{"issue": "money_not_shown"}]},
        }
    )
    assert result["verify"]["warnings"] == [
        "a key repeats",
        "{'issue': 'money_not_shown'}",
    ]
