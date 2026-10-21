"""What ``job wait`` reports about the object a finished job acted on.

Expected values follow the module's documented contract: only the listed view operations
count; ids come from the job's ``path`` (``/projects/P/datasets/D/dataviews/V``) with the
response's ``dataset_id`` / ``dataview_id`` / ``id`` as the fallback; a project copy reports
its counts and per-view runs from the job record itself.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands.job import _with_outcome
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import job_outcome as jo
from mammoth_cli.services.testing import FakeMammothService

_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_VIEW_PATH = "/api/v2/projects/180/datasets/9/dataviews/7/pipeline/rerun"


def _job(operation: str, path: str = "", result: Any = None) -> dict[str, Any]:
    return {"job_id": 1, "operation": operation, "path": path, "result": result}


# ── view_target ──


def test_view_target_reads_all_three_ids_from_the_path() -> None:
    assert jo.view_target(_job("rerun_dataview", _VIEW_PATH)) == jo.ViewTarget(180, 9, 7)


@pytest.mark.parametrize("operation", sorted(jo.VIEW_JOB_OPERATIONS))
def test_every_documented_view_operation_names_its_target(operation: str) -> None:
    assert jo.view_target(_job(operation, _VIEW_PATH)) == jo.ViewTarget(180, 9, 7)


def test_a_job_that_leaves_no_view_has_no_target() -> None:
    assert jo.view_target(_job("copy_project", _VIEW_PATH)) is None
    assert jo.view_target({"path": _VIEW_PATH}) is None


def test_a_created_view_takes_its_id_from_the_response() -> None:
    """``create_dataview`` posts to the dataset; the new view is in the response ``id``."""
    job = _job("create_dataview", "/projects/180/datasets/9/dataviews", {"id": "55"})
    assert jo.view_target(job) == jo.ViewTarget(180, 9, 55)


def test_response_dataview_id_wins_over_id_and_supplies_a_missing_dataset() -> None:
    job = _job("clone_dataview", "/projects/180", {"dataset_id": 9, "dataview_id": 8, "id": 99})
    assert jo.view_target(job) == jo.ViewTarget(180, 9, 8)


@pytest.mark.parametrize(
    "job",
    [
        _job("rerun_dataview", "/datasets/9/dataviews/7"),  # no project
        _job("rerun_dataview", "/projects/180/datasets/9"),  # no view
        _job("rerun_dataview", "/projects/180"),  # no dataset, no response
        _job("rerun_dataview", _VIEW_PATH.replace("/7/", "/x/")),  # not numeric
        _job("rerun_dataview", "", None),
    ],
)
def test_a_target_missing_any_id_is_none(job: dict[str, Any]) -> None:
    assert jo.view_target(job) is None


# ── export_target ──


def test_an_add_export_job_names_the_view_it_added_the_export_to() -> None:
    path = "/projects/180/datasets/9/dataviews/7/pipeline/exports"
    assert jo.export_target(_job("add_action", path)) == jo.ViewTarget(180, 9, 7)


@pytest.mark.parametrize(
    "job",
    [
        _job("rerun_dataview", "/projects/180/datasets/9/dataviews/7/pipeline/exports"),
        _job("add_action", "/projects/180/datasets/9/dataviews/7/pipeline/tasks"),
        _job("add_action", "/projects/180/datasets/9/pipeline/exports"),
        {"operation": "add_action"},
    ],
)
def test_any_other_job_has_no_export_target(job: dict[str, Any]) -> None:
    assert jo.export_target(job) is None


# ── view_outcome ──


def test_view_outcome_reports_rows_columns_state_and_running_flag() -> None:
    record = {
        "id": 7,
        "name": "Sales",
        "row_count": 10,
        "column_count": 2,
        "pipeline_status": "runtime_error",
        "is_dataview_data_in_sync": False,
        "is_pipeline_running": True,
        "metadata": [
            {"display_name": "Region", "type": "TEXT"},
            {"display_name": "Amount", "type": "NUMERIC"},
        ],
    }
    assert jo.view_outcome(record, jo.ViewTarget(180, 9, 7)) == {
        "kind": "view",
        "view_id": 7,
        "dataset_id": 9,
        "status": "runtime_error",
        "name": "Sales",
        "rows": 10,
        "cols": 2,
        "columns": "Region:text, Amount:numeric",
        "pipeline_status": "runtime_error",
        "in_sync": False,
        "pipeline_running": True,
    }


def test_view_outcome_of_an_unreadable_record_still_names_the_target() -> None:
    assert jo.view_outcome("nope", jo.ViewTarget(180, 9, 7)) == {
        "kind": "view",
        "view_id": 7,
        "dataset_id": 9,
        "status": None,
        "pipeline_running": False,
    }


def test_a_ready_view_reports_status_ready_without_a_pipeline_status_key() -> None:
    outcome = jo.view_outcome({"status": "ready"}, jo.ViewTarget(180, 9, 7))
    assert outcome["status"] == "ready"
    assert "pipeline_status" not in outcome


# ── copy_outcome / runs ──


def test_a_copy_without_view_map_has_no_outcome() -> None:
    assert jo.copy_outcome({"project_id": 5}) is None
    assert jo.copy_outcome("done") is None


def test_a_copy_counts_what_was_copied_and_skipped_and_omits_runs_if_unrecorded() -> None:
    outcome = jo.copy_outcome(
        {
            "project_id": 77,
            "dataset_map": {"1": 11, "2": 12},
            "view_map": {"10": 20},
            "skipped": [{"id": 3}],
        }
    )
    assert outcome == {
        "kind": "project_copy",
        "project_id": 77,
        "datasets": 2,
        "views": 1,
        "skipped": 1,
    }


def test_copy_runs_count_ok_list_failures_with_errors_and_queued_views_as_pending() -> None:
    outcome = jo.copy_outcome(
        {
            "project_id": 77,
            "view_map": {"10": 20, "11": 21, "12": 22},
            "runs": {
                "20": {"dataview_id": 20, "error": None},
                "21": {"dataview_id": 21, "error": "ref_error"},
            },
            "run_views": [20, 21, 22],
        }
    )
    assert outcome is not None
    assert outcome["runs"] == {
        "ok": 1,
        "failed": [{"view_id": 21, "error": "ref_error"}],
        "pending": [22],
    }


def test_a_failed_run_without_dataview_id_is_named_by_its_key() -> None:
    outcome = jo.copy_outcome({"view_map": {}, "runs": {"31": {"error": "boom"}}})
    assert outcome is not None
    assert outcome["runs"] == {
        "ok": 0,
        "failed": [{"view_id": "31", "error": "boom"}],
        "pending": [],
    }


def test_derived_datasets_are_sorted_and_non_numeric_keys_are_kept() -> None:
    result = jo.with_derived_datasets({"derived": {"9": [1], "10": None, "abc": [2]}})
    assert result["derived_datasets"] == [
        {"dataset_id": 10, "from_view_ids": []},
        {"dataset_id": 9, "from_view_ids": [1]},
        {"dataset_id": "abc", "from_view_ids": [2]},
    ]


# ── job wait: _with_outcome ──


def test_job_wait_reads_the_target_view_once_and_attaches_its_outcome() -> None:
    service = FakeMammothService()
    service.responses[_DATAVIEW_GET] = {"id": 7, "name": "Sales", "row_count": 3, "column_count": 1}

    data = _with_outcome(service, _job("rerun_dataview", _VIEW_PATH))

    assert service.call_log == [
        (_DATAVIEW_GET, {"dataset_id": 9, "dataview_id": 7, "project_id": 180})
    ]
    assert data["outcome"]["rows"] == 3
    assert data["outcome"]["view_id"] == 7


def test_an_unreadable_target_is_an_outcome_error_not_a_failed_wait() -> None:
    service = FakeMammothService()
    service.responses[_DATAVIEW_GET] = CliError(
        code="resource_not_found", message="no such view", exit_status=5
    )

    data = _with_outcome(service, _job("rerun_dataview", _VIEW_PATH))

    assert data["outcome_error"] == "resource_not_found: no such view"
    assert "outcome" not in data


def test_a_job_with_no_target_is_returned_without_any_read() -> None:
    service = FakeMammothService()
    job = _job("delete_dataset", "/projects/180/datasets/9")
    assert _with_outcome(service, job) == job
    assert service.call_log == []
