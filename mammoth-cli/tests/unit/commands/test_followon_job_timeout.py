"""A follow-on job that outlives ``--job-timeout`` is pending, not failed (bug bash 2026-10-15)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view import wait_for_followon_job, wait_for_view_row_count
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
