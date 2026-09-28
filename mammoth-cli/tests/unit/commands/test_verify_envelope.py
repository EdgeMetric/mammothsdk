"""``_execute`` adds the ``verify`` read-back to real, non-read, API-backed writes.

See :mod:`mammoth_cli.runtime.verify` for the pure derivation, and
``mammoth_cli.commands.view_ops._dispatch_view`` for the ``row_check`` a plain
view transform gets when it declares no ``before``/``after`` of its own.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation, ResourceRef
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_WAIT_FOR_PIPELINE = "mammoth.api.pipeline.PipelineAPI.wait_for_pipeline"
_PIPELINE_GET = "mammoth.api.pipeline.PipelineAPI.get_pipeline"
_TASK_LIST = "mammoth.api.pipeline.PipelineAPI.list_tasks"
_JSON_NO_INPUT = ["--output", "json", "--no-input"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _parent(view_id: int) -> ResourceRef:
    return ResourceRef(dataset_id=122, view_id=view_id)


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


def test_a_mutating_command_gets_a_verify_block(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DELETE] = {"status": "done"}
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--yes", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["verify"] == {
        "verified": True,
        "state": "done",
        "warnings": [],
        "reason": None,
        "needs_user": None,
    }


def test_a_read_command_gets_no_verify_block(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(["dataset", "get", "7", "--project", "180", *_JSON_NO_INPUT])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert "verify" not in data


def test_a_dry_run_gets_no_verify_block(fake_service: FakeMammothService) -> None:
    result = make_runner().invoke(
        ["dataset", "delete", "7", "--project", "180", "--dry-run", *_JSON_NO_INPUT]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert "verify" not in data


def test_a_plain_view_transform_gets_a_row_check(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert data["row_check"] == {"rows_before": 20, "rows_after": 20}
    assert (
        fake_service.call_log.count(
            (_DATAVIEW_GET, {"dataset_id": 122, "dataview_id": 3, "project_id": None})
        )
        == 2
    )


def test_a_plain_view_transform_waits_for_the_pipeline_before_reading_rows_after(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A read taken right after the write can catch the pipeline still
    recomputing and come back with no ``row_count`` yet; waiting for it to
    settle first (bounded) lets a real number arrive instead.
    """
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}

    def gate(symbol: str, kwargs: dict[str, object], **_ignored: object) -> None:
        if symbol == _WAIT_FOR_PIPELINE:
            fake_service.responses[_DATAVIEW_GET] = {"row_count": 17}

    fake_service.gate = gate
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert data["row_check"] == {"rows_before": 20, "rows_after": 17}
    assert (_WAIT_FOR_PIPELINE, {"dataview_id": 3, "dataset_id": 122, "timeout": 60.0}) in (
        fake_service.call_log
    )
    verified = with_verify(data)["verify"]
    assert verified["verified"] is True
    assert verified["warnings"] == []


