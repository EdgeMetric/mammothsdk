"""Two readings an agent got wrong on koyal: a copy's ``derived`` and a 403's next step."""

from __future__ import annotations

from mammoth.exceptions import MammothAPIError

from mammoth_cli.commands.job import _with_outcome
from mammoth_cli.services.job_outcome import copy_outcome, with_derived_datasets
from mammoth_cli.services.mapping import map_sdk_exception

_COPY = {
    "project_id": 77,
    "dataset_map": {"1": 5213, "2": 5214},
    "view_map": {"10": 5223, "11": 5224},
    "skipped": [],
    "derived": {"5214": [5224]},
}


def test_derived_says_which_dataset_is_derived_from_which_view() -> None:
    result = with_derived_datasets(_COPY)
    assert result["derived_datasets"] == [{"dataset_id": 5214, "from_view_ids": [5224]}]
    assert result["derived"] == {"5214": [5224]}


def test_a_result_without_derived_is_returned_as_it_is() -> None:
    plain = {k: v for k, v in _COPY.items() if k != "derived"}
    assert with_derived_datasets(plain) is plain
    assert with_derived_datasets(None) is None


def test_the_copy_outcome_carries_derived_datasets() -> None:
    outcome = copy_outcome(_COPY)
    assert outcome is not None
    assert outcome["derived_datasets"] == [{"dataset_id": 5214, "from_view_ids": [5224]}]


def test_job_wait_puts_derived_datasets_in_the_result_and_the_outcome() -> None:
    job = {"id": 9, "operation": "copy_project", "status": "success", "result": _COPY}
    data = _with_outcome(None, job)
    expected = [{"dataset_id": 5214, "from_view_ids": [5224]}]
    assert data["result"]["derived_datasets"] == expected
    assert data["outcome"]["derived_datasets"] == expected


def test_a_403_says_to_check_ids_and_scope_not_to_reload() -> None:
    refused = MammothAPIError(
        "Invalid hierarchy: datasource_5214 is not parent of dataview_5224",
        status_code=403,
        method="POST",
        operation_state="failed",
    )
    hint = map_sdk_exception(refused).hint or ""
    assert "reload" not in hint.lower()
    assert hint.startswith("Check the ids and scope first")
