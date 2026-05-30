"""Connector tools — manage cloud data source connections and dataset configs."""

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
async def list_connectors(ctx: Context) -> dict[str, Any]:
    """List all available connector types (e.g. Salesforce, Google Sheets, Snowflake)."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.connectors.list)
    return success_response(result, f"Found {len(result)} connector type(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_connector(ctx: Context, connector_key: str) -> dict[str, Any]:
    """Get details of a specific connector type.

    Args:
        connector_key: The connector key (e.g. "salesforce", "google_sheets").
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.connectors.get, connector_key)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def list_active_connectors(ctx: Context) -> dict[str, Any]:
    """List connectors that have active connections in the workspace."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.connectors.active_connectors)
    return success_response(result, f"Found {len(result)} active connector(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def list_connections(
    ctx: Context,
    connector_key: str,
) -> dict[str, Any]:
    """List all connections for a connector type.

    Args:
        connector_key: The connector key (e.g. "salesforce").
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.connectors.list_connections, connector_key)
    return success_response(result, f"Found {len(result)} connection(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_connection(
    ctx: Context,
    connector_key: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new connection to a cloud data source.

    Args:
        connector_key: The connector key (e.g. "salesforce").
        config: Connection configuration (credentials, endpoint, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.connectors.create_connection, connector_key, config)
    return success_response(result, f"Created connection for {connector_key}")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_connection(
    ctx: Context,
    connector_key: str,
    connection_key: str,
) -> dict[str, Any]:
    """Get details of a specific connection.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.connectors.get_connection, connector_key, connection_key)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_connection(
    ctx: Context,
    connector_key: str,
    connection_key: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update an existing connection's configuration.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
        config: Updated connection configuration.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.update_connection,
        connector_key,
        connection_key,
        config,
    )
    return success_response(result, f"Updated connection {connection_key}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_connection(
    ctx: Context,
    connector_key: str,
    connection_key: str,
) -> dict[str, Any]:
    """Delete a connection permanently.

    Args:
        connector_key: The connector key.
        connection_key: The connection key to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.delete_connection, connector_key, connection_key
    )
    return success_response(result, f"Deleted connection {connection_key}")


@mcp.tool()
@log_tool_call
@handle_errors
async def list_connector_datasets(
    ctx: Context,
    connector_key: str,
    connection_key: str,
) -> dict[str, Any]:
    """List dataset configurations for a connection.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.list_ds_configs, connector_key, connection_key
    )
    return success_response(result, f"Found {len(result)} dataset config(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_connector_dataset(
    ctx: Context,
    connector_key: str,
    connection_key: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new dataset configuration to import data from a connection.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
        config: Dataset import configuration (tables, queries, schedules, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.create_ds_config,
        connector_key,
        connection_key,
        config,
    )
    return success_response(result, "Created connector dataset config")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_connector_dataset(
    ctx: Context,
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
) -> dict[str, Any]:
    """Get details of a connector dataset configuration.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
        ds_config_key: The dataset configuration key.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.get_ds_config,
        connector_key,
        connection_key,
        ds_config_key,
    )
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_connector_dataset(
    ctx: Context,
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update a connector dataset configuration.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
        ds_config_key: The dataset configuration key.
        config: Updated dataset configuration.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.update_ds_config,
        connector_key,
        connection_key,
        ds_config_key,
        config,
    )
    return success_response(result, f"Updated dataset config {ds_config_key}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_connector_dataset(
    ctx: Context,
    connector_key: str,
    connection_key: str,
    ds_config_key: str,
) -> dict[str, Any]:
    """Delete a connector dataset configuration.

    Args:
        connector_key: The connector key.
        connection_key: The connection key.
        ds_config_key: The dataset configuration key to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.connectors.delete_ds_config,
        connector_key,
        connection_key,
        ds_config_key,
    )
    return success_response(result, f"Deleted dataset config {ds_config_key}")
