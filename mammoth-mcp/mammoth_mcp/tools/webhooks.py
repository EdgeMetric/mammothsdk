"""Webhook tools — manage webhook datasets for data ingestion."""

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
async def list_webhooks(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List all webhooks in the workspace.

    Args:
        limit: Maximum number of webhooks to return (default 50).
        offset: Number of webhooks to skip for pagination.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.webhooks.list, limit=limit, offset=offset)
    return success_response(result, f"Found {len(result)} webhook(s)")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_webhook(
    ctx: Context,
    name: str = "Generic Webhook",
    mode: str = "replace",
    origins: str = "*",
    is_secure: bool = False,
    folder_resource_id: str | None = None,
) -> dict[str, Any]:
    """Create a new webhook dataset for receiving data via HTTP.

    Args:
        name: Webhook name (default "Generic Webhook").
        mode: Data mode — "replace" (overwrite) or "combine" (append).
        origins: Allowed CORS origins (default "*" for all).
        is_secure: Whether to require authentication.
        folder_resource_id: Optional folder to place the webhook in.
    """
    manager = await get_manager(ctx)
    result = await run_sync(
        manager.client.webhooks.create,
        name=name,
        mode=mode,
        origins=origins,
        is_secure=is_secure,
        folder_resource_id=folder_resource_id,
    )
    return success_response(result, f"Created webhook '{name}'")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_webhook(ctx: Context, webhook_id: int) -> dict[str, Any]:
    """Get details of a specific webhook.

    Args:
        webhook_id: The webhook ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.webhooks.get, webhook_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_webhook(
    ctx: Context,
    webhook_id: int,
    mode: str | None = None,
    origins: str | None = None,
    is_secure: bool | None = None,
) -> dict[str, Any]:
    """Update an existing webhook's settings.

    Args:
        webhook_id: The webhook ID.
        mode: Data mode — "replace" or "combine".
        origins: Allowed CORS origins.
        is_secure: Whether to require authentication.
    """
    manager = await get_manager(ctx)
    kwargs: dict[str, Any] = {}
    if mode is not None:
        kwargs["mode"] = mode
    if origins is not None:
        kwargs["origins"] = origins
    if is_secure is not None:
        kwargs["is_secure"] = is_secure
    result = await run_sync(manager.client.webhooks.update, webhook_id, **kwargs)
    return success_response(result, f"Updated webhook {webhook_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_webhook(ctx: Context, webhook_id: int) -> dict[str, Any]:
    """Delete a webhook permanently.

    Args:
        webhook_id: The webhook ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.webhooks.delete, webhook_id)
    return success_response(result, f"Deleted webhook {webhook_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def send_webhook_data(
    ctx: Context,
    webhook_uri: str,
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    method: str = "POST",
) -> dict[str, Any]:
    """Send data to a webhook endpoint.

    Args:
        webhook_uri: The webhook URI path (from webhook details).
        data: JSON data to send (POST method).
        params: Query parameters (GET method).
        method: HTTP method — "POST" or "GET" (default POST).
    """
    manager = await get_manager(ctx)
    if method.upper() == "GET":
        result = await run_sync(manager.client.webhooks.send_data_get, webhook_uri, params=params)
    else:
        if not data:
            raise ValueError("data is required for POST webhook calls")
        result = await run_sync(manager.client.webhooks.send_data, webhook_uri, data)
    return success_response(result, f"Sent data to webhook via {method.upper()}")
