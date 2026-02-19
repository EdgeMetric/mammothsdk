"""View management tools."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import error_response, format_view_info, get_manager, log_tool_call, success_response
from mammoth_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
@log_tool_call
async def list_views(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """List all views in a dataset.

    Args:
        dataset_id: The dataset ID.
    """
    try:
        manager = await get_manager(ctx)
        views = manager.client.views.list(dataset_id)
        result = [format_view_info(v) for v in views]
        return success_response(result, f"Found {len(result)} views")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in list_views")
        return error_response(e)


@mcp.tool()
@log_tool_call
async def get_view(ctx: Context, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
    """Get detailed metadata for a view, including all columns and their types.

    Args:
        view_id: The dataview ID.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        return success_response(format_view_info(view))
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in get_view")
        return error_response(e)


@mcp.tool()
@log_tool_call
async def create_view(
    ctx: Context,
    dataset_id: int,
    name: str = "View",
    clone_from: int | None = None,
) -> dict[str, Any]:
    """Create a new view in a dataset.

    Args:
        dataset_id: The dataset ID to create the view in.
        name: Name for the new view (default "View").
        clone_from: ID of an existing view to clone from (optional).
    """
    try:
        manager = await get_manager(ctx)
        view = manager.client.views.create(dataset_id, name=name, clone_from=clone_from)
        return success_response(format_view_info(view), f"Created view '{name}'")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in create_view")
        return error_response(e)


@mcp.tool()
@log_tool_call
async def delete_view(ctx: Context, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
    """Delete a view.

    Args:
        view_id: The dataview ID to delete.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = await get_manager(ctx)
        manager._ensure_project_for_view(view_id)
        manager.client.views.delete(view_id, dataset_id)
        manager.invalidate_view(view_id)
        return success_response(message=f"Deleted view {view_id}")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in delete_view")
        return error_response(e)
