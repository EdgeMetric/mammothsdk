"""Translate SDK failures into the CLI's versioned recovery contract."""

from __future__ import annotations

import json
import re
import shlex
from typing import Any

from mammoth.exceptions import (
    MammothAPIError,
    MammothAuthError,
    MammothColumnError,
    MammothError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    MammothPipelineTimeoutError,
    MammothValidationError,
    safe_response_body,
)

from mammoth_cli.context import credentials, profiles
from mammoth_cli.errors.envelope import (
    CODE_API_ERROR,
    CODE_AUTHENTICATION_FAILED,
    CODE_AUTHORIZATION_REQUIRED,
    CODE_CONFLICT,
    CODE_INVALID_ARGUMENT,
    CODE_INVALID_ARGUMENTS,
    CODE_JOB_FAILED,
    CODE_OUTCOME_UNKNOWN,
    CODE_RESOURCE_NOT_FOUND,
    CODE_RETRYABLE,
    EMBEDDED_AUTH_HINT,
    EXIT_API,
    EXIT_AUTH,
    EXIT_CONFLICT,
    EXIT_NOT_FOUND,
    EXIT_RETRYABLE,
    EXIT_USAGE,
    CliError,
    interrupted_error,
)
from mammoth_cli.runtime import embedded

_RETRYABLE_READ_STATUSES = frozenset({408, 425, 429, 502, 503, 504})


#: A client app's key is a credential identifier; an envelope never repeats it.
_CLIENT_KEY_SEGMENT = re.compile(r"(/clientapps/)[^/?#]+")


def _metadata(exc: MammothAPIError) -> dict[str, Any]:
    """Copy only safe, bounded recovery metadata from an SDK exception."""
    details: dict[str, Any] = {}
    if exc.status_code is not None:
        details["status_code"] = exc.status_code
    for name in ("method", "operation_state", "phase", "job_handle", "resource_handle"):
        value = getattr(exc, name, None)
        if value is not None:
            details[name] = value
    endpoint = getattr(exc, "endpoint", None)
    if endpoint is not None:
        details["endpoint"] = _CLIENT_KEY_SEGMENT.sub(r"\1{client_key}", str(endpoint))
    if exc.retry_after is not None:
        details["retry_after"] = exc.retry_after
    if exc.request_id is not None:
        details["request_id"] = exc.request_id
    if exc.response_body:
        details["response_body"] = exc.response_body
        # Backends commonly carry their stable diagnostic code in the JSON
        # body. Preserve it independently of the human message so callers do
        # not need to parse prose to decide the next safe action.
        for name in ("code", "error_code"):
            value = exc.response_body.get(name)
            if isinstance(value, (str, int)) and not isinstance(value, bool):
                details.setdefault("backend_code", value)
                break
    for name in (
        "backend_code",
        "error_code",
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
        "remote_export_state",
        "local_artifact_state",
        "recovery_hint",
    ):
        if name in exc.details and name not in details:
            details[name] = (
                safe_response_body(exc.details[name])
                if name == "response_body"
                else exc.details[name]
            )
    return details


def _is_known_read(method: object) -> bool:
    """Return whether transport metadata proves the request was observational."""
    return isinstance(method, str) and method.upper() in {"GET", "HEAD", "OPTIONS"}


def _job_recovery(job_id: object, *, profile: str | None = None) -> list[str]:
    profile_option = f" --profile {shlex.quote(profile)}" if profile else ""
    return [
        f"mammoth job get {job_id}{profile_option}",
        f"mammoth job wait {job_id}{profile_option}",
    ]


def _pipeline_recovery(exc: MammothPipelineTimeoutError, *, profile: str | None) -> list[str]:
    scope = f" --project {exc.project_id}" if exc.project_id is not None else ""
    scope += f" --profile {shlex.quote(profile)}" if profile else ""
    return [
        f"mammoth view pipeline get {exc.dataview_id}{scope}",
        f"mammoth view pipeline wait {exc.dataview_id}{scope}",
    ]


def _observed_job_fields(details: dict[str, Any]) -> dict[str, Any]:
    """The ``operation``/``path`` of the last observed job, when the server sent them."""
    observed = details.get("observed_job")
    if not isinstance(observed, dict):
        return {}
    return {key: observed[key] for key in ("operation", "path") if observed.get(key) is not None}


_PROJECT_DELETE = re.compile(r"/workspaces/\d+/projects/(\d+)/?$")
_DASHBOARD_WRITE = re.compile(r"/dashboards/(\d+)(?:/|$)")
_ENDPOINT_WORKSPACE = re.compile(r"/workspaces/(\d+)")


