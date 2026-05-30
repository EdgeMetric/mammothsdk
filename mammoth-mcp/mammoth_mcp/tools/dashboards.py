"""Dashboard tools — manage dashboards, sharing, and queries."""

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
async def list_dashboards(ctx: Context) -> dict[str, Any]:
    """List all dashboards in the workspace."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.list)
    return success_response(result, f"Found {len(result)} dashboard(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_dashboard(
    ctx: Context,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new dashboard.

    Args:
        config: Dashboard configuration (name, layout, widgets, data sources, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.create, config)
    return success_response(result, "Created dashboard")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_dashboard(ctx: Context, dashboard_id: int) -> dict[str, Any]:
    """Get details of a specific dashboard.

    Args:
        dashboard_id: The dashboard ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.get, dashboard_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_dashboard(
    ctx: Context,
    dashboard_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update an existing dashboard.

    Args:
        dashboard_id: The dashboard ID.
        config: Updated dashboard configuration.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.update, dashboard_id, config)
    return success_response(result, f"Updated dashboard {dashboard_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_dashboard(ctx: Context, dashboard_id: int) -> dict[str, Any]:
    """Delete a dashboard permanently.

    Args:
        dashboard_id: The dashboard ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.delete, dashboard_id)
    return success_response(result, f"Deleted dashboard {dashboard_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def share_dashboard(
    ctx: Context,
    dashboard_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Share a dashboard with users or make it public.

    Args:
        dashboard_id: The dashboard ID.
        config: Sharing configuration (users, permissions, public URL settings).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.share, dashboard_id, config)
    return success_response(result, f"Shared dashboard {dashboard_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def list_dashboard_sources(ctx: Context) -> dict[str, Any]:
    """List available data sources for dashboards (views that can be used as widgets)."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.get_sources)
    return success_response(result, f"Found {len(result)} dashboard source(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def query_dashboard(
    ctx: Context,
    dashboard_id: int,
    sql: str,
) -> dict[str, Any]:
    """Query a dashboard's draft data using SQL.

    Args:
        dashboard_id: The dashboard ID.
        sql: SQL query to run against the dashboard's data sources.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.get_draft_data, dashboard_id, sql)
    return success_response(result, "Dashboard query executed")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_dashboard_analytics(
    ctx: Context,
    dashboard_id: int,
) -> dict[str, Any]:
    """Get usage analytics for a dashboard (views, interactions).

    Args:
        dashboard_id: The dashboard ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.get_analytics, dashboard_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def get_dashboard_by_url(ctx: Context, url: str) -> dict[str, Any]:
    """Look up a dashboard by its public or shared URL.

    Args:
        url: The dashboard URL.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.get_by_url, url)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def query_published_dashboard(
    ctx: Context,
    dashboard_id: int,
    sql: str,
) -> dict[str, Any]:
    """Query a published dashboard's data using SQL.

    Args:
        dashboard_id: The dashboard ID.
        sql: SQL query to run against the published dashboard data.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.dashboards.get_publish_data, dashboard_id, sql)
    return success_response(result, "Published dashboard query executed")
