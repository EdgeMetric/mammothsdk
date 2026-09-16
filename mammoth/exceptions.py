"""Custom exceptions for the Mammoth Analytics SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_SECRET_FIELDS = frozenset(
    {
        "authorization",
        "proxy_authorization",
        "cookie",
        "set_cookie",
        "api_key",
        "api_secret",
        "x_api_key",
        "x_api_secret",
        "access_token",
        "refresh_token",
        "id_token",
        "bearer_token",
        "password",
        "passphrase",
        "private_key",
        "client_secret",
    }
)

# These response sections are conventionally maps of credentials/HTTP
# headers.  Redact the section as a whole, while leaving ordinary business
# fields such as ``token_count`` and ``secret_sauce`` untouched.
_SECRET_CONTAINERS = frozenset(
    {"credentials", "credential", "auth", "authentication", "headers", "request_headers", "secrets"}
)


def _is_secret_field(name: object) -> bool:
    normalized = str(name).lower().replace("-", "_").replace(" ", "_")
    return normalized in _SECRET_FIELDS or normalized in _SECRET_CONTAINERS


def safe_response_body(value: object) -> dict[str, Any]:
    """Return a bounded, credential-safe representation of an API body.

    Error objects are often logged or serialized by callers.  Keep useful
    structured diagnostics while ensuring credential-bearing fields from an
    upstream response can never become part of the public exception.
    """

    def scrub(item: object, depth: int = 0) -> object:
        if depth > 8:
            return "<nested value omitted>"
        if isinstance(item, Mapping):
            return {
                str(key): "<redacted>" if _is_secret_field(key) else scrub(val, depth + 1)
                for key, val in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [scrub(val, depth + 1) for val in item[:100]]
        if isinstance(item, (str, int, float, bool)) or item is None:
            return item
        return str(item)

    result = scrub(value)
    return result if isinstance(result, dict) else {}


def _metadata_details(
    *,
    details: dict[str, Any] | None,
    method: str | None,
    request_id: str | None,
    retry_after: str | None,
    operation_state: str | None,
    phase: str | None,
    job_handle: object | None,
    resource_handle: object | None,
) -> dict[str, Any]:
    metadata = dict(details or {})
    for key, value in (
        ("method", method),
        ("request_id", request_id),
        ("retry_after", retry_after),
        ("operation_state", operation_state),
        ("phase", phase),
        ("job_handle", job_handle),
        ("resource_handle", resource_handle),
    ):
        if value is not None:
            metadata.setdefault(key, value)
    return metadata


class MammothError(Exception):
    """Base exception for all Mammoth SDK errors.

    Attributes:
        message: Human-readable error description.
        details: Additional context dict (varies by subclass).
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MammothAPIError(MammothError):
    """Exception raised when the Mammoth API returns an error response.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code (e.g. 400, 404, 500), or ``None``.
        response_body: Raw JSON response body dict from the API.

    Example::

        try:
            client.datasets.get(dataset_id=99999)
        except MammothAPIError as e:
            print(e.status_code)     # 404
            print(e.response_body)   # {"detail": "Not found"}
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
        *,
        method: str | None = None,
        request_id: str | None = None,
        retry_after: str | None = None,
        operation_state: str | None = None,
        phase: str | None = None,
        job_handle: object | None = None,
        resource_handle: object | None = None,
        endpoint: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = safe_response_body(response_body or {})
        self.method = method
        self.request_id = request_id
        self.retry_after = retry_after
        self.operation_state = operation_state
        self.phase = phase
        self.job_handle = job_handle
        self.resource_handle = resource_handle
        self.endpoint = endpoint
        merged_details = _metadata_details(
            details=details,
            method=method,
            request_id=request_id,
            retry_after=retry_after,
            operation_state=operation_state,
            phase=phase,
            job_handle=job_handle,
            resource_handle=resource_handle,
        )
        super().__init__(message, merged_details)


class MammothAuthError(MammothAPIError):
    """Exception raised when API credentials are invalid (HTTP 401).

    Attributes:
        message: ``"Authentication failed"`` (default).
        status_code: Always ``401``.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        response_body: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=401, response_body=response_body, **kwargs)


