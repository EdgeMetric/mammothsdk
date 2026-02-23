"""Discovery tools — projects, datasets, file upload."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import get_manager, handle_errors, log_tool_call, run_sync, success_response
from mammoth_mcp.server import mcp


@mcp.tool()
@log_tool_call
@handle_errors
async def list_projects(ctx: Context) -> dict[str, Any]:
    """List all projects in the current workspace."""
    manager = await get_manager(ctx)
    projects = await run_sync(manager.client.projects.list)
    items = projects if isinstance(projects, list) else projects.get("projects", [])
    result = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "description": p.get("description", ""),
        }
        for p in items
    ]
    return success_response(result, f"Found {len(result)} projects")


@mcp.tool()
@log_tool_call
@handle_errors
async def list_datasets(ctx: Context) -> dict[str, Any]:
    """List all datasets in the current project."""
    manager = await get_manager(ctx)
    datasets = await run_sync(manager.client.datasets.list)
    items = datasets if isinstance(datasets, list) else datasets.get("datasets", [])
    result = [
        {
            "id": d.get("id"),
            "name": d.get("name"),
            "description": d.get("description", ""),
            "dataview_count": d.get("dataview_count", 0),
        }
        for d in items
    ]
    return success_response(result, f"Found {len(result)} datasets")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_dataset(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """Get detailed info about a dataset, including its views.

    Args:
        dataset_id: The dataset ID.
    """
    manager = await get_manager(ctx)
    ds = await run_sync(manager.client.datasets.get, dataset_id)
    return success_response(ds)


@mcp.tool()
@log_tool_call
@handle_errors
async def upload_file(ctx: Context, file_path: str) -> dict[str, Any]:
    """Upload a CSV or Excel file to create a new dataset.

    Args:
        file_path: Absolute path to the file on the local filesystem.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.files.upload, file_path)
    return success_response(
        {"dataset_ids": result if isinstance(result, list) else [result]},
        "File uploaded successfully",
    )
