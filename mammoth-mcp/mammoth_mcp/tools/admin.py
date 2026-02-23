"""Admin tools — workspace management, users, API keys, activity logs."""

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

# ── Workspaces ───────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_workspaces(ctx: Context) -> dict[str, Any]:
    """List all workspaces accessible to the current user."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.workspaces.list)
    return success_response(result, "Listed workspaces")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_workspace(
    ctx: Context,
    workspace_id: int | None = None,
) -> dict[str, Any]:
    """Get details of a workspace.

    Args:
        workspace_id: Workspace ID (default: current workspace).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.workspaces.get, workspace_id=workspace_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_workspace(
    ctx: Context,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update workspace settings.

    Args:
        config: Workspace settings to update (name, settings, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.workspaces.update, config)
    return success_response(result, "Updated workspace")


@mcp.tool()
@log_tool_call
@handle_errors
async def list_workspace_users(ctx: Context) -> dict[str, Any]:
    """List all users in the current workspace."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.workspaces.list_users)
    return success_response(result, f"Found {len(result)} user(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_workspace_user(ctx: Context, user_id: str) -> dict[str, Any]:
    """Get details of a specific workspace user.

    Args:
        user_id: The user ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.workspaces.get_user, user_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_workspace_user(
    ctx: Context,
    user_id: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update a workspace user's role or settings.

    Args:
        user_id: The user ID.
        config: User settings to update (role, permissions, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.workspaces.update_user, user_id, config)
    return success_response(result, f"Updated user {user_id}")


# ── User Profile ─────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def get_user_profile(ctx: Context) -> dict[str, Any]:
    """Get the current user's profile information."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.user_profile.get)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_user_profile(
    ctx: Context,
    fields: dict[str, Any],
) -> dict[str, Any]:
    """Update the current user's profile.

    Args:
        fields: Profile fields to update (name, email, timezone, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.user_profile.update, **fields)
    return success_response(result, "Updated user profile")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_user_preferences(ctx: Context) -> dict[str, Any]:
    """Get the current user's preference settings."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.user_profile.get_preferences)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_user_preferences(
    ctx: Context,
    preferences: dict[str, Any],
) -> dict[str, Any]:
    """Update the current user's preferences.

    Args:
        preferences: Preference settings to update.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.user_profile.update_preferences, **preferences)
    return success_response(result, "Updated user preferences")


# ── External Keys (API Keys) ────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_external_keys(ctx: Context) -> dict[str, Any]:
    """List all external API keys in the workspace."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.external_keys.list)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def get_external_key(ctx: Context, key_id: int) -> dict[str, Any]:
    """Get details of a specific external API key.

    Args:
        key_id: The external key ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.external_keys.get, key_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def create_external_key(
    ctx: Context,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new external API key (e.g. OpenAI key for ai_transform).

    Args:
        config: Key configuration (provider, key value, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.external_keys.create, config)
    return success_response(result, "Created external key")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_external_key(ctx: Context, key_id: int) -> dict[str, Any]:
    """Delete an external API key.

    Args:
        key_id: The external key ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.external_keys.delete, key_id)
    return success_response(result, f"Deleted external key {key_id}")


# ── Activity Logs ────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_activity_logs(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
    sort: str | None = None,
) -> dict[str, Any]:
    """List activity logs for the workspace (audit trail).

    Args:
        limit: Maximum number of log entries (default 50).
        offset: Number of entries to skip for pagination.
        sort: Sort order (e.g. "(created_at:desc)").
    """
    manager = await get_manager(ctx)
    kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
    if sort:
        kwargs["sort"] = sort
    result = await run_sync(manager.client.activity_logs.list, **kwargs)
    return success_response(result, "Listed activity logs")


@mcp.tool()
@log_tool_call
@handle_errors
async def export_activity_logs(
    ctx: Context,
    format: str = "csv",
) -> dict[str, Any]:
    """Export activity logs to a file.

    Args:
        format: Export format (default "csv").
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.activity_logs.export, format=format)
    return success_response(result, f"Exported activity logs as {format}")


# ── Reports ──────────────────────────────────────────────────


@mcp.tool()
@log_tool_call
@handle_errors
async def list_reports(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List available reports in the workspace.

    Args:
        limit: Maximum number of reports (default 50).
        offset: Number of reports to skip for pagination.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.reports.list, limit=limit, offset=offset)
    return success_response(result, "Listed reports")
