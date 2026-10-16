"""The choice between a run job's ``write_result`` and the reads that stand in for it.

Payloads are the shapes in the write-response contract (PRD-3091 S18): the run job's
``response`` is the run result plus ``write_result`` on a newer server, and the run result
alone on an older one, in draft mode, with auto-run off or after an analysis error.
"""

from __future__ import annotations

from mammoth_cli.commands.view_ops import clean_write_result

_RUN_RESULT = {"has_error": False, "taskwise_execution_result": [], "context": {}}
_WRITE_RESULT = {
    "task_id": 123,
    "task_run_status": "DONE",
    "pipeline_state": "ready",
    "row_count": 3,
    "columns": [{"name": "Brand new", "internal_name": "column_8", "type": "TEXT"}],
}


def test_a_finished_task_on_a_ready_pipeline_is_taken_from_the_run_job() -> None:
    job = {**_RUN_RESULT, "write_result": _WRITE_RESULT}

    assert clean_write_result(job) == _WRITE_RESULT


def test_a_run_job_without_write_result_falls_back_to_the_reads() -> None:
    assert clean_write_result(_RUN_RESULT) is None
    assert clean_write_result({"status": "processing", "future_id": 7}) is None


def test_a_write_result_that_does_not_say_clean_success_falls_back_to_the_reads() -> None:
    for fault in (
        {"task_run_status": "ERROR"},
        {"task_run_status": None},
        {"pipeline_state": "runtime_error"},
        {"row_count": None},
        {"task_id": None},
    ):
        job = {**_RUN_RESULT, "write_result": {**_WRITE_RESULT, **fault}}
        assert clean_write_result(job) is None, fault
