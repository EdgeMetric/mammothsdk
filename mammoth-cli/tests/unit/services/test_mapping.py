"""Independent CLI recovery mapping tests.

These construct SDK exceptions directly so the expected CLI outcome does not
come from the mapper itself or from a shared fake transport.
"""

from __future__ import annotations

import pytest
from mammoth.exceptions import MammothAPIError, MammothJobTimeoutError

from mammoth_cli.errors.envelope import (
    EXIT_AUTH,
    EXIT_CONFLICT,
    EXIT_INTERRUPT,
    EXIT_RETRYABLE,
)
from mammoth_cli.services.mapping import map_sdk_exception


@pytest.mark.parametrize(
    ("status", "method", "state", "code", "exit_status"),
    [
        (403, "POST", "failed", "authorization_required", EXIT_AUTH),
        (409, "POST", "failed", "conflict", EXIT_CONFLICT),
        (429, "GET", "not_started", "retryable_error", EXIT_RETRYABLE),
        (503, "GET", "not_started", "retryable_error", EXIT_RETRYABLE),
    ],
)
def test_http_outcomes_keep_typed_exit_and_safe_metadata(
    status: int,
    method: str,
    state: str,
    code: str,
    exit_status: int,
) -> None:
    error = MammothAPIError(
        "credential text must not escape",
        status_code=status,
        method=method,
        operation_state=state,
        request_id="req-1",
        retry_after="9",
        response_body={"detail": "blocked", "api_secret": "hidden"},
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == code
    assert mapped.exit_status == exit_status
    assert mapped.details["request_id"] == "req-1"
    assert mapped.details["retry_after"] == "9"
    assert "hidden" not in str(mapped.to_envelope())


def test_unknown_mutation_is_not_advertised_as_safe_retry() -> None:
    error = MammothAPIError(
        "response lost",
        status_code=503,
        method="POST",
        operation_state="outcome_unknown",
        job_handle=44,
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "outcome_unknown"
    assert mapped.exit_status == EXIT_RETRYABLE
    assert mapped.retryable is False
    assert mapped.details["job_handle"] == 44
    assert any("job get 44" in command for command in mapped.recovery_commands)


def test_post_submit_readback_failure_preserves_safe_task_recovery() -> None:
    error = MammothAPIError(
        "pipeline readback failed",
        method="POST",
        operation_state="outcome_unknown",
        details={
            "post_submitted": True,
            "task_handle": 130,
            "dataview_id": 303,
            "dataset_id": 375,
            "project_id": 3,
        },
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "outcome_unknown"
    assert mapped.retryable is False
    assert mapped.recovery_commands == [
        "mammoth view task get 303 130 --project 3 "
        "--input '{\"dataset_id\": 375}' --output json --no-input"
    ]


def test_future_handle_gets_job_recovery_not_fake_task_lookup() -> None:
    error = MammothAPIError(
        "pipeline readback failed",
        method="POST",
        operation_state="outcome_unknown",
        job_handle=77,
        details={"post_submitted": True},
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "outcome_unknown"
    assert all("view task get" not in command for command in mapped.recovery_commands)
    assert any("job get 77" in command for command in mapped.recovery_commands)


def test_job_timeout_retains_handle_and_recovery_action() -> None:
    mapped = map_sdk_exception(MammothJobTimeoutError(44, 1))

    assert mapped.code == "timeout"
    assert mapped.details["job_handle"] == 44
    assert mapped.recovery_commands == [
        "mammoth job get 44 --output json --no-input",
        "mammoth job wait 44 --output json --no-input",
    ]


def test_keyboard_interrupt_has_exit_130_and_resume_commands() -> None:
    interrupt = KeyboardInterrupt()
    interrupt.job_handle = 44  # type: ignore[attr-defined]
    interrupt.operation_state = "running"  # type: ignore[attr-defined]
    interrupt.phase = "polling"  # type: ignore[attr-defined]

    mapped = map_sdk_exception(interrupt)

    assert mapped.code == "interrupted"
    assert mapped.exit_status == EXIT_INTERRUPT
    assert mapped.details["job_handle"] == 44
    assert any("job wait 44" in command for command in mapped.recovery_commands)
