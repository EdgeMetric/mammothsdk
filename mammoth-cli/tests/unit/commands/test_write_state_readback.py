"""Unit tests for the D-077 ``state`` read-back on the families this agent owns:
view, dataset, file, and the export commands inside view.

Unlike the generic mechanism tests (``tests/unit/runtime/test_state.py``,
fake ``command_by_id``/``HANDLERS``), these exercise the *real* manifest
declarations landed in ``spec/manifests/commands/{view,dataset,file}.yaml``
against the *real* registered command handlers, through ``with_state``
directly -- one test per readback kind actually used by these families
(data, object, delivery) plus one confirming ``no_readback`` adds nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import with_state
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_VIEW_GET = "mammoth.client.ViewsResource.get"
_VIEW_GET_EXACT_PARENT = "mammoth.api.dataviews.DataviewsAPI.get"
_VIEW_DATA_GET = "mammoth.api.dataviews.DataviewsAPI.get_data"
_VIEW_LIST = "mammoth.api.dataviews.DataviewsAPI.list"
_FIND_DATASET = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_JOB_GET = "mammoth.api.jobs.JobsAPI.get_job"
_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_FILE_GET = "mammoth.api.files.FilesAPI.get"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(command_id: str, extra_args: list[str], project: int = 10) -> Invocation:
    return Invocation(command_id=command_id, output="json", project=project, extra_args=extra_args)


# ---------------------------------------------------------------------------
# kind: data -- a view.transform.* write reads back its own view's real
# columns, row count and sample rows.
# ---------------------------------------------------------------------------


def test_view_transform_readback_is_kind_data(fake_service: FakeMammothService) -> None:
    # Neither readback needs a dataset id (transforms declare only view_id),
    # so both view.get and view.data.get fall to the discovery branch.
    fake_service.responses[_FIND_DATASET] = 122
    fake_service.responses[_VIEW_GET] = {
        "id": 3310,
        "row_count": 113,
        "metadata": [{"internal_name": "c1", "display_name": "petal_width", "type": "NUMERIC"}],
    }
    fake_service.responses[_VIEW_DATA_GET] = {"data": [{"petal_width": 1.4}, {"petal_width": 1.5}]}
    result = with_state(_inv("view.transform.filter", ["3310"]), {"status": "done"})
    assert result["state"] == {
        "kind": "data",
        "read_by": "view.data.get 3310",
        "columns": [{"name": "petal_width", "type": "NUMERIC"}],
        "row_count": 113,
        "sample": [{"petal_width": 1.4}, {"petal_width": 1.5}],
    }


# ---------------------------------------------------------------------------
# kind: object -- a plain CRUD write on a view/dataset/file reads back the
# record itself.
# ---------------------------------------------------------------------------


def test_view_trash_readback_is_kind_object(fake_service: FakeMammothService) -> None:
    # No dataset id in this readback's ids either: discovery branch, brief
    # record (BRIEF_VIEW_FIELDS keeps ``status``, not an ad hoc trashed flag).
    fake_service.responses[_VIEW_GET] = {"id": 3310, "name": "Sales", "status": "trashed"}
    result = with_state(_inv("view.trash", ["3310"]), {"status": "done"})
    assert result["state"] == {
        "kind": "object",
        "read_by": "view.get 3310",
        "object": {"id": 3310, "name": "Sales", "status": "trashed"},
    }


def test_dataset_rename_readback_is_kind_object(fake_service: FakeMammothService) -> None:
    fake_service.responses[_DATASET_GET] = {"id": 501, "name": "Sales (renamed)"}
    result = with_state(_inv("dataset.rename", ["501"]), {"status": "done"})
    # dataset.get's own handler adds view_count/hint when the dataset has no
    # views yet; the readback shows the real read, not a hand-trimmed one.
    assert result["state"] == {
        "kind": "object",
        "read_by": "dataset.get 501",
        "object": {
            "id": 501,
            "name": "Sales (renamed)",
            "view_count": 0,
            "hint": (
                "This dataset has no views yet; nothing is queryable until one exists. "
                "Run 'mammoth view create 501' to create one."
            ),
        },
    }


def test_file_update_readback_is_kind_object(fake_service: FakeMammothService) -> None:
    fake_service.responses[_FILE_GET] = {"id": 88, "name": "report.csv", "size": 1024}
    result = with_state(_inv("file.update", ["88"]), {"status": "done"})
    assert result["state"] == {
        "kind": "object",
        "read_by": "file.get 88",
        "object": {"id": 88, "name": "report.csv", "size": 1024},
    }


# ---------------------------------------------------------------------------
# kind: data, discovered from a dataset id -- dataset.create's output is its
# new default view, not the dataset object itself.
# ---------------------------------------------------------------------------


def test_dataset_create_readback_discovers_the_new_view(fake_service: FakeMammothService) -> None:
    fake_service.responses[_VIEW_LIST] = {"dataviews": [{"id": 91, "name": "Sheet1"}]}
    # The dataset id is already known here, so view.get takes the exact-parent
    # branch -- a different SDK symbol than the plain-view-id discovery path.
    fake_service.responses[_VIEW_GET_EXACT_PARENT] = {
        "id": 91,
        "row_count": 4,
        "metadata": [{"internal_name": "c1", "display_name": "a", "type": "TEXT"}],
    }
    fake_service.responses[_VIEW_DATA_GET] = {"data": [{"a": "x"}]}
    result = with_state(_inv("dataset.create", []), {"status": "ready", "dataset_id": 501})
    assert result["state"]["kind"] == "data"
    assert result["state"]["read_by"] == "view.data.get 91"
    assert result["state"]["row_count"] == 4
    assert result["state"]["columns"] == [{"name": "a", "type": "TEXT"}]
    assert result["state"]["sample"] == [{"a": "x"}]


# ---------------------------------------------------------------------------
# kind: delivery -- an external-destination export reads back its job.
# ---------------------------------------------------------------------------


def test_view_export_postgres_readback_is_kind_delivery(fake_service: FakeMammothService) -> None:
    fake_service.responses[_JOB_GET] = {"status": "done", "message": "exported 113 rows"}
    result = with_state(
        _inv("view.export.postgres", ["3310"]),
        {"trigger_id": 1, "status": "created", "future_id": 7660},
    )
    assert result["state"] == {
        "kind": "delivery",
        "read_by": "job.get 7660",
        "status": "done",
        "detail": "exported 113 rows",
    }


# ---------------------------------------------------------------------------
# no_readback -- declared writes add no state block at all.
# ---------------------------------------------------------------------------


def test_view_export_csv_declares_no_readback(fake_service: FakeMammothService) -> None:
    result = with_state(_inv("view.export.csv", ["3310"]), {"status": "done"})
    assert "state" not in result