def _workspace_mismatch_error(exc: MammothAuthError, workspace_id: int | None) -> CliError | None:
    """A 401 whose endpoint targets a workspace other than the profile's own
    is a scoping mistake, not invalid credentials, so it must not tell the
    user to reauthenticate (release evidence T4-L-002 — the in-product agent
    parroted "reauthenticate" to a web user for exactly this case).
    """
    if workspace_id is None:
        return None
    endpoint = getattr(exc, "endpoint", None)
    if not isinstance(endpoint, str):
        return None
    match = _ENDPOINT_WORKSPACE.search(endpoint)
    if match is None:
        return None
    target_workspace_id = int(match.group(1))
    if target_workspace_id == workspace_id:
        return None
    return CliError(
        code=CODE_AUTHORIZATION_REQUIRED,
        message=(
            f"No access to workspace {target_workspace_id} "
            f"(this sign-in is for workspace {workspace_id})."
        ),
        exit_status=EXIT_AUTH,
        hint="Use a profile whose token belongs to that workspace.",
        details=_metadata(exc),
        request_id=exc.request_id,
        authorization_required=True,
    )


def _resource_recovery(
    method: object, endpoint: object, project_id: object, *, profile: str | None = None
) -> list[str]:
    """Reads that settle an unknown outcome for writes with no job handle.

    Seen on release during an outage: ``dashboard create-blank`` and
    ``project delete`` timed out with nothing to inspect, and agents could
    not tell whether to replay. Each command here answers that question.
    """
    if not isinstance(endpoint, str):
        return []
    options = f"{' --profile ' + shlex.quote(profile) if profile else ''}"
    verb = str(method or "").upper()
    if verb == "DELETE" and (match := _PROJECT_DELETE.search(endpoint)):
        # Deletion is asynchronous (202): read until resource_not_found.
        return [f"mammoth project get {match.group(1)}{options}"]
    if verb == "POST" and endpoint.rstrip("/").endswith("/dashboards/v3/blank"):
        project = f" --project {project_id}" if isinstance(project_id, int) else ""
        # Look for a dashboard with the title you sent before creating another.
        return [f"mammoth dashboard list{project}{options}"]
    if verb in {"POST", "PUT", "PATCH"} and (match := _DASHBOARD_WRITE.search(endpoint)):
        return [f"mammoth dashboard canvas get {match.group(1)}{options}"]
    return []


def with_dashboard_scope(error: CliError, dashboard_url: str) -> CliError:
    """Point a timed-out published-dashboard job's recovery at the URL-scoped route.

    ``GET /jobs/{id}`` answers ``4PERM002`` for these jobs, so the generic
    ``job get``/``job wait`` recovery would fail; ``job wait`` takes the
    dashboard URL as an ``--input`` field and polls the URL-scoped route.
    """
    job_id = error.details.get("job_id")
    if error.code != "timeout" or job_id is None:
        return error
    document = shlex.quote(json.dumps({"dashboard_url": dashboard_url}))
    error.details["resume"] = f"mammoth job wait {job_id} --input {document}"
    error.recovery_commands = [
        f"mammoth dashboard job-by-url {shlex.quote(dashboard_url)} {job_id}",
        error.details["resume"],
    ]
    return error


def running_handle(error: CliError, command_id: str) -> dict[str, Any] | None:
    """The ``status: running`` payload for a wait that ran out, else ``None``.

    Used by ``--return-running``: a job wait or pipeline wait that timed out is
    not a failure, so the caller gets the handle to resume with instead.
    """
    details = error.details
    if error.code != "timeout" or "resume" not in details:
        return None
    if details.get("phase") == "pipeline" and "dataview_id" in details:
        handle: dict[str, Any] = {"dataview_id": details["dataview_id"]}
    elif "job_id" in details:
        handle = {"job_id": details["job_id"], **_observed_job_fields(details)}
    else:
        return None
    return {
        "status": "running",
        **handle,
        "command": command_id,
        "waited_seconds": details.get("waited_seconds"),
        "resume": details["resume"],
    }


def _retry_hint(retry_after: str | None) -> str:
    """How to retry a read that failed for a transient reason."""
    if retry_after:
        return f"Retry the read after {retry_after} s, as the server's Retry-After asks."
    return "Retry the read once; it changed nothing. If it fails again, tell the user."


#: A backend error ``name`` that refuses an action for lack of permission
#: (``DASHBOARD_CREATE_NOT_ALLOWED``) arrives as a 400, not a 403.
_NOT_ALLOWED_SUFFIX = "_NOT_ALLOWED"


