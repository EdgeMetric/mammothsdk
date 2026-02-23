"""Automation and schedule tools — manage workflow automations and schedules."""

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

# ── Automations ──────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_automations(ctx: Context) -> dict[str, Any]:
    """List all automations in the workspace."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.automations.list)
    return success_response(result, f"Found {len(result)} automation(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_automation(
    ctx: Context,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new automation workflow.

    Args:
        config: Automation configuration (triggers, actions, schedule, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.automations.create, config)
    return success_response(result, "Created automation")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_automation(ctx: Context, automation_id: int) -> dict[str, Any]:
    """Get details of a specific automation.

    Args:
        automation_id: The automation ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.automations.get, automation_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_automation(
    ctx: Context,
    automation_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update an existing automation.

    Args:
        automation_id: The automation ID.
        config: Updated automation configuration.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.automations.update, automation_id, config)
    return success_response(result, f"Updated automation {automation_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_automation(ctx: Context, automation_id: int) -> dict[str, Any]:
    """Delete an automation permanently.

    Args:
        automation_id: The automation ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.automations.delete, automation_id)
    return success_response(result, f"Deleted automation {automation_id}")


# ── Schedules ────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_schedules(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List all schedules in the current project.

    Args:
        limit: Maximum number of schedules to return (default 50).
        offset: Number of schedules to skip for pagination.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.schedules.list, limit=limit, offset=offset)
    return success_response(result, "Listed schedules")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_schedule(
    ctx: Context,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new schedule for automated data processing.

    Args:
        config: Schedule configuration (cron expression, actions, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.schedules.create, config)
    return success_response(result, "Created schedule")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_schedule(ctx: Context, schedule_id: int) -> dict[str, Any]:
    """Get details of a specific schedule.

    Args:
        schedule_id: The schedule ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.schedules.get, schedule_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_schedule(
    ctx: Context,
    schedule_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update an existing schedule.

    Args:
        schedule_id: The schedule ID.
        config: Updated schedule configuration.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.schedules.update, schedule_id, config)
    return success_response(result, f"Updated schedule {schedule_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_schedule(ctx: Context, schedule_id: int) -> dict[str, Any]:
    """Delete a schedule permanently.

    Args:
        schedule_id: The schedule ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.schedules.delete, schedule_id)
    return success_response(result, f"Deleted schedule {schedule_id}")
