"""Connection and configuration tools."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import error_response, get_manager, handle_errors, log_tool_call, success_response
from mammoth_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
@log_tool_call
@handle_errors
async def test_connection(ctx: Context) -> dict[str, Any]:
    """Test that the Mammoth API credentials are valid and the connection works."""
    manager = await get_manager(ctx)
    ok = manager.client.test_connection()
    if ok:
        return success_response(manager.config.summary(), "Connection successful")
    raise RuntimeError("Connection failed — check API key/secret")


@mcp.tool()
@log_tool_call
@handle_errors
async def set_project(ctx: Context, project_id: int) -> dict[str, Any]:
    """Set the active project ID for subsequent API calls.

    Args:
        project_id: The Mammoth project ID to use.
    """
    manager = await get_manager(ctx)
    manager.set_project(project_id)
    return success_response(
        {"project_id": project_id},
        f"Active project set to {project_id}",
    )


@mcp.tool()
def parse_mammoth_url(url: str) -> dict[str, Any]:
    """Extract workspace, project, and view IDs from a Mammoth URL.

    Args:
        url: A Mammoth Analytics URL (e.g. https://app.mammoth.io/#/workspaces/11/projects/98/views/1039).
    """
    try:
        from mammoth import parse_path

        ids = parse_path(url)
        return success_response(ids)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in parse_mammoth_url")
        return error_response(e)