def _not_allowed_reason(body: Any, status: int | None) -> str | None:
    """The backend's own reason when a 4xx refuses an action as not allowed."""
    if status is None or not 400 <= status < 500 or not isinstance(body, dict):
        return None
    name = body.get("name")
    message = body.get("message")
    if not isinstance(name, str) or not name.endswith(_NOT_ALLOWED_SUFFIX):
        return None
    return message if isinstance(message, str) and message else name


CODE_CLI_KEYS_NOT_ALLOWED = "cli_keys_not_allowed"
CODE_CLI_KEYS_NEED_BROWSER_SIGN_IN = "cli_keys_need_browser_sign_in"
CODE_CLI_KEY_EXPIRED = "cli_key_expired"
_TOKEN_EXPIRED_NAME = "API_TOKEN_EXPIRED"  # noqa: S105 - an error name
_TOKEN_REFUSED_NAME = "INVALID_TOKEN_FOR_CLIENT_APPS"  # noqa: S105 - an error name


def _is_cli_keys_refused(exc: BaseException) -> bool:
    """True for the server's refusal of an ``mm_`` token on the client-apps routes."""
    body = getattr(exc, "response_body", None)
    return isinstance(body, dict) and body.get("name") == _TOKEN_REFUSED_NAME


def _is_token_expired(exc: BaseException) -> bool:
    """True for the server's 401 naming an API key that is past its expiry."""
    body = getattr(exc, "response_body", None)
    return isinstance(body, dict) and body.get("name") == _TOKEN_EXPIRED_NAME


def _stored_credential_kind(profile: str | None) -> str | None:
    """The stored credential kind of ``profile`` (the selected one when None)."""
    credential = credentials.load_credential(profile or profiles.get_selected())
    return credential.kind if credential is not None else None


