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
async def list_views(ctx: Context) -> dict[str, Any]:
    """List all views across all datasets in the current project."""
    manager = await get_manager(ctx)
    views = await run_sync(manager.client.views.list)
    result = [format_view_info(v) for v in views]
    return success_response(result, f"Found {len(result)} views")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_view(ctx: Context, view_id: int) -> dict[str, Any]:
    """Get detailed metadata for a view, including all columns and their types. Auto-discovers the project and dataset — no need to call set_project or list_projects first.

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    return success_response(format_view_info(view))
