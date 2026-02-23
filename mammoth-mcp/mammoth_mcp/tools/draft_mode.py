"""Draft mode tools — preview transformations before committing them."""

from __future__ import annotations

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


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_task(
    ctx: Context,
    view_id: int,
    task_id: int,
) -> dict[str, Any]:
    """Delete (undo) a pipeline transformation step from a view.

    Args:
        view_id: The dataview ID.
        task_id: The pipeline task ID to remove.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    await run_sync(view.delete_task, task_id)
    return success_response(message=f"Deleted task {task_id} from view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def enter_draft_mode(ctx: Context, view_id: int) -> dict[str, Any]:
    """Enter draft mode on a view — transformations won't execute until submitted.

    In draft mode, pipeline tasks are queued but not run. Use preview_task to
    see what a transformation would produce, then submit_draft to execute all
    queued tasks at once, or discard_draft to cancel.

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.enter_draft_mode)
    return success_response(result, f"Entered draft mode on view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def submit_draft(ctx: Context, view_id: int) -> dict[str, Any]:
    """Submit and execute all queued draft transformations on a view.

    This commits all tasks added during draft mode and runs the pipeline.

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.submit_draft)
    return success_response(result, f"Submitted draft for view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def discard_draft(ctx: Context, view_id: int) -> dict[str, Any]:
    """Discard all queued draft transformations on a view.

    This cancels draft mode and removes all pending tasks without executing them.

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.discard_draft)
    return success_response(result, f"Discarded draft for view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def set_auto_run(
    ctx: Context,
    view_id: int,
    enabled: bool,
) -> dict[str, Any]:
    """Enable or disable auto-run on a view's pipeline.

    When auto-run is disabled, new tasks are queued but not executed automatically.

    Args:
        view_id: The dataview ID.
        enabled: True to enable auto-run, False to disable.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.set_auto_run, enabled)
    state = "enabled" if enabled else "disabled"
    return success_response(result, f"Auto-run {state} for view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def preview_task(
    ctx: Context,
    view_id: int,
    task_spec: dict[str, Any],
) -> dict[str, Any]:
    """Preview what a transformation would produce without actually applying it.

    Returns sample output rows showing the effect of the transformation.

    Args:
        view_id: The dataview ID.
        task_spec: The transformation task specification (same format as pipeline tasks).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(view.preview_task, task_spec)
    return success_response(result, "Task preview generated")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_pipeline(ctx: Context, view_id: int) -> dict[str, Any]:
    """Get the full pipeline definition for a view (all tasks and their specs).

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(
        manager.client.pipeline.get_pipeline, view.id, dataset_id=view.dataset_id
    )
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def get_task(
    ctx: Context,
    view_id: int,
    task_id: int,
) -> dict[str, Any]:
    """Get the full specification of a single pipeline task.

    Args:
        view_id: The dataview ID.
        task_id: The pipeline task ID (from list_tasks).
    """
    manager = await get_manager(ctx)
    view = await run_sync(manager.get_view, view_id)
    result = await run_sync(
        manager.client.pipeline.get_task,
        view.id,
        task_id,
        dataset_id=view.dataset_id,
    )
    return success_response(result)
