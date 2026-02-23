"""View management tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    format_view_info,
    get_manager,
    handle_errors,
    log_tool_call,
    run_sync,
    success_response,
)
from mammoth_mcp.server import mcp


@mcp.tool()
@log_tool_call
@handle_errors
async def list_views(ctx: Context, dataset_id: int | None = None) -> dict[str, Any]:
    """List all views in a dataset.

    Args:
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    views = await run_sync(manager.client.views.list, dataset_id)
    result = [format_view_info(v) for v in views]
    return success_response(result, f"Found {len(result)} views")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_view(ctx: Context, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
    """Get detailed metadata for a view, including all columns and their types. Auto-discovers the project and dataset — no need to call set_project or list_projects first.

    Args:
        view_id: The dataview ID.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id, dataset_id)
    return success_response(format_view_info(view))


@mcp.tool()
@log_tool_call
@handle_errors
async def create_view(
    ctx: Context,
    dataset_id: int,
    name: str = "View",
    clone_from: int | None = None,
) -> dict[str, Any]:
    """Create a new view in a dataset. Use clone_from to safely experiment on a copy.

    Args:
        dataset_id: The dataset ID to create the view in.
        name: Name for the new view (default "View").
        clone_from: ID of an existing view to clone from (optional).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.client.views.create, dataset_id, name=name, clone_from=clone_from)
    return success_response(format_view_info(view), f"Created view '{name}'")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_view(ctx: Context, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
    """Permanently delete a view. This action is irreversible — the view and its pipeline are lost.

    Args:
        view_id: The dataview ID to delete.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    await run_sync(manager._ensure_project_for_view, view_id)
    await run_sync(manager.client.views.delete, view_id, dataset_id)
    manager.invalidate_view(view_id)
    return success_response(message=f"Deleted view {view_id}")