class MammothJobTimeoutError(MammothError):
    """Exception raised when polling a job exceeds the timeout.

    Attributes:
        message: Description including job ID and timeout.
        details: ``{"job_id": int, "timeout": int}``.
    """

    def __init__(
        self,
        job_id: int,
        timeout_seconds: int,
        *,
        observed_job: dict[str, Any] | None = None,
        phase: str | None = "polling",
    ) -> None:
        message = f"Job {job_id} timed out after {timeout_seconds} seconds"
        details: dict[str, Any] = {
            "job_id": job_id,
            "timeout": timeout_seconds,
            "operation_state": "running",
            "phase": phase,
            "job_handle": job_id,
            "recovery_action": {
                "operation": "jobs.get_job",
                "job_id": job_id,
                "scope": "same workspace",
            },
        }
        if observed_job is not None:
            details["observed_job"] = safe_response_body(observed_job)
        super().__init__(message, details)
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds
        self.job_handle = job_id
        self.operation_state = "running"
        self.phase = phase


class MammothJobFailedError(MammothError):
    """Exception raised when a job completes with a failure status.

    Attributes:
        message: Description including job ID and failure reason.
        details: ``{"job_id": int, "failure_reason": str | None}``.
    """

    def __init__(
        self,
        job_id: int,
        failure_reason: str | None = None,
        *,
        observed_job: dict[str, Any] | None = None,
        phase: str | None = "polling",
    ) -> None:
        message = f"Job {job_id} failed"
        if failure_reason:
            message += f": {failure_reason}"
        details: dict[str, Any] = {
            "job_id": job_id,
            "failure_reason": failure_reason,
            "operation_state": "failed",
            "phase": phase,
            "job_handle": job_id,
        }
        if observed_job is not None:
            details["observed_job"] = safe_response_body(observed_job)
        super().__init__(message, details)
        self.job_id = job_id
        self.job_handle = job_id
        self.operation_state = "failed"
        self.phase = phase


class MammothTransformError(MammothError):
    """Exception raised when a pipeline transformation task fails.

    Attributes:
        message: Human-readable error description.
        task_key: The pipeline task key (e.g. ``"SET"``, ``"MATH"``).
        details: Additional context dict.
    """

    def __init__(
        self,
        message: str,
        task_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details or {})
        self.task_key = task_key


class MammothExportError(MammothError):
    """Exception raised when an export completes but its result can't be resolved.

    Internal-dataset exports (crosstab / branch-out) run as a fire-and-forget
    downstream action: the submit job returns immediately and the new dataset's
    id only appears on the export trigger once it reaches ``EXECUTED``. This is
    raised when that trigger never materialises a dataset id within the timeout.

    Attributes:
        message: Human-readable error description.
        details: Additional context dict (e.g. ``{"dataset_name": str,
            "timeout": int}``).

    Example::

        try:
            new_id = view.branch_out("Sales snapshot")
        except MammothExportError as exc:
            # The export was submitted but its dataset id didn't resolve in time.
            print(exc.details["dataset_name"], exc.details["timeout"])
    """


class MammothValidationError(MammothError):
    """Exception raised when SDK method arguments are invalid.

    Raised proactively — before any API call — when an argument or a
    combination of arguments cannot form a valid request (e.g. an aggregation
    that needs a value column was given none, or APPEND mode without a target
    dataset). The message states exactly what is wrong and how to fix it, so
    callers fail fast with an actionable error instead of an opaque backend one.

    Attributes:
        message: Description of exactly what is wrong and how to fix it.
        details: Additional context dict (the offending argument(s)).

    Example::

        try:
            view.crosstab(
                rows=["Region"], pivot_column="Product",
                select=CrosstabSpec(function=AggregateFunction.SUM),  # missing column
                dataset_name="x",
            )
        except MammothValidationError as e:
            print(e.message)  # "Crosstab SUM requires a value `column`."
    """


class MammothColumnError(MammothError):
    """Exception raised when a column display name cannot be resolved.

    Attributes:
        message: Description including the missing column name and
            available columns.
        details: ``{"column_name": str, "available_columns": list[str] | None}``.

    Example::

        try:
            view.filter_rows(Condition("NonExistent", Operator.EQ, 1))
        except MammothColumnError as e:
            print(e.details["column_name"])        # "NonExistent"
            print(e.details["available_columns"])   # ["Sales", "Region", ...]
    """

    def __init__(self, column_name: str, available_columns: list[str] | None = None) -> None:
        available = f". Available columns: {available_columns}" if available_columns else ""
        message = f"Column '{column_name}' not found{available}"
        super().__init__(
            message,
            {"column_name": column_name, "available_columns": available_columns},
        )


class MammothPaginationError(MammothError):
    """A paginated read could not prove forward progress.

    A ``next`` hint is advisory until the next page advances the cursor and
    contains new records.  This typed error lets callers stop safely when a
    backend repeats a page, returns an empty page with a continuation hint, or
    exceeds the caller's explicit page bound.
    """


class MammothDeletionVerificationError(MammothError):
    """A delete acknowledgement could not be reconciled to terminal absence."""
