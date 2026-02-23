"""Data retrieval and export tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    build_condition,
    get_manager,
    handle_errors,
    log_tool_call,
    run_sync,
    success_response,
)
from mammoth_mcp.server import mcp

_MAX_ROWS = 400


@mcp.tool()
@log_tool_call
@handle_errors
async def get_data(
    ctx: Context,
    view_id: int,
    limit: int = 100,
    offset: int = 1,
    columns: list[str] | None = None,
    condition: dict[str, Any] | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    """Fetch actual row data from a view with optional filtering, column selection, and pagination. Returns row values, not metadata — use get_view for column info and row count.

    Args:
        view_id: The dataview ID to fetch data from.
        limit: Number of rows to return (default 100, max 400).
        offset: 1-indexed starting row (default 1).
        columns: List of column display names to include (default all).
        condition: Filter condition as a JSON object. Simple: {"column": "Sales", "operator": "GTE", "value": 1000}. Compound: {"logic": "AND", "conditions": [...]}.
        sort: Sort specification string (e.g. "column_name:asc").
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)

    truncated = limit > _MAX_ROWS
    actual_limit = min(limit, _MAX_ROWS)

    cond_obj = build_condition(condition) if condition else None
    result = await run_sync(
        view.data,
        limit=actual_limit,
        offset=offset,
        columns=columns,
        condition=cond_obj,
        sort=sort,
    )

    message = None
    if truncated:
        message = (
            f"(Note: results limited to {_MAX_ROWS} rows. Request fewer rows for faster responses.)"
        )

    return success_response(result, message)


@mcp.tool()
@log_tool_call
@handle_errors
async def export_data(
    ctx: Context,
    view_id: int,
    format: str,
    # S3 options
    file_name: str | None = None,
    file_type: str = "csv",
    # email options
    recipients: list[str] | None = None,
    # dataset (branch out) options
    dest_dataset_id: int | None = None,
    column_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Export view data to CSV file, S3, email, or another dataset.

    Args:
        view_id: The dataview ID to export from.
        format: Export format — one of: csv, s3, email, dataset.
        file_name: (s3) Output filename (auto-generated if not provided).
        file_type: (s3) File format (default "csv").
        recipients: (email) List of email addresses.
        dest_dataset_id: (dataset) Target dataset ID for branch-out.
        column_mapping: (dataset) Column mapping dict (optional).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    fmt = format.lower()

    if fmt == "csv":
        path = await run_sync(view.export.to_csv)
        return success_response({"file_path": str(path)}, f"Exported to {path}")

    elif fmt == "s3":
        result = await run_sync(view.export.to_s3, file_name=file_name, file_type=file_type)
        return success_response(result, "Exported to S3")

    elif fmt == "email":
        if not recipients:
            raise ValueError("recipients is required for email export")
        result = await run_sync(view.export.to_email, recipients=recipients)
        return success_response(result, f"Emailed to {', '.join(recipients)}")

    elif fmt == "dataset":
        if not dest_dataset_id:
            raise ValueError("dest_dataset_id is required for dataset export")
        result = await run_sync(view.export.to_dataset, dest_dataset_id, column_mapping)
        return success_response(result, f"Branched out to dataset {dest_dataset_id}")

    else:
        raise ValueError(f"Unknown format '{format}'. Use: csv, s3, email, dataset")