def test_a_plain_view_transform_is_unverified_when_rows_after_never_arrives(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Even after waiting for the pipeline to settle, ``row_count`` can still
    come back unreadable; that must never be reported as a verified count.
    """
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}

    def gate(symbol: str, kwargs: dict[str, object], **_ignored: object) -> None:
        if symbol == _WAIT_FOR_PIPELINE:
            fake_service.responses[_DATAVIEW_GET] = {}

    fake_service.gate = gate
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert data["row_check"] == {"rows_before": 20, "rows_after": None}
    verified = with_verify(data)["verify"]
    assert verified["verified"] is False
    assert verified["needs_user"] is None
    assert verified["reason"] == (
        "the row count after the change could not be read; read the view before building on it"
    )
    assert verified["warnings"] == [
        "the row count after the change could not be read; read the view before building on it"
    ]


def test_a_staged_draft_transform_skips_the_row_check_and_the_settle_wait(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A view in draft mode never runs the pipeline, so there is no row
    count to wait for or read -- ``row_check`` must not appear at all.
    """
    fake_service.view_responses[(3, "limit_rows")] = {"status": "staged"}
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert "row_check" not in data
    assert _WAIT_FOR_PIPELINE not in fake_service.calls
    verified = with_verify(data)["verify"]
    assert verified["verified"] is True
    assert verified["state"] == "staged"
    assert "rows_before" not in verified
    assert "rows_after" not in verified
    assert verified["reason"] == "staged in draft; not applied until the draft is submitted"


def test_a_plain_view_transform_catches_a_runtime_error_execution_state(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """The write's own envelope can say ``status: done`` / ``pipeline_state:
    ready`` while the pipeline's own ``execution_state`` already carries
    runtime_error -- the row-count read alone never surfaces this. verify
    must see it and mark the write unverified, with the failing task id and
    error code when a cheap follow-up read finds them; needs_user stays
    null (2.0.74 rule: a failure is not "the user must hear about this").
    """
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    fake_service.responses[_PIPELINE_GET] = {
        "state": "ready",
        "execution_state": "runtime_error",
        "executing_task_id": 42,
    }
    fake_service.responses[_TASK_LIST] = {
        "tasks": [{"id": 42, "transform_status": "ERROR", "reference_errors": {"error_code": 7000}}]
    }
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    verified = with_verify(data)["verify"]
    assert verified["verified"] is False
    assert verified["needs_user"] is None
    assert "runtime error" in verified["reason"]
    assert "42" in verified["reason"]
    assert "7000" in verified["reason"]


def test_a_failed_pipeline_read_after_settle_is_unverified_not_silently_ok(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A failed ``get_pipeline`` read must never be treated as "no error" --
    that would report the write as verified when nobody actually confirmed
    it (fail loud, no silent fallbacks). Same reason text either way,
    needs_user stays null.
    """
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    fake_service.responses[_PIPELINE_GET] = CliError(code="api_error", message="boom")
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert data["pipeline_error"]["execution_state"] == "unknown"
    assert "CliError" in data["pipeline_error"]["read_error"]
    verified = with_verify(data)["verify"]
    assert verified["verified"] is False
    assert verified["needs_user"] is None
    assert verified["reason"] == (
        "the pipeline state after this change could not be read; read the view "
        "before building on it"
    )


def test_a_non_dict_pipeline_read_is_unverified_not_silently_ok(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    fake_service.responses[_PIPELINE_GET] = "not a dict"
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert data["pipeline_error"]["execution_state"] == "unknown"
    verified = with_verify(data)["verify"]
    assert verified["verified"] is False
    assert verified["needs_user"] is None


def test_a_failed_task_detail_read_is_recorded_not_swallowed(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A failed follow-up task-list read (finding the failing task's id and
    error code) must be recorded as ``task_detail_error``, not silently
    passed -- the pipeline error itself is still reported either way.
    """
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    fake_service.responses[_PIPELINE_GET] = {
        "state": "ready",
        "execution_state": "runtime_error",
    }
    fake_service.responses[_TASK_LIST] = CliError(code="api_error", message="task list boom")
    data, _meta = view_ops_cmd.view_transform_limit_rows(
        _inv(
            "view.transform.limit-rows",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, {"n": 10}),
            yes=True,
        )
    )
    assert data["pipeline_error"]["execution_state"] == "runtime_error"
    assert "CliError" in data["pipeline_error"]["task_detail_error"]
    verified = with_verify(data)["verify"]
    assert verified["verified"] is False
    assert verified["needs_user"] is None


def test_a_join_transform_keeps_its_own_join_check_not_row_check(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = {"row_count": 20}
    doc = {
        "foreign_view": 9,
        "join_type": "OUTER",
        "on": [{"left": "a", "right": "a"}],
        "select": [{"column": "b"}],
    }
    data, _meta = view_ops_cmd.view_transform_join(
        _inv(
            "view.transform.join",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=_write(tmp_path, doc),
        )
    )
    assert "row_check" not in data
    assert "join_check" in data