def map_sdk_exception(
    exc: BaseException,
    *,
    profile: str | None = None,
    project_id: int | None = None,
    workspace_id: int | None = None,
    non_member_project_id: int | None = None,
) -> CliError:
    """Map one SDK or transport failure to a typed, stable CLI outcome.

    Mutation timeouts and retry responses are *not* blanket-retryable: the SDK
    marks those calls ``outcome_unknown`` because the server may have committed
    the write while the response was lost.  A read timeout remains safely
    retryable.  This function only describes recovery; it never sends a second
    request.
    """
    if isinstance(exc, CliError):
        # Already a typed outcome (for example a login that could not refresh
        # mid-call); mapping it again would flatten it into a generic failure.
        return exc

    if isinstance(exc, KeyboardInterrupt):
        job_id = getattr(exc, "job_handle", None) or getattr(exc, "job_id", None)
        return interrupted_error(
            job_id=job_id,
            operation_state=getattr(exc, "operation_state", None),
            phase=getattr(exc, "phase", None),
            details=getattr(exc, "details", None),
        )

    if isinstance(exc, MammothAuthError) and _is_token_expired(exc):
        return CliError(
            code=CODE_CLI_KEY_EXPIRED,
            message="This API key has expired; run `mammoth auth login` to sign in again.",
            exit_status=EXIT_AUTH,
            hint="Sign in again to get a new key.",
            details=_metadata(exc),
            request_id=exc.request_id,
            recovery_commands=["mammoth auth login"],
        )

    if isinstance(exc, MammothAuthError):
        mismatch = _workspace_mismatch_error(exc, workspace_id)
        if mismatch is not None:
            return mismatch
        in_app = embedded.active()
        return CliError(
            code=CODE_AUTHENTICATION_FAILED,
            message="Mammoth rejected the provided credentials.",
            exit_status=EXIT_AUTH,
            hint=(
                EMBEDDED_AUTH_HINT
                if in_app
                else (
                    "Your sign-in may have expired or been revoked: "
                    "run `mammoth auth login` again, or check the API token."
                )
            ),
            details=_metadata(exc),
            request_id=exc.request_id,
            recovery_commands=[] if in_app else ["mammoth auth login"],
        )

    if isinstance(exc, MammothPipelineTimeoutError):
        recovery = _pipeline_recovery(exc, profile=profile)
        details = dict(exc.details)
        details["waited_seconds"] = details.get("timeout")
        details["resume"] = recovery[1]
        return CliError(
            code="timeout",
            message="The view pipeline did not finish before the timeout.",
            exit_status=EXIT_RETRYABLE,
            hint="No job is involved; read the view's pipeline state and wait for it to finish.",
            details=details,
            retryable=True,
            recovery_commands=recovery,
        )

    if isinstance(exc, MammothJobTimeoutError):
        job_id = getattr(exc, "job_handle", None) or getattr(exc, "job_id", None)
        details = dict(getattr(exc, "details", {}) or {})
        if job_id is not None:
            details.setdefault("job_id", job_id)
        details.setdefault("operation_state", "running")
        details.setdefault("phase", getattr(exc, "phase", None) or "polling")
        details.update(_observed_job_fields(details))
        details["waited_seconds"] = details.get("timeout")
        if job_id is not None:
            details["resume"] = _job_recovery(job_id, profile=profile)[1]
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
        details["status"] = "failure"
        details["reason"] = details.get("failure_reason") or "no reason recorded by the job"
        details.update(_observed_job_fields(details))
        return CliError(
            code=CODE_JOB_FAILED,
            message=f"The Mammoth job failed: {details['reason']}",
            exit_status=EXIT_API,
            hint="Inspect the job response for the failure reason.",
            details=details,
            recovery_commands=(
                _job_recovery(job_id, profile=profile)[:1] if job_id is not None else []
            ),
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
        method = getattr(exc, "method", None) or details.get("method")
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
                    f"--input '{{\"dataset_id\": {dataset_id}}}'"
                ]
            elif not recovery and valid_scope:
                recovery = [
                    f"mammoth view pipeline items-all {dataview_id} --project {recovery_project_id}"
                    f"{' --profile ' + shlex.quote(profile) if profile else ''} "
                    f"--input '{{\"dataset_id\": {dataset_id}}}'"
                ]

        # A complete destination was intentionally not published by the SDK
        # when a local write failed (for example ENOSPC).  This is a terminal
        # artifact error, not an invitation to replay a remote export job.
        if details.get("errno") is not None:
            return CliError(
                code="download_failed",
                message="The export could not be saved locally; the destination was not replaced.",
                exit_status=EXIT_API,
                hint=str(
                    details.get(
                        "recovery_hint",
                        "Free disk space or choose another destination, then inspect the "
                        "export job before downloading again.",
                    )
                ),
                details=details,
                request_id=request_id,
                recovery_commands=recovery,
            )

        # Missing metadata must never be interpreted as a safe read. Likewise,
        # a write with a lost/gateway response can have committed even when an
        # older SDK did not attach ``operation_state=outcome_unknown``.
        uncertain_effect = operation_state == "outcome_unknown" or (
            not _is_known_read(method)
            and (
                status is None
                or status in {408, 425}  # 429 refused the request before any effect
                or (status is not None and status >= 500)
            )
        )
        if uncertain_effect:
            if not recovery:
                recovery = _resource_recovery(
                    method, details.get("endpoint"), project_id, profile=profile
                )
            details.setdefault("operation_state", CODE_OUTCOME_UNKNOWN)
            if method is None:
                details.setdefault("metadata_missing", ["method", "operation_state"])
            if workspace_id is not None:
                details.setdefault("workspace_id", workspace_id)
            if project_id is not None:
                details.setdefault("project_id", project_id)
            return CliError(
                code=CODE_OUTCOME_UNKNOWN,
                message="The request may have committed, but its outcome was not confirmed.",
                exit_status=EXIT_RETRYABLE,
                hint=(
                    "Do not replay this operation. Inspect the observed job/resource "
                    "and original request context before taking any further mutation."
                ),
                details=details,
                request_id=request_id,
                retryable=False,
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
        if status == 403 and non_member_project_id is not None:
            return CliError(
                code=CODE_AUTHORIZATION_REQUIRED,
                message=f"You are not a member of project {non_member_project_id}.",
                exit_status=EXIT_AUTH,
                hint=(
                    "Project lists show only the projects you belong to. Ask a project "
                    "admin to add you; a workspace owner can see the project but cannot "
                    "open it without being a member."
                ),
                details=details,
                request_id=request_id,
                authorization_required=True,
            )
        if (
            status == 403
            and _is_cli_keys_refused(exc)
            and _stored_credential_kind(profile) == "token"
        ):
            return CliError(
                code=CODE_CLI_KEYS_NEED_BROWSER_SIGN_IN,
                message=(
                    "This call used an API token, and the server refuses API tokens when "
                    "creating or listing API keys; run `mammoth auth login` (browser "
                    "sign-in) and try again."
                ),
                exit_status=EXIT_AUTH,
                hint="Sign in with the browser, not an API token, to manage API keys.",
                details=details,
                request_id=request_id,
                recovery_commands=["mammoth auth login"],
            )
        if status == 403 and _is_cli_keys_refused(exc):
            return CliError(
                code=CODE_CLI_KEYS_NOT_ALLOWED,
                message=(
                    "This server doesn't allow CLI-created keys yet; create one in "
                    "Settings → API keys, then `mammoth auth login --method token`."
                ),
                exit_status=EXIT_AUTH,
                hint="A browser sign-in cannot create API keys on this server.",
                details=details,
                request_id=request_id,
                recovery_commands=["mammoth auth login --method token"],
            )
        if status == 403:
            return CliError(
                code=CODE_AUTHORIZATION_REQUIRED,
                message="Mammoth denied access to the requested resource or operation.",
                exit_status=EXIT_AUTH,
                hint=(
                    "Check the ids and scope first: a view id given with another dataset's id, "
                    "or an id from a different project, is refused the same way. Then ask an "
                    "administrator for permission. "
                    "An API token limited to one project gets this in every other "
                    "project, including one it created: pass that project's --project ID, "
                    "or log in with a token created without a project."
                ),
                details=details,
                request_id=request_id,
                authorization_required=True,
            )
        not_allowed = _not_allowed_reason(exc.response_body, status)
        if not_allowed is not None:
            return CliError(
                code=CODE_AUTHORIZATION_REQUIRED,
                message=not_allowed,
                exit_status=EXIT_AUTH,
                hint=(
                    "This user lacks the permission for this action here. Do not retry or "
                    "work around it: tell the user what is blocked and who can grant it."
                ),
                details=details,
                request_id=request_id,
                authorization_required=True,
            )
        if status == 413:
            # The ingress in front of the API caps a request body (measured
            # on release 2026-09-19: a 16 MB upload passes, 60 MB does not);
            # the application never sees the file, so the body is a bare
            # "Request Entity Too Large" with no backend code.
            return CliError(
                code=CODE_INVALID_ARGUMENT,
                message="The request body is larger than Mammoth accepts.",
                exit_status=EXIT_USAGE,
                hint="Split the file (or compress it: .zip/.gz/.bz2/.7z are accepted) "
                "and upload the parts; see 'mammoth schema get file.upload'.",
                details=details,
                request_id=request_id,
                retryable=False,
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
        # A read that hit a gateway or capacity limit (502/504 from the edge,
        # 503, 429, 408/425) has no effect to reconcile: retry it.
        if status in _RETRYABLE_READ_STATUSES or (status is None and _is_known_read(method)):
            return CliError(
                code=CODE_RETRYABLE,
                message="Mammoth is temporarily unavailable or the request timed out.",
                exit_status=EXIT_RETRYABLE,
                hint=_retry_hint(exc.retry_after),
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

    if isinstance(exc, (MammothValidationError, MammothColumnError)):
        # The SDK rejected the arguments before any request was sent; its
        # message names the offending argument, so surface it instead of a
        # generic API-error envelope that hides what to change.
        return CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=str(getattr(exc, "message", None) or exc),
            exit_status=EXIT_USAGE,
            hint="Correct the listed argument; no request was sent.",
            details={
                "exception_type": type(exc).__name__,
                **dict(getattr(exc, "details", {}) or {}),
            },
        )

    if isinstance(exc, MammothError):
        return CliError(
            code=CODE_API_ERROR,
            message="Mammoth could not complete the operation.",
            exit_status=EXIT_API,
            hint="Inspect the structured details and correct the request.",
            details=dict(getattr(exc, "details", {}) or {}),
        )

    errors = getattr(exc, "errors", None)
    if type(exc).__name__ == "ValidationError" and callable(errors):
        # A pydantic validation failure: say which fields, not just the class
        # name, or the operator cannot tell what was wrong with the call.
        try:
            raw_errors = errors(include_url=False, include_input=False)
        except TypeError:
            raw_errors = errors()
        summary = [
            {
                "loc": ".".join(str(part) for part in item.get("loc", ())),
                "type": item.get("type"),
                "msg": item.get("msg"),
            }
            for item in list(raw_errors)[:10]
        ]
        return CliError(
            code=CODE_API_ERROR,
            message=(
                f"The SDK could not validate {getattr(exc, 'title', 'the payload')} "
                "against its model."
            ),
            exit_status=EXIT_API,
            hint="Compare the listed fields with 'mammoth schema get COMMAND_ID'.",
            details={
                "exception_type": "ValidationError",
                "model": getattr(exc, "title", None),
                "validation_errors": summary,
            },
        )

    return CliError(
        code=CODE_API_ERROR,
        message="The Mammoth operation failed unexpectedly.",
        exit_status=EXIT_API,
        details={"exception_type": type(exc).__name__},
    )
