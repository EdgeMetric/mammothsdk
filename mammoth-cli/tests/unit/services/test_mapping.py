"""Independent CLI recovery mapping tests.

These construct SDK exceptions directly so the expected CLI outcome does not
come from the mapper itself or from a shared fake transport.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mammoth.exceptions import MammothAPIError, MammothJobTimeoutError

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import (
    EXIT_AUTH,
    EXIT_CONFLICT,
    EXIT_INTERRUPT,
    EXIT_NOT_FOUND,
    EXIT_RETRYABLE,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.services.mapping import map_sdk_exception
from mammoth_cli.services.sdk_service import SdkMammothService


@pytest.mark.parametrize(
    ("status", "method", "state", "code", "exit_status"),
    [
        (403, "POST", "failed", "authorization_required", EXIT_AUTH),
        (409, "POST", "failed", "conflict", EXIT_CONFLICT),
        (429, "GET", "not_started", "retryable_error", EXIT_RETRYABLE),
        (503, "GET", "not_started", "retryable_error", EXIT_RETRYABLE),
        # Gateway timeouts on a read (release edge returns 504 after ~90 s)
        # have nothing to reconcile: retry, do not report an api_error.
        (502, "GET", "failed", "retryable_error", EXIT_RETRYABLE),
        (504, "GET", "failed", "retryable_error", EXIT_RETRYABLE),
        # The same status on a write is uncertain, never retryable.
        (504, "POST", "failed", "outcome_unknown", EXIT_RETRYABLE),
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


@pytest.mark.parametrize(
    ("status", "state", "expected_code", "expected_exit"),
    [
        (403, "failed", "authorization_required", EXIT_AUTH),
        (404, "failed", "resource_not_found", EXIT_NOT_FOUND),
        (409, "failed", "conflict", EXIT_CONFLICT),
        (413, "failed", "invalid_argument", EXIT_USAGE),
        (502, "outcome_unknown", "outcome_unknown", EXIT_RETRYABLE),
    ],
)
def test_status_taxonomy_keeps_backend_identity_and_safe_next_action(
    status: int, state: str, expected_code: str, expected_exit: int
) -> None:
    mapped = map_sdk_exception(
        MammothAPIError(
            "failed",
            status_code=status,
            method="POST",
            operation_state=state,
            request_id="req-status",
            response_body={"code": "BACKEND_STATUS", "detail": "safe detail"},
        )
    )

    assert mapped.code == expected_code
    assert mapped.exit_status == expected_exit
    assert mapped.request_id == "req-status"
    assert mapped.details["backend_code"] == "BACKEND_STATUS"
    assert mapped.retryable is False


def test_metadata_free_api_failure_is_unknown_not_a_replayable_read() -> None:
    mapped = map_sdk_exception(MammothAPIError("transport context lost"))

    assert mapped.code == "outcome_unknown"
    assert mapped.retryable is False
    assert mapped.details["metadata_missing"] == ["method", "operation_state"]
    assert "Do not replay" in mapped.hint


def test_unclassified_mutation_gateway_and_malformed_success_are_unknown() -> None:
    for error in (
        MammothAPIError("gateway", status_code=502, method="PATCH"),
        MammothAPIError(
            "wrong response shape",
            status_code=200,
            method="POST",
            operation_state="outcome_unknown",
        ),
    ):
        mapped = map_sdk_exception(error)
        assert mapped.code == "outcome_unknown"
        assert mapped.retryable is False
        assert "Do not replay" in mapped.hint


@pytest.mark.parametrize("status", [500, 502, 504, 200])
def test_sdk_classified_ambiguous_mutation_is_unknown_regardless_of_status(status: int) -> None:
    error = MammothAPIError(
        "gateway or decode failure",
        status_code=status,
        method="POST",
        operation_state="outcome_unknown",
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "outcome_unknown"
    assert mapped.retryable is False


def test_service_uses_resolved_nondefault_profile_in_job_recovery() -> None:
    service = SdkMammothService(
        ResolvedAuth("key", "secret", 4, "https://fake.mammoth.test/api/v2"),
        profile="production",
        project_id=9,
    )
    service._client.jobs.get_job = MagicMock(  # type: ignore[method-assign]
        side_effect=MammothAPIError(
            "response lost",
            status_code=502,
            method="POST",
            operation_state="outcome_unknown",
            job_handle=44,
        )
    )

    with pytest.raises(CliError) as raised:
        service.call("mammoth.api.jobs.JobsAPI.get_job", job_id=44)

    mapped = raised.value
    assert mapped.code == "outcome_unknown"
    assert mapped.details["workspace_id"] == 4
    assert mapped.details["project_id"] == 9
    assert mapped.recovery_commands == [
        "mammoth job get 44 --profile production",
        "mammoth job wait 44 --profile production",
    ]


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
        "mammoth view task get 303 130 --project 3 " "--input '{\"dataset_id\": 375}'"
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


def test_unidentified_post_submit_gets_scoped_pipeline_readback() -> None:
    error = MammothAPIError(
        "pipeline readback failed",
        method="POST",
        operation_state="outcome_unknown",
        details={
            "post_submitted": True,
            "dataview_id": 303,
            "dataset_id": 375,
            "project_id": 3,
        },
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "outcome_unknown"
    assert mapped.retryable is False
    assert mapped.recovery_commands == [
        "mammoth view pipeline items-all 303 --project 3 " "--input '{\"dataset_id\": 375}'"
    ]
    assert all("task get" not in command for command in mapped.recovery_commands)
    assert all("job get" not in command for command in mapped.recovery_commands)


def test_job_timeout_retains_handle_and_recovery_action() -> None:
    mapped = map_sdk_exception(MammothJobTimeoutError(44, 1))

    assert mapped.code == "timeout"
    assert mapped.details["job_handle"] == 44
    assert mapped.recovery_commands == [
        "mammoth job get 44",
        "mammoth job wait 44",
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


def test_completed_export_local_failure_keeps_delivery_state_and_redownload_hint() -> None:
    mapped = map_sdk_exception(
        MammothAPIError(
            "Failed to save downloaded file",
            method="GET",
            operation_state="succeeded",
            phase="download",
            job_handle=919,
            details={
                "errno": 28,
                "remote_export_state": "succeeded",
                "local_artifact_state": "failed",
                "recovery_hint": "Re-download the observed artifact; do not recreate the export.",
            },
        )
    )

    assert mapped.code == "download_failed"
    assert mapped.details["remote_export_state"] == "succeeded"
    assert mapped.details["local_artifact_state"] == "failed"
    assert mapped.hint == "Re-download the observed artifact; do not recreate the export."
    assert any("job get 919" in command for command in mapped.recovery_commands)


def test_pydantic_validation_error_names_the_failing_fields() -> None:
    # A response that no longer matches the SDK's snapshot model used to
    # surface as an empty "failed unexpectedly" envelope.
    from pydantic import BaseModel, ValidationError

    class Probe(BaseModel):
        tokens: dict[str, str]

    try:
        Probe.model_validate({"tokens": "***"})
    except ValidationError as exc:
        error = map_sdk_exception(exc)
    else:  # pragma: no cover
        raise AssertionError("expected a validation failure")

    assert error.code == "api_error"
    assert error.details["model"] == "Probe"
    assert error.details["validation_errors"][0]["loc"] == "tokens"
    assert error.details["validation_errors"][0]["type"] == "dict_type"
    assert "schema get" in (error.hint or "")


def test_sdk_validation_error_surfaces_its_message_as_invalid_arguments() -> None:
    # `ai expression generate --input {"mode": "sample"}` used to come back as
    # an opaque api_error with empty details even though the SDK had rejected
    # the mode before sending anything.
    from mammoth.exceptions import MammothValidationError

    error = map_sdk_exception(
        MammothValidationError("mode must be 'math' or 'metric', got 'sample'.", {"mode": "sample"})
    )

    assert error.code == "invalid_arguments"
    assert error.exit_status == 2
    assert error.message == "mode must be 'math' or 'metric', got 'sample'."
    assert error.details == {"exception_type": "MammothValidationError", "mode": "sample"}
    assert "no request was sent" in (error.hint or "")


@pytest.mark.parametrize(
    ("method", "endpoint", "expected"),
    [
        ("DELETE", "/workspaces/4/projects/97", "mammoth project get 97"),
        ("POST", "/dashboards/v3/blank", "mammoth dashboard list --project 12"),
        ("POST", "/dashboards/54/pages", "mammoth dashboard canvas get 54"),
    ],
)
def test_unknown_write_without_a_job_names_the_read_that_settles_it(
    method: str, endpoint: str, expected: str
) -> None:
    error = MammothAPIError(
        "read timeout",
        status_code=None,
        method=method,
        endpoint=endpoint,
        operation_state="outcome_unknown",
    )
    mapped = map_sdk_exception(error, project_id=12)
    assert mapped.code == "outcome_unknown"
    assert mapped.recovery_commands == [expected]
