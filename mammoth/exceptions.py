"""Custom exceptions for the Mammoth Analytics SDK."""

from __future__ import annotations

from typing import Any


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
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body or {}
        super().__init__(message, details)


class MammothAuthError(MammothAPIError):
    """Exception raised when API credentials are invalid (HTTP 401).

    Attributes:
        message: ``"Authentication failed"`` (default).
        status_code: Always ``401``.
    """

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401)


class MammothJobTimeoutError(MammothError):
    """Exception raised when polling a job exceeds the timeout.

    Attributes:
        message: Description including job ID and timeout.
        details: ``{"job_id": int, "timeout": int}``.
    """

    def __init__(self, job_id: int, timeout_seconds: int) -> None:
        message = f"Job {job_id} timed out after {timeout_seconds} seconds"
        super().__init__(message, {"job_id": job_id, "timeout": timeout_seconds})


class MammothJobFailedError(MammothError):
    """Exception raised when a job completes with a failure status.

    Attributes:
        message: Description including job ID and failure reason.
        details: ``{"job_id": int, "failure_reason": str | None}``.
    """

    def __init__(self, job_id: int, failure_reason: str | None = None) -> None:
        message = f"Job {job_id} failed"
        if failure_reason:
            message += f": {failure_reason}"
        super().__init__(message, {"job_id": job_id, "failure_reason": failure_reason})


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
