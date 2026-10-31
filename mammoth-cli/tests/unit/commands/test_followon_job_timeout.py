"""A follow-on job that outlives ``--job-timeout`` is pending, not failed (bug bash 2026-10-15)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view.settle import wait_for_followon_job, wait_for_view_row_count
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services.testing import FakeMammothService


def _timeout() -> CliError:
    return CliError(
        code="timeout",
        message="The operation did not finish before the timeout.",
        exit_status=7,
        details={"job_id": 9001, "resume": "mammoth job wait 9001"},
        retryable=True,
    )


def test_a_followon_job_that_times_out_is_unfinished_not_job_failed(
    fake_service: FakeMammothService,
) -> None:
    def _raise(response: Any, **_kwargs: Any) -> Any:
        raise _timeout()

    fake_service.wait_if_job = _raise  # type: ignore[method-assign]
    error = wait_for_followon_job(fake_service, {"job_id": 9001, "status": "done"})
    assert error is not None
    assert error["execution_state"] == "unfinished"
    assert error["job_id"] == 9001
    assert error["resume"] == "mammoth job wait 9001"


def test_a_real_job_failure_is_still_job_failed(fake_service: FakeMammothService) -> None:
    def _raise(response: Any, **_kwargs: Any) -> Any:
        raise CliError(code="job_failed", message="boom", exit_status=1)

    fake_service.wait_if_job = _raise  # type: ignore[method-assign]
    error = wait_for_followon_job(fake_service, {"job_id": 9001})
    assert error is not None and error["execution_state"] == "job_failed"


def test_a_timed_out_transform_reads_pending_with_the_way_to_wait(
    fake_service: FakeMammothService,
) -> None:
    def _raise(response: Any, **_kwargs: Any) -> Any:
        raise _timeout()

    fake_service.wait_if_job = _raise  # type: ignore[method-assign]
    write = {"status": "done", "job_id": 9001}
    rows, error = wait_for_view_row_count(fake_service, 1, 2, 3, write_result=write)
    write["pipeline_error"] = error
    result = with_verify(write)
    assert result["verify"]["outcome"] == "pending"
    assert result["status"] == "pending"
    assert result["verify"]["next_command"] == "mammoth job wait 9001"


def test_the_row_count_and_the_pipeline_state_are_read_together(
    fake_service: FakeMammothService,
) -> None:
    """Two independent reads after the write take one round trip, not two."""
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {"row_count": 12}
    fake_service.responses["mammoth.api.pipeline.PipelineAPI.get_pipeline"] = {
        "execution_state": "ready"
    }
    batches: list[int] = []
    real = fake_service.call_many

    def spy(calls: Any) -> Any:
        batches.append(len(calls))
        return real(calls)

    fake_service.call_many = spy  # type: ignore[method-assign]
    rows, error = wait_for_view_row_count(
        fake_service, 1, 2, 3, write_result={"status": "done", "pipeline_state": "ready"}
    )
    assert (rows, error) == (12, None)
    assert batches == [2]
    # Each was read once: the answers of the batch were used, not fetched again.
    assert len(fake_service.call_log) == 2
    # And nothing read here outlives the settle.
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.get"] = {"row_count": 3}
    assert (
        fake_service.call("mammoth.api.dataviews.DataviewsAPI.get", dataset_id=1, dataview_id=2)[
            "row_count"
        ]
        == 3
    )


def test_an_unreadable_followon_job_is_unfinished_not_job_failed(
    fake_service: FakeMammothService,
) -> None:
    def _raise(response: Any, **_kwargs: Any) -> Any:
        raise CliError(code="retryable_error", message="unavailable", exit_status=7)

    fake_service.wait_if_job = _raise  # type: ignore[method-assign]
    error = wait_for_followon_job(fake_service, {"job_id": 9001})
    assert error is not None
    assert error["execution_state"] == "unfinished"
    assert error["job_id"] == 9001
    assert error["resume"] == "mammoth job wait 9001"
