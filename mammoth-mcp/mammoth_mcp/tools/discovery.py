"""Discovery tools — projects, datasets, file upload."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import error_response, success_response
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager


def _get_manager(ctx: Context) -> ClientManager:
    return ctx.request_context.lifespan_context["manager"]


@mcp.tool()
def list_projects(ctx: Context) -> dict[str, Any]:
    """List all projects in the current workspace."""
    try:
        manager = _get_manager(ctx)
        projects = manager.client.projects.list()
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
    except Exception as e:
        return error_response(e)


@mcp.tool()
def list_datasets(ctx: Context) -> dict[str, Any]:
    """List all datasets in the current project."""
    try:
        manager = _get_manager(ctx)
        datasets = manager.client.datasets.list()
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
    except Exception as e:
        return error_response(e)


@mcp.tool()
def get_dataset(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """Get detailed info about a dataset, including its views.

    Args:
        dataset_id: The dataset ID.
    """
    try:
        manager = _get_manager(ctx)
        ds = manager.client.datasets.get(dataset_id)
        return success_response(ds)
    except Exception as e:
        return error_response(e)


@mcp.tool()
def upload_file(ctx: Context, file_path: str) -> dict[str, Any]:
    """Upload a CSV or Excel file to create a new dataset.

    Args:
        file_path: Absolute path to the file on the local filesystem.
    """
    try:
        manager = _get_manager(ctx)
        result = manager.client.files.upload(file_path)
        return success_response(
            {"dataset_ids": result if isinstance(result, list) else [result]},
            "File uploaded successfully",
        )
    except Exception as e:
        return error_response(e)
