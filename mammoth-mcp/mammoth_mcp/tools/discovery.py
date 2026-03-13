"""Discovery tools — projects, datasets, file upload."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    get_manager,
    handle_errors,
    log_tool_call,
    run_sync,
    success_response,
)
from mammoth_mcp.server import mcp

logger = logging.getLogger(__name__)


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
    datasets = await run_sync(browse_project_datasets, manager.client)
    return success_response(datasets, f"Found {len(datasets)} datasets")


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


# ── Browse-based dataset discovery ───────────────────────────


def browse_project_datasets(client: Any) -> list[dict[str, Any]]:
    """Discover datasets in the current project using the browse API.

    Uses workspace browse + folder recursion instead of datasets.list(),
    which requires project-level permissions that resource-level API keys
    may not have.
    """
    ws = client.workspace_id
    proj = client.project_id
    if proj is None:
        raise ValueError("project_id must be set — call set_project first")

    browse_resp = client.browse.workspace_resources(workspace_id=ws, level=2)
    project_children: list[dict[str, Any]] = []
    for resource in browse_resp.get("resources", []):
        if resource.get("id") == proj:
            project_children = resource.get("children", [])
            break

    return _collect_datasets_from_browse(client, project_children, proj, ws)


def _collect_datasets_from_browse(
    client: Any,
    children: list[dict[str, Any]],
    project_id: int,
    workspace_id: int,
) -> list[dict[str, Any]]:
    """Recursively collect datasets from browse hierarchy."""
    datasets: list[dict[str, Any]] = []
    folders: list[dict[str, Any]] = []

    for child in children:
        child_type = child.get("type", "")
        if child_type == "datasource":
            datasets.append({
                "id": child["id"],
                "name": child.get("name", ""),
            })
        elif child_type == "label":
            folders.append(child)

    for folder in folders:
        try:
            resp = client.browse.folder_resources(
                folder_id=folder["id"],
                project_id=project_id,
                workspace_id=workspace_id,
                level=2,
            )
            all_children: list[dict[str, Any]] = []
            for sub_resource in resp.get("resources", []):
                all_children.extend(sub_resource.get("children", []))
            datasets.extend(
                _collect_datasets_from_browse(client, all_children, project_id, workspace_id)
            )
        except Exception:
            logger.warning("Failed to browse folder %s", folder.get("id"), exc_info=True)
            continue

    return datasets
