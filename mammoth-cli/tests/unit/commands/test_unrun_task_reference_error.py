"""A convert-type that breaks a downstream step is reported as that, not as an unfinished run.

On koyal (view 38745) the backend answered the add without ``has_error``, validated afterwards
('customer_id', ``type_mismatch``, 7003) and left the task ``added``; the CLI then read back an
unreadable state. These run the real functions on the backend's own reference-error record.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands import view_ops as view_ops_cmd

BROKEN_ITEM: dict[str, Any] = {
    "id": 5,
    "reference_errors": {
        "reference_errors": [
            {
                "column": {"display_name": "customer_id", "type": "NUMERIC"},
                "reason": "type_mismatch",
                "error_code": 7003,
            }
        ]
    },
}
UNFINISHED = {"execution_state": view_ops_cmd.UNFINISHED_STATE, "task_id": 7}


def test_the_envelope_names_the_column_the_reason_and_the_task_to_remove() -> None:
    error = view_ops_cmd._reference_error(
        38745,
        {"dataview_id": 38745, "dataset_id": 38754},
        {"state": "ref_error"},
        [BROKEN_ITEM],
        UNFINISHED,
    )
    assert error.code == view_ops_cmd.CODE_PIPELINE_REFERENCE_ERROR
    assert error.details["reference_errors"][0]["column"] == "customer_id"
    assert error.details["reference_errors"][0]["reason"] == "type_mismatch"
    assert error.recovery_commands == [
        "mammoth view task delete 38745 5 --yes --input '{\"dataset_id\": 38754}'"
    ]


@pytest.mark.parametrize("run_error", [None, {"execution_state": "runtime_error"}])
def test_a_finished_or_failed_run_is_not_this_error(run_error: dict[str, Any] | None) -> None:
    # No pipeline read is made: the guard returns before it touches the service.
    assert view_ops_cmd.reject_unrun_task_with_reference_errors(object(), 1, 2, run_error) is None
