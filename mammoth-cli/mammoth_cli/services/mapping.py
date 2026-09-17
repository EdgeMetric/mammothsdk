"""Translate SDK failures into the CLI's versioned recovery contract."""

from __future__ import annotations

import shlex
from typing import Any

from mammoth.exceptions import (
    MammothAPIError,
    MammothAuthError,
    MammothError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    safe_response_body,
)

from mammoth_cli.errors.envelope import (
    CODE_API_ERROR,
    CODE_AUTHENTICATION_FAILED,
    CODE_AUTHORIZATION_REQUIRED,
    CODE_CONFLICT,
    CODE_JOB_FAILED,
    CODE_OUTCOME_UNKNOWN,
    CODE_RESOURCE_NOT_FOUND,
    CODE_RETRYABLE,
    EXIT_API,
    EXIT_AUTH,
    EXIT_CONFLICT,
    EXIT_NOT_FOUND,
    EXIT_RETRYABLE,
    CliError,
    interrupted_error,
)


def _metadata(exc: MammothAPIError) -> dict[str, Any]:
    """Copy only safe, bounded recovery metadata from an SDK exception."""
    details: dict[str, Any] = {}
    if exc.status_code is not None:
        details["status_code"] = exc.status_code
    for name in ("method", "operation_state", "phase", "job_handle", "resource_handle", "endpoint"):
        value = getattr(exc, name, None)
        if value is not None:
            details[name] = value
    if exc.retry_after is not None:
        details["retry_after"] = exc.retry_after
    if exc.request_id is not None:
        details["request_id"] = exc.request_id
    if exc.response_body:
        details["response_body"] = exc.response_body
    for name in (
        "exception_type",
        "operation_state",
        "phase",
        "job_handle",
        "resource_handle",
        "response_body",
        "errno",
        "quarantined_path",
        "post_submitted",
        "task_handle",
        "dataview_id",
        "dataset_id",
        "project_id",
        "readback_error",
    ):
        if name in exc.details and name not in details:
            details[name] = (
                safe_response_body(exc.details[name])
                if name == "response_body"
                else exc.details[name]
            )
    return details


def _job_recovery(job_id: object, *, profile: str | None = None) -> list[str]:
    profile_option = f" --profile {shlex.quote(profile)}" if profile else ""
    return [
        f"mammoth job get {job_id}{profile_option} --output json --no-input",
        f"mammoth job wait {job_id}{profile_option} --output json --no-input",
    ]


