"""Unit tests for the automatic write read-back block."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    service = FakeMammothService()

    def _build(auth: Any, **kwargs: Any) -> FakeMammothService:
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    return service


def test_non_dict_data_passes_through_unchanged() -> None:
    assert with_verify(["a", "b"]) == ["a", "b"]
    assert with_verify(None) is None


def test_a_card_field_on_the_result_is_mirrored_into_verify() -> None:
    assert with_verify({"id": 10, "card": False})["verify"]["card"] is False
    assert with_verify({"id": 10, "card": True})["verify"]["card"] is True
    assert "card" not in with_verify({"id": 10})["verify"]


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


# ---------------------------------------------------------------------------
# Settling an unfinished write: a bare job_id/future_id, or an HTTP 202 with
# no job reference at all, must never be reported verified before it has
# actually finished (truth-probe finding, 2026-09-28: `connector connection
# create` and `project delete`).
# ---------------------------------------------------------------------------


def test_bare_job_id_with_no_invocation_keeps_legacy_behavior() -> None:
    """No invocation to settle with (a direct unit-test call): unchanged."""
    result = with_verify({"job_id": 8827, "failure_reason": None, "status_code": None})
    assert result["verify"]["verified"] is True
    assert result["verify"]["state"] == "done"


def test_bare_job_id_settles_to_the_jobs_real_status_before_reporting(
    fake_service: FakeMammothService,
) -> None:
    """`connector connection create` shape: bare ``job_id``, job later succeeds."""
    fake_service.job_result = {"status": "done", "connection_id": 42}
    invocation = Invocation(command_id="connector.connection.create", output="json")
    result = with_verify({"job_id": 8827, "failure_reason": None, "status_code": None}, invocation)
    assert fake_service.calls == ["wait_if_job", "close"]
    assert fake_service.wait_log == [{"job_id": 8827, "failure_reason": None, "status_code": None}]
    assert result["connection_id"] == 42
    assert result["verify"]["verified"] is True
    assert result["verify"]["state"] == "done"


def test_bare_job_id_whose_job_fails_propagates_the_failure(
    fake_service: FakeMammothService,
) -> None:
    """`connector connection create` shape: the job later fails (psycopg2 DNS error).

    ``wait_if_job`` raises on a failed job, exactly like every other settle in
    this codebase; a job that fails must never be reported verified, so the
    failure is left to propagate rather than swallowed here.
    """

    def _raise(response: Any, **_kwargs: Any) -> Any:
        raise CliError(code="job_failed", message="could not translate host name", exit_status=1)

    fake_service.wait_if_job = _raise  # type: ignore[method-assign]
    invocation = Invocation(command_id="connector.connection.create", output="json")
    with pytest.raises(CliError, match="could not translate host name"):
        with_verify({"job_id": 8827, "failure_reason": None, "status_code": None}, invocation)


def test_bare_202_with_no_job_reference_is_not_verified(fake_service: FakeMammothService) -> None:
    """`project delete` shape: HTTP 202, no job reference at all to poll."""
    invocation = Invocation(command_id="project.delete", output="json")
    result = with_verify({"response": None, "status_code": 202}, invocation)
    assert fake_service.calls == []  # nothing to poll
    assert result["verify"]["verified"] is False
    assert result["verify"]["reason"] == (
        "the change was accepted but has not finished; read the view before building on it"
    )


def test_a_write_with_an_explicit_status_is_never_re_settled(
    fake_service: FakeMammothService,
) -> None:
    """A ``job_id`` alongside an already-meaningful ``status`` is left alone."""
    invocation = Invocation(command_id="connector.connection.create", output="json")
    result = with_verify({"job_id": 8827, "status": "done"}, invocation)
    assert fake_service.calls == []
    assert result["verify"]["verified"] is True


# ---------------------------------------------------------------------------
# A pipeline write can succeed on the view itself while breaking a saved
# export whose target_properties still reference something the write just
# removed (T2-WPP-W2: `view export dataset` then `view transform
# delete-columns` left the export's COLUMN_MAPPING pointing at a deleted
# column; `view export get` afterwards showed error_info 7001, but the
# delete's own verify said verified: true with no warnings).
# ---------------------------------------------------------------------------

_BROKEN_EXPORT = {
    "id": 251,
    "handler_type": "internal_dataset",
    "error_info": {
        "error_code": 7001,
        "reference_errors": {
            "reference_errors": [
                {
                    "column": {"display_name": "revision_rank"},
                    "reason": "missing_column",
                    "error_code": 7001,
                }
            ]
        },
    },
}


def test_pipeline_write_with_a_now_broken_export_is_unverified_and_needs_user(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses["mammoth.api.exports.ExportsAPI.list"] = {"exports": [_BROKEN_EXPORT]}
    invocation = Invocation(
        command_id="view.transform.delete-columns", output="json", extra_args=["3388"]
    )
    result = with_verify({"status": "done"}, invocation)
    assert result["verify"]["verified"] is False
    assert "export 251" in result["verify"]["reason"]
    assert "revision_rank" in result["verify"]["reason"]
    assert any("revision_rank" in warning for warning in result["verify"]["warnings"])
    assert result["verify"]["needs_user"] is not None
    assert "export 251" in result["verify"]["needs_user"]
    assert ("mammoth.api.exports.ExportsAPI.list", {"dataview_id": 3388}) in fake_service.call_log


@pytest.mark.parametrize(
    ("command_id", "args"),
    [
        ("view.task.delete", ["3388", "12"]),
        ("view.transform.rename-columns", ["3388"]),
        ("view.pipeline.edit", ["3388"]),
    ],
)
def test_every_write_that_can_drop_or_rename_a_column_checks_the_exports(
    fake_service: FakeMammothService, command_id: str, args: list[str]
) -> None:
    """Deleting a step, renaming a column or editing the pipeline breaks an
    export the same way a column delete does, but none of them is classed
    ``reversible_pipeline``, so the check never ran for them."""
    fake_service.responses["mammoth.api.exports.ExportsAPI.list"] = {"exports": [_BROKEN_EXPORT]}
    invocation = Invocation(command_id=command_id, output="json", extra_args=args)
    result = with_verify({"status": "done"}, invocation)
    assert result["verify"]["verified"] is False
    assert "export 251" in result["verify"]["reason"]


def test_pipeline_write_with_no_broken_exports_is_unaffected(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses["mammoth.api.exports.ExportsAPI.list"] = {
        "exports": [{"id": 251, "handler_type": "internal_dataset", "error_info": None}]
    }
    invocation = Invocation(
        command_id="view.transform.delete-columns", output="json", extra_args=["3388"]
    )
    result = with_verify({"status": "done"}, invocation)
    assert result["verify"]["verified"] is True
    assert result["verify"]["needs_user"] is None
    assert result["verify"]["warnings"] == []


def test_the_downstream_export_check_is_skipped_once_the_write_already_failed(
    fake_service: FakeMammothService,
) -> None:
    """A write already flagged unverified must not spend the extra read at all."""
    invocation = Invocation(
        command_id="view.transform.delete-columns", output="json", extra_args=["3388"]
    )
    result = with_verify({"has_error": True}, invocation)
    assert result["verify"]["verified"] is False
    assert fake_service.calls == []


def test_the_downstream_export_check_only_runs_for_pipeline_writes() -> None:
    """A non-view, non-pipeline write (no ``view_id``/``dataview_id`` positional) is unaffected."""
    invocation = Invocation(command_id="connector.connection.create", output="json")
    result = with_verify({"status": "done"}, invocation)
    assert result["verify"]["verified"] is True


def test_a_broken_export_in_the_live_nested_shape_names_its_error_and_column(
    fake_service: FakeMammothService,
) -> None:
    """The backend nests the details under ``additional_info`` (live koyal
    `view export get 3388 251`, T2-WPP-W2)."""
    fake_service.responses["mammoth.api.exports.ExportsAPI.list"] = {
        "exports": [
            {
                "id": 251,
                "handler_type": "internal_dataset",
                "error_info": {
                    "additional_info": {
                        "error_code": 7001,
                        "reference_errors": [{"column": {"display_name": "revision_rank"}}],
                    }
                },
            }
        ]
    }
    invocation = Invocation(
        command_id="view.transform.delete-columns", output="json", extra_args=["3388"]
    )
    result = with_verify({"status": "done"}, invocation)
    assert "error 7001" in result["verify"]["reason"]
    assert "revision_rank" in result["verify"]["reason"]


def test_a_failed_export_read_is_reported_not_hidden(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses["mammoth.api.exports.ExportsAPI.list"] = RuntimeError("503")
    invocation = Invocation(
        command_id="view.transform.delete-columns", output="json", extra_args=["3388"]
    )
    result = with_verify({"status": "done"}, invocation)
    assert result["verify"]["verified"] is True
    assert any("could not check" in w for w in result["verify"]["warnings"])
