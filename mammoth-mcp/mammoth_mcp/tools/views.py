"""View management tools."""

from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)


@mcp.tool()
@log_tool_call
@handle_errors
async def list_views(ctx: Context) -> dict[str, Any]:
    """List all views across all datasets in the current project."""
    manager = await get_manager(ctx)
    views = await run_sync(_list_all_views, manager.client)
    return success_response(views, f"Found {len(views)} views")


def _list_all_views(client: Any) -> list[dict[str, Any]]:
    """List views across all datasets using browse API for dataset discovery."""
    from mammoth_mcp.tools.discovery import browse_project_datasets

    datasets = browse_project_datasets(client)
    ws = client.workspace_id
    proj = client.project_id

    all_views: list[dict[str, Any]] = []
    for ds in datasets:
        try:
            dv_resp = client.dataviews.list(
                dataset_id=ds["id"],
                workspace_id=ws,
                project_id=proj,
            )
            for dv in dv_resp.get("dataviews", []):
                all_views.append({
                    "id": dv.get("id"),
                    "name": dv.get("name", ""),
                    "dataset_id": ds["id"],
                    "dataset_name": ds["name"],
                })
        except Exception:
            logger.warning("Failed to list views for dataset %s", ds.get("id"), exc_info=True)
            continue

    return all_views


@mcp.tool()
@log_tool_call
@handle_errors
async def get_view(ctx: Context, view_id: int) -> dict[str, Any]:
    """Get detailed metadata for a view, including all columns and types.

    Auto-discovers the project and dataset — no need to call set_project first.

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    return success_response(format_view_info(view))
