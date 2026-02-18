"""Custom exceptions for the Mammoth Analytics SDK."""

from __future__ import annotations

from typing import Any


class MammothError(Exception):
    """Base exception for Mammoth SDK errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MammothAPIError(MammothError):
    """Exception raised for API-related errors."""

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
    """Exception raised for authentication-related errors."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401)


class MammothJobTimeoutError(MammothError):
    """Exception raised when a job times out."""

    def __init__(self, job_id: int, timeout_seconds: int) -> None:
        message = f"Job {job_id} timed out after {timeout_seconds} seconds"
        super().__init__(message, {"job_id": job_id, "timeout": timeout_seconds})


class MammothJobFailedError(MammothError):
    """Exception raised when a job fails."""

    def __init__(self, job_id: int, failure_reason: str | None = None) -> None:
        message = f"Job {job_id} failed"
        if failure_reason:
            message += f": {failure_reason}"
        super().__init__(message, {"job_id": job_id, "failure_reason": failure_reason})


class MammothTransformError(MammothError):
    """Exception raised when a transformation task fails."""

    def __init__(
        self,
        message: str,
        task_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details or {})
        self.task_key = task_key


class MammothColumnError(MammothError):
    """Exception raised when a column name cannot be resolved."""

    def __init__(self, column_name: str, available_columns: list[str] | None = None) -> None:
        available = f". Available columns: {available_columns}" if available_columns else ""
        message = f"Column '{column_name}' not found{available}"
        super().__init__(
            message,
            {"column_name": column_name, "available_columns": available_columns},
        )
