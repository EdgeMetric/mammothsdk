"""Independent CLI recovery mapping tests.

These construct SDK exceptions directly so the expected CLI outcome does not
come from the mapper itself or from a shared fake transport.
"""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mammoth.client import MammothClient
from mammoth.exceptions import (
    MammothAPIError,
    MammothAuthError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    MammothPipelineTimeoutError,
)

from mammoth_cli.context import credentials
from mammoth_cli.context.oauth import OAuthSession
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
from mammoth_cli.services.mapping import map_sdk_exception, with_dashboard_scope
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


class _RefusedPollHandler(BaseHTTPRequestHandler):
    """Answers every read with the status its server was given."""

    server: _RefusedPollServer

    def do_GET(self) -> None:  # noqa: N802
        body = json.dumps({"detail": "token expired"}).encode()
        self.send_response(self.server.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


class _RefusedPollServer(HTTPServer):
    status = 401


@pytest.fixture(params=[401, 403])
def refused_poll_client(request: pytest.FixtureRequest) -> Iterator[MammothClient]:
    server = _RefusedPollServer(("127.0.0.1", 0), _RefusedPollHandler)
    server.status = request.param
    threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    ).start()
    yield MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    server.shutdown()


def test_a_refused_sign_in_while_polling_stays_outcome_unknown_and_says_to_sign_in(
    refused_poll_client: MammothClient,
) -> None:
    # A real SDK poll the server refuses (401 or 403): the job was accepted, so the code is
    # still outcome_unknown, but the hint is to sign in again and then read the job.
    with pytest.raises(MammothAPIError) as raised:
        asyncio.run(refused_poll_client.jobs.wait_for_job(52618, timeout=5))

    mapped = map_sdk_exception(raised.value)

    assert mapped.code == "outcome_unknown"
    assert mapped.exit_status == EXIT_RETRYABLE
    assert mapped.retryable is False
    assert "job 52618" in mapped.message
    hint = mapped.hint or ""
    assert "Do not resubmit" in hint
    assert hint.index("mammoth auth login") < hint.index("mammoth job get 52618")
    assert mapped.recovery_commands == ["mammoth auth login", "mammoth job get 52618"]
    assert mapped.details["job_handle"] == 52618


def test_a_refused_sign_in_outside_a_poll_is_still_an_authentication_failure() -> None:
    mapped = map_sdk_exception(MammothAuthError("expired", method="GET", operation_state="failed"))

    assert mapped.code == "authentication_failed"


