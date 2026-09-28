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
        "reason": None,
        "needs_user": None,
    }


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        ({"has_error": True, "status": "done"}, "the operation reported an error"),
        ({"status": "ERROR"}, "the operation failed"),
        ({"job": {"status": "failed"}}, "the operation failed"),
        ({"pipeline_state": "ref_error"}, "the pipeline reported an error"),
        ({"bake_ok": False}, "the dashboard did not bake"),
        (
            {"status": "processing"},
            "the change was accepted but has not finished; read the view before building on it",
        ),
    ],
)
def test_each_failure_signal_marks_unverified_with_a_reason_and_no_needs_user(
    data: dict[str, object], reason: str
) -> None:
    result = with_verify(data)
    assert result["verify"]["verified"] is False
    assert result["verify"]["reason"] == reason
    assert result["verify"]["needs_user"] is None


def test_unreadable_row_count_is_a_failure_not_a_needs_user() -> None:
    result = with_verify({"status": "done", "row_check": {"rows_before": 20, "rows_after": None}})
    assert result["verify"]["verified"] is False
    assert result["verify"]["needs_user"] is None
    assert result["verify"]["reason"] == (
        "the row count after the change could not be read; read the view before building on it"
    )


def test_append_that_did_not_grow_is_a_failure_not_a_needs_user() -> None:
    result = with_verify(
        {
            "status": "done",
            "row_check": {
                "rows_before": 60,
                "rows_after": 60,
                "expected_row_increase": True,
            },
        }
    )
    assert result["verify"]["verified"] is False
    assert result["verify"]["needs_user"] is None
    assert result["verify"]["reason"] == "the append did not add rows"


def test_changed_false_is_a_no_op_not_a_needs_user() -> None:
    result = with_verify(
        {
            "changed": False,
            "bake_ok": False,
            "message": "I didn't change anything because the request was unclear.",
        }
    )
    assert result["verify"]["verified"] is False
    assert result["verify"]["needs_user"] is None
    assert result["verify"]["reason"] == (
        "nothing changed: I didn't change anything because the request was unclear."
    )


def test_changed_false_message_is_truncated_to_200_chars() -> None:
    long_message = "x" * 300
    result = with_verify({"changed": False, "message": long_message})
    assert result["verify"]["reason"] == f"nothing changed: {'x' * 200}"


def test_staged_status_is_verified_with_no_rows_and_a_reason() -> None:
    result = with_verify({"status": "staged"})
    assert result["verify"] == {
        "verified": True,
        "state": "staged",
        "warnings": [],
        "reason": "staged in draft; not applied until the draft is submitted",
        "needs_user": None,
    }


def test_pipeline_error_with_unknown_execution_state_is_a_failed_read() -> None:
    """``execution_state: "unknown"`` means the settle step's own read of the
    pipeline failed or came back malformed -- fail loud: that is never
    reported as verified just because nothing named an error.
    """
    result = with_verify(
        {"status": "done", "pipeline_error": {"execution_state": "unknown", "read_error": "boom"}}
    )
    assert result["verify"]["verified"] is False
    assert result["verify"]["needs_user"] is None
    assert result["verify"]["reason"] == (
        "the pipeline state after this change could not be read; read the view "
        "before building on it"
    )


def test_pipeline_error_with_a_real_execution_state_reports_task_and_code() -> None:
    result = with_verify(
        {
            "status": "done",
            "pipeline_error": {
                "execution_state": "runtime_error",
                "task_id": 42,
                "error_code": 7000,
            },
        }
    )
    assert result["verify"]["verified"] is False
    assert result["verify"]["needs_user"] is None
    assert "42" in result["verify"]["reason"]
    assert "7000" in result["verify"]["reason"]


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
