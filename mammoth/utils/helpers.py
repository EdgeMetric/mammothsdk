"""Helper functions for the Mammoth Analytics SDK."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def format_date_range(from_date: datetime, to_date: datetime) -> str:
    """Format a date range for API queries.

    The backend parses only ``%Y-%m-%dT%H:%M:%S.%fZ``, so every value is sent in UTC with
    microseconds and a ``Z``: a timezone-aware value is converted to UTC first, a naive one is
    taken as UTC.

    Args:
        from_date: Start date.
        to_date: End date.

    Returns:
        Formatted date range string for API.
    """
    return f"(from:'{_backend_time(from_date)}',to:'{_backend_time(to_date)}')"


def _backend_time(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def validate_file_path(file_path: str | Path) -> Path:
    """Validate and normalize a file path.

    Args:
        file_path: File path to validate.

    Returns:
        Normalized Path object.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If path is not a file.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return path


def parse_job_ids(job_ids_str: str) -> list[int]:
    """Parse comma-separated job IDs string into list of integers.

    Args:
        job_ids_str: Comma-separated job IDs.

    Returns:
        List of job ID integers.

    Raises:
        ValueError: If any job ID is not a valid integer.
    """
    if not job_ids_str.strip():
        return []

    try:
        return [int(job_id.strip()) for job_id in job_ids_str.split(",")]
    except ValueError as e:
        raise ValueError(f"Invalid job ID format: {e}") from e
