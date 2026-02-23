"""Client app tools — manage API tokens and client applications."""

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
async def list_client_apps(ctx: Context) -> dict[str, Any]:
    """List all client applications (API tokens) in the workspace."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.client_apps.list)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, "Listed client apps")


@mcp.tool()
@log_tool_call
@handle_errors
async def create_client_app(
    ctx: Context,
    app_name: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a new client application (API token pair).

    Args:
        app_name: Application name.
        description: Optional description.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.client_apps.create, app_name, description=description)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, f"Created client app '{app_name}'")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_client_app(ctx: Context, client_key: str) -> dict[str, Any]:
    """Get details of a specific client application.

    Args:
        client_key: The client application key.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.client_apps.get, client_key)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data)


@mcp.tool()
@log_tool_call
@handle_errors
async def update_client_app(
    ctx: Context,
    client_key: str,
    patch_data: dict[str, Any],
) -> dict[str, Any]:
    """Update a client application's settings.

    Args:
        client_key: The client application key.
        patch_data: Patch request with a "patch" key containing a list of
            operations, each with "op", "path", and optionally "value".
            Example: {"patch": [{"op": "replace", "path": "/app_name", "value": "New Name"}]}
    """
    from mammoth.models.clientapps import PatchRequest

    manager = await get_manager(ctx)
    patch_request = PatchRequest(**patch_data)
    result = await run_sync(manager.client.client_apps.update, client_key, patch_request)
    data = result.model_dump() if hasattr(result, "model_dump") else result
    return success_response(data, f"Updated client app {client_key}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_client_app(ctx: Context, client_key: str) -> dict[str, Any]:
    """Delete a client application and revoke its API tokens.

    Args:
        client_key: The client application key to delete.
    """
    manager = await get_manager(ctx)
    await run_sync(manager.client.client_apps.delete, client_key)
    return success_response(message=f"Deleted client app {client_key}")