def map_sdk_exception(
    exc: BaseException,
    *,
    profile: str | None = None,
    project_id: int | None = None,
    workspace_id: int | None = None,
) -> CliError:
    """Map one SDK or transport failure to a typed, stable CLI outcome.

    Mutation timeouts and retry responses are *not* blanket-retryable: the SDK
    marks those calls ``outcome_unknown`` because the server may have committed
    the write while the response was lost.  A read timeout remains safely
    retryable.  This function only describes recovery; it never sends a second
    request.
    """
    if isinstance(exc, KeyboardInterrupt):
        job_id = getattr(exc, "job_handle", None) or getattr(exc, "job_id", None)
        return interrupted_error(
            job_id=job_id,
            operation_state=getattr(exc, "operation_state", None),
            phase=getattr(exc, "phase", None),
            details=getattr(exc, "details", None),
        )

    if isinstance(exc, MammothAuthError):
        return CliError(
            code=CODE_AUTHENTICATION_FAILED,
            message="Mammoth rejected the provided credentials.",
            exit_status=EXIT_AUTH,
            hint="Check the API key, secret, and workspace id.",
            details=_metadata(exc),
            request_id=exc.request_id,
            recovery_commands=["mammoth auth login"],
        )

    if isinstance(exc, MammothJobTimeoutError):
        job_id = getattr(exc, "job_handle", None) or getattr(exc, "job_id", None)
        details = dict(getattr(exc, "details", {}) or {})
        if job_id is not None:
            details.setdefault("job_id", job_id)
        details.setdefault("operation_state", "running")
        details.setdefault("phase", getattr(exc, "phase", None) or "polling")
        return CliError(
            code="timeout",
            message="The operation did not finish before the timeout.",
            exit_status=EXIT_RETRYABLE,
            hint="Inspect the job and wait for it to reach a terminal state.",
            details=details,
            retryable=True,
            recovery_commands=_job_recovery(job_id, profile=profile) if job_id is not None else [],
        )

    if isinstance(exc, MammothJobFailedError):
        details = dict(getattr(exc, "details", {}) or {})
        job_id = getattr(exc, "job_handle", None) or getattr(exc, "job_id", None)
        return CliError(
            code=CODE_JOB_FAILED,
            message="The Mammoth job failed.",
            exit_status=EXIT_API,
            hint="Inspect the job response for the failure reason.",
            details=details,
            recovery_commands=_job_recovery(job_id, profile=profile) if job_id is not None else [],
        )

    if isinstance(exc, MammothAPIError):
        status = exc.status_code
        details = _metadata(exc)
        operation_state = getattr(exc, "operation_state", None) or details.get("operation_state")
        job_id = getattr(exc, "job_handle", None) or details.get("job_handle")
        if job_id is None and isinstance(exc.response_body, dict):
            candidate = exc.response_body.get("job_id")
            if candidate is None and isinstance(exc.response_body.get("job"), dict):
                job_body = exc.response_body["job"]
                candidate = job_body.get("id") or job_body.get("job_id")
            if candidate is not None:
                job_id = candidate
        if job_id is not None:
            details.setdefault("job_handle", job_id)
        request_id = getattr(exc, "request_id", None)
        recovery = _job_recovery(job_id, profile=profile) if job_id is not None else []
        if details.get("post_submitted"):
            task_id = details.get("task_handle")
            dataview_id = details.get("dataview_id")
            dataset_id = details.get("dataset_id")
            recovery_project_id = details.get("project_id")
            valid_scope = all(
                isinstance(value, int) and not isinstance(value, bool)
                for value in (dataview_id, dataset_id, recovery_project_id)
            )
            if (
                isinstance(task_id, int)
                and not isinstance(task_id, bool)
                and isinstance(dataview_id, int)
                and not isinstance(dataview_id, bool)
                and isinstance(dataset_id, int)
                and not isinstance(dataset_id, bool)
                and isinstance(recovery_project_id, int)
                and not isinstance(recovery_project_id, bool)
            ):
                recovery = [
                    f"mammoth view task get {dataview_id} {task_id} --project {recovery_project_id}"
                    f"{' --profile ' + shlex.quote(profile) if profile else ''} "
                    f"--input '{{\"dataset_id\": {dataset_id}}}' --output json --no-input"
                ]
            elif not recovery and valid_scope:
                recovery = [
                    f"mammoth view pipeline items-all {dataview_id} --project {recovery_project_id}"
                    f"{' --profile ' + shlex.quote(profile) if profile else ''} "
                    f"--input '{{\"dataset_id\": {dataset_id}}}' --output json --no-input"
                ]

        # A complete destination was intentionally not published by the SDK
        # when a local write failed (for example ENOSPC).  This is a terminal
        # artifact error, not an invitation to replay a remote export job.
        if details.get("errno") is not None:
            return CliError(
                code="download_failed",
                message="The export could not be saved locally; the destination was not replaced.",
                exit_status=EXIT_API,
                hint=(
                    "Free disk space or choose another destination, then inspect the "
                    "export job before downloading again."
                ),
                details=details,
                request_id=request_id,
                recovery_commands=recovery,
            )

        if status == 404:
            return CliError(
                code=CODE_RESOURCE_NOT_FOUND,
                message="The requested Mammoth resource does not exist.",
                exit_status=EXIT_NOT_FOUND,
                hint="Check the resource id and scope.",
                details=details,
                request_id=request_id,
            )
        if status == 403:
            return CliError(
                code=CODE_AUTHORIZATION_REQUIRED,
                message="Mammoth denied access to the requested resource or operation.",
                exit_status=EXIT_AUTH,
                hint="Check the target scope or ask an administrator for permission.",
                details=details,
                request_id=request_id,
                authorization_required=True,
            )
        if status == 409:
            return CliError(
                code=CODE_CONFLICT,
                message="Mammoth rejected the request because the target is in conflict.",
                exit_status=EXIT_CONFLICT,
                hint="Inspect current remote state and resolve the conflict before retrying.",
                details=details,
                request_id=request_id,
                recovery_commands=recovery,
            )
        if operation_state == "outcome_unknown":
            details.setdefault("operation_state", CODE_OUTCOME_UNKNOWN)
            if workspace_id is not None:
                details.setdefault("workspace_id", workspace_id)
            if project_id is not None:
                details.setdefault("project_id", project_id)
            return CliError(
                code=CODE_OUTCOME_UNKNOWN,
                message="The request may have committed, but its outcome was not confirmed.",
                exit_status=EXIT_RETRYABLE,
                hint=(
                    "The mutation outcome is unknown. Inspect the observed "
                    "job/resource before taking any further mutation."
                ),
                details=details,
                request_id=request_id,
                retryable=False,
                recovery_commands=recovery,
            )
        if status in {429, 503} or status is None:
            return CliError(
                code=CODE_RETRYABLE,
                message="Mammoth is temporarily unavailable or the request timed out.",
                exit_status=EXIT_RETRYABLE,
                hint="Retry the read after the indicated delay, honoring Retry-After when present.",
                details=details,
                request_id=request_id,
                retryable=True,
            )
        return CliError(
            code=CODE_API_ERROR,
            message="Mammoth returned an API error.",
            exit_status=EXIT_API,
            hint="Inspect the structured details and correct the request.",
            details=details,
            request_id=request_id,
            recovery_commands=recovery,
        )

    if isinstance(exc, MammothError):
        return CliError(
            code=CODE_API_ERROR,
            message="Mammoth could not complete the operation.",
            exit_status=EXIT_API,
            hint="Inspect the structured details and correct the request.",
            details=dict(getattr(exc, "details", {}) or {}),
        )

    return CliError(
        code=CODE_API_ERROR,
        message="The Mammoth operation failed unexpectedly.",
        exit_status=EXIT_API,
        details={"exception_type": type(exc).__name__},
    )
