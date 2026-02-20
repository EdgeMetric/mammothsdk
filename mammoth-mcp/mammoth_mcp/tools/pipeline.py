"""Pipeline management tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import get_manager, handle_errors, log_tool_call, run_sync, success_response
from mammoth_mcp.server import mcp


@mcp.tool()
@log_tool_call
@handle_errors
async def list_tasks(ctx: Context, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
    """List all pipeline transformation steps applied to a view.

    Args:
        view_id: The dataview ID.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    tasks = view.list_tasks()
    result = []
    for t in tasks:
        result.append({
            "id": t.get("id"),
            "sequence": t.get("sequence"),
            "task_key": t.get("task_key"),
            "status": t.get("status"),
            "params": t.get("params"),
        })
    return success_response(result, f"View has {len(result)} pipeline tasks")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_task(
    ctx: Context,
    view_id: int,
    task_id: int,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Delete (undo) a pipeline transformation step from a view.

    Args:
        view_id: The dataview ID.
        task_id: The pipeline task ID to remove.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    await run_sync(view.delete_task, task_id)
    return success_response(message=f"Deleted task {task_id} from view {view_id}")