def test_a_failed_poll_of_an_accepted_job_says_the_state_is_unknown_not_unchanged() -> None:
    # The SDK re-labels a poll that failed after the write was accepted (#340).
    error = MammothAPIError(
        "Request timed out",
        method="GET",
        operation_state="outcome_unknown",
        phase="polling",
        job_handle=52618,
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "outcome_unknown"
    assert mapped.retryable is False
    assert "job 52618" in mapped.message
    assert "changed nothing" not in (mapped.hint or "")
    assert "mammoth job get 52618" in (mapped.hint or "")
    assert any("job get 52618" in command for command in mapped.recovery_commands)


def test_cross_workspace_401_is_no_access_not_bad_credentials() -> None:
    """A 401 whose endpoint targets a workspace other than the profile's own
    is a scoping mistake, not invalid credentials: it must not tell the user
    to reauthenticate (release evidence T4-L-002 — the in-product agent
    parroted "reauthenticate" to a web user for exactly this case)."""
    error = MammothAuthError(
        "Token is invalid",
        endpoint="/workspaces/7/projects",
        method="GET",
    )

    mapped = map_sdk_exception(error, workspace_id=4)

    assert mapped.code == "authorization_required"
    assert mapped.exit_status == EXIT_AUTH
    assert "workspace 7" in mapped.message
    assert "workspace 4" in mapped.message
    assert mapped.authorization_required is True
    assert mapped.recovery_commands == []
    assert "mammoth auth login" not in mapped.recovery_commands


def test_401_without_a_workspace_mismatch_is_still_bad_credentials() -> None:
    error = MammothAuthError("Token is invalid", endpoint="/workspaces/4/projects", method="GET")

    mapped = map_sdk_exception(error, workspace_id=4)

    assert mapped.code == "authentication_failed"
    assert mapped.recovery_commands == ["mammoth auth login"]


def test_401_with_no_workspace_id_context_is_still_bad_credentials() -> None:
    error = MammothAuthError("Token is invalid", endpoint="/workspaces/7/projects", method="GET")

    mapped = map_sdk_exception(error)

    assert mapped.code == "authentication_failed"
    assert mapped.recovery_commands == ["mammoth auth login"]


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
        "mammoth job get 44 --project 9 --profile production",
        "mammoth job wait 44 --project 9 --profile production",
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


def test_pipeline_timeout_identifies_view_and_recovers_via_pipeline_commands() -> None:
    mapped = map_sdk_exception(
        MammothPipelineTimeoutError(5, 60, dataset_id=7, project_id=3), profile="p"
    )

    assert mapped.code == "timeout"
    assert mapped.retryable is True
    assert mapped.details == {
        "dataview_id": 5,
        "timeout": 60,
        "operation_state": "running",
        "phase": "pipeline",
        "dataset_id": 7,
        "project_id": 3,
        "waited_seconds": 60,
        "resume": "mammoth view pipeline wait 5 --project 3 --profile p",
    }
    assert mapped.recovery_commands == [
        "mammoth view pipeline get 5 --project 3 --profile p",
        "mammoth view pipeline wait 5 --project 3 --profile p",
    ]


def test_job_failure_carries_the_reason_status_and_job() -> None:
    mapped = map_sdk_exception(
        MammothJobFailedError(
            44, "column X missing", observed_job={"operation": "TRANSFORM", "path": "/x"}
        )
    )

    assert mapped.code == "job_failed"
    assert mapped.details["job_id"] == 44
    assert mapped.details["status"] == "failure"
    assert mapped.details["reason"] == "column X missing"
    assert (mapped.details["operation"], mapped.details["path"]) == ("TRANSFORM", "/x")
    assert "column X missing" in mapped.message
    assert mapped.recovery_commands == ["mammoth job get 44"]


def test_job_failure_without_a_reason_says_so() -> None:
    mapped = map_sdk_exception(MammothJobFailedError(44, None))

    assert mapped.details["reason"] == "no reason recorded by the job"


def test_job_timeout_details_carry_wait_and_resume() -> None:
    mapped = map_sdk_exception(MammothJobTimeoutError(44, 300))

    assert mapped.details["waited_seconds"] == 300
    assert mapped.details["operation_state"] == "running"
    assert mapped.details["resume"] == "mammoth job wait 44"


def test_dashboard_job_timeout_resumes_through_the_url_scoped_wait() -> None:
    mapped = with_dashboard_scope(map_sdk_exception(MammothJobTimeoutError(44, 300)), "sales")

    assert mapped.details["resume"] == (
        'mammoth job wait 44 --input \'{"dashboard_url": "sales"}\''
    )
    assert mapped.recovery_commands[0] == "mammoth dashboard job-by-url sales 44"


def test_a_not_allowed_400_is_an_authorization_error_with_the_backends_reason() -> None:
    # FB-10: 4DASH019 came back as a generic api_error, hint "Inspect the
    # structured details"; the agent got through only by reading the body.
    reason = (
        "You can view this project's dashboards but not create them. "
        "Ask a project admin for analyst access."
    )
    error = MammothAPIError(
        "Bad request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={
            "error_code": "4DASH019",
            "name": "DASHBOARD_CREATE_NOT_ALLOWED",
            "message": reason,
            "status_code": 400,
        },
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "authorization_required"
    assert mapped.exit_status == EXIT_AUTH
    assert mapped.authorization_required is True
    assert mapped.message == reason
    assert "Do not retry" in (mapped.hint or "")


def test_a_permission_error_400_is_an_authorization_error() -> None:
    # #277: 4PERM002 in a 400 fell through to api_error, "correct the request".
    error = MammothAPIError(
        "Bad request",
        status_code=400,
        method="GET",
        operation_state="not_started",
        response_body={
            "error_code": "4PERM002",
            "name": "PERMISSION_ERROR",
            "message": "User lacks permission to perform given action",
            "status_code": 400,
        },
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "authorization_required"
    assert mapped.exit_status == EXIT_AUTH
    assert mapped.authorization_required is True
    assert mapped.message == "User lacks permission to perform given action"


@pytest.mark.parametrize("status", [400, 403])
def test_a_plan_or_quota_refusal_names_the_plan_not_the_ids(status: int) -> None:
    # #254: 4SUBS104 said "You don't have permission" and "Check the ids".
    message = "Monthly AI usage limit reached. Contact support to extend."
    error = MammothAPIError(
        "Forbidden",
        status_code=status,
        method="POST",
        operation_state="failed",
        response_body={"error_code": "4SUBS104", "name": "AI_QUOTA_EXHAUSTED", "message": message},
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "plan_limit"
    assert mapped.exit_status == EXIT_AUTH
    assert mapped.authorization_required is False
    assert mapped.message == message
    assert "ids" not in mapped.to_envelope()["error"]["summary"]
    assert "Check the ids" not in (mapped.hint or "")


def test_feature_disabled_names_support_not_the_request() -> None:
    # 5GENR012 (FEATURE_DISABLED) read "correct the request" on `view export csv`.
    message = "This feature is disabled for the user-account combination, contact support"
    error = MammothAPIError(
        "Bad Request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={"error_code": "5GENR012", "name": "FEATURE_DISABLED", "message": message},
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "feature_disabled"
    assert mapped.retryable is False
    assert mapped.message == message
    assert "support" in (mapped.hint or "") and "admin" in (mapped.hint or "")
    assert "correct the request" not in (mapped.hint or "").lower()


@pytest.mark.parametrize(
    ("backend_code", "noun"),
    [
        ("4DSET001", "dataset"),
        ("4FILE001", "file"),
        ("4DTVW019", "view"),
        ("4AUTO001", "automation"),
        ("4AUTO005", "automation"),
        ("4DASH001", "dashboard"),
    ],
)
def test_every_gone_backend_code_reads_as_resource_not_found(backend_code: str, noun: str) -> None:
    error = MammothAPIError(
        "Bad Request",
        status_code=400,
        method="GET",
        operation_state="failed",
        response_body={"error_code": backend_code, "name": "NOT_FOUND", "message": "No such id"},
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "resource_not_found"
    assert mapped.exit_status == EXIT_NOT_FOUND
    assert noun in mapped.message


def test_an_ordinary_400_stays_an_api_error() -> None:
    error = MammothAPIError(
        "Bad request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={"error_code": "4DSET053", "name": "MUST_PROVIDE_TABLE_LIST_OR_PREVIEW"},
    )

    assert map_sdk_exception(error).code == "api_error"


def test_a_400_whose_reason_sits_in_name_says_it() -> None:
    # Recorded (workspace create): the message was generic, the missing field was in "name".
    error = MammothAPIError(
        "Bad request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={
            "details": None,
            "error_code": "4WKSP005",
            "message": "Workspace Creation Failed",
            "name": "INVALID_API_USAGE: Missing required field: user_email (Code: 4GENR014)",
        },
    )

    mapped = map_sdk_exception(error)

    assert mapped.message == (
        "Workspace Creation Failed: INVALID_API_USAGE: Missing required field: user_email "
        "(Code: 4GENR014) [4WKSP005]"
    )


def test_a_bare_error_name_is_not_added_to_the_message() -> None:
    error = MammothAPIError(
        "Bad request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={
            "error_code": "4DSET030",
            "message": "Invalid columns to get data",
            "name": "INVALID_COLUMNS",
        },
    )

    assert map_sdk_exception(error).message == "Invalid columns to get data [4DSET030]"


def test_a_read_timeout_hint_names_no_delay_the_server_never_gave() -> None:
    # FB-07: "Retry after the indicated delay" with no delay indicated.
    error = MammothAPIError(
        "timed out", status_code=None, method="GET", operation_state="not_started"
    )

    mapped = map_sdk_exception(error)

    assert mapped.code == "retryable_error"
    assert "indicated delay" not in (mapped.hint or "")
    assert "Retry the read" in (mapped.hint or "")


def test_a_retry_after_hint_names_the_delay() -> None:
    error = MammothAPIError(
        "busy", status_code=503, method="GET", operation_state="not_started", retry_after="9"
    )

    assert "9 s" in (map_sdk_exception(error).hint or "")


def _keys_refused() -> MammothAPIError:
    """The 403 the server returns for an mm_ token on the client-apps routes."""
    return MammothAPIError(
        "Cannot access this API with API-tokens",
        status_code=403,
        method="POST",
        endpoint="/workspaces/4/clientapps",
        response_body={"name": "INVALID_TOKEN_FOR_CLIENT_APPS", "code": "4GENR012"},
    )


def test_keys_refused_for_an_api_token_profile_says_sign_in_with_the_browser(
    isolated_cli_config: Path,
) -> None:
    credentials.store_credentials("default", storage="file", api_token="mm_" + "t" * 43)

    mapped = map_sdk_exception(_keys_refused())

    assert mapped.code == "cli_keys_need_browser_sign_in"
    assert "API token" in mapped.message
    assert "mammoth auth login" in mapped.message
    assert "cannot create API keys" not in (mapped.hint or "")
    assert mapped.recovery_commands == ["mammoth auth login"]


def test_keys_refused_for_an_oauth_profile_keeps_the_server_wording(
    isolated_cli_config: Path,
) -> None:
    session = OAuthSession("mm_" + "a" * 43, "12.secret.mac", 4_000_000_000, "oc_test", 12)
    credentials.store_credentials("default", storage="file", oauth=session)

    mapped = map_sdk_exception(_keys_refused())

    assert mapped.code == "cli_keys_not_allowed"
    assert "doesn't allow CLI-created keys" in mapped.message
    assert mapped.hint == "A browser sign-in cannot create API keys on this server."
    assert mapped.recovery_commands == ["mammoth auth login --method token"]


def _key_expired() -> MammothAuthError:
    """The 401 the server returns for an mm_ key past its expiry."""
    return MammothAuthError(
        "This token has expired. Sign in again to get a new one.",
        response_body={"name": "API_TOKEN_EXPIRED", "code": "4OAUT008"},
    )


def test_an_expired_key_says_to_sign_in_again() -> None:
    mapped = map_sdk_exception(_key_expired())

    assert mapped.code == "cli_key_expired"
    assert "mammoth auth login" in mapped.message
    assert mapped.recovery_commands == ["mammoth auth login"]


def test_an_expired_key_is_told_apart_from_a_rejected_one() -> None:
    mapped = map_sdk_exception(MammothAuthError("Invalid API credentials"))

    assert mapped.code == "authentication_failed"


def test_a_rejected_credential_names_the_failing_non_default_profile_in_recovery() -> None:
    error = MammothAuthError("Token is invalid", endpoint="/workspaces/4/projects", method="GET")
    mapped = map_sdk_exception(error, workspace_id=4, profile="work")
    assert mapped.recovery_commands == ["mammoth auth login --profile work"]
    assert "mammoth auth login --profile work" in (mapped.hint or "")
    default = map_sdk_exception(error, workspace_id=4, profile="default")
    assert default.recovery_commands == ["mammoth auth login"]


def test_a_file_dataset_in_a_retrieval_automation_gets_its_own_code_and_a_way_forward() -> None:
    """Bug bash 2026-10-15: 4AUTO006 was a generic api_error with no recovery."""
    error = MammothAPIError(
        "bad request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={
            "message": (
                "Invalid datasets for data retrieval, dataset ids should be a list of "
                "cloud datasets under the given project [4AUTO006]"
            )
        },
    )
    mapped = map_sdk_exception(error)
    assert mapped.code == "dataset_not_refreshable"
    assert mapped.exit_status == EXIT_USAGE
    assert "append_to_ds_id" in (mapped.hint or "")
    assert "cloud" in (mapped.hint or "")
    assert any("file upload" in c and "append_to_ds_id" in c for c in mapped.recovery_commands)


def test_refreshing_a_file_dataset_gets_the_same_code_as_automating_it() -> None:
    """Live recipe sweep 2026-10-26: 'dataset refresh' on a file dataset (4DSET048) was a
    generic api_error, while the automation refusal (4AUTO006) said what to do."""
    error = MammothAPIError(
        "bad request",
        status_code=400,
        method="POST",
        operation_state="failed",
        response_body={"message": "Invalid source type [4DSET048]"},
    )
    mapped = map_sdk_exception(error)
    assert mapped.code == "dataset_not_refreshable"
    assert mapped.exit_status == EXIT_USAGE
    assert "cloud or database source" in mapped.message
    assert any("file upload" in c and "append_to_ds_id" in c for c in mapped.recovery_commands)


def test_an_unknown_dataset_or_file_id_is_resource_not_found_like_a_view() -> None:
    """Bug bash 2026-10-15: 4DSET001 / 4FILE001 came back as a generic api_error."""
    for code, noun in (("4DSET001", "dataset"), ("4FILE001", "file")):
        error = MammothAPIError(
            "bad request",
            status_code=400,
            method="GET",
            operation_state="failed",
            response_body={"message": f"Invalid {noun} id [{code}]"},
        )
        mapped = map_sdk_exception(error)
        assert mapped.code == "resource_not_found", code
        assert mapped.exit_status == 5
        assert noun in (mapped.hint or "")


def test_job_recovery_commands_keep_the_project_they_ran_in() -> None:
    mapped = map_sdk_exception(MammothJobTimeoutError(44, 1), project_id=3633)

    assert mapped.recovery_commands == [
        "mammoth job get 44 --project 3633",
        "mammoth job wait 44 --project 3633",
    ]
    assert mapped.details["resume"] == "mammoth job wait 44 --project 3633"
