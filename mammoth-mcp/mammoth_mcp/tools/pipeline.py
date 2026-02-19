"""Pipeline management tools."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import error_response, success_response
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager

logger = logging.getLogger(__name__)


def _get_manager(ctx: Context) -> ClientManager:
    try:
        return ctx.request_context.lifespan_context["manager"]
    except KeyError:
        raise RuntimeError("MCP server not initialized — check environment variables")


@mcp.tool()
def list_tasks(ctx: Context, view_id: int, dataset_id: int | None = None) -> dict[str, Any]:
    """List all pipeline transformation steps applied to a view.

    Args:
        view_id: The dataview ID.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = _get_manager(ctx)
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
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in list_tasks")
        return error_response(e)


@mcp.tool()
def delete_task(
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
    try:
        manager = _get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        view.delete_task(task_id)
        return success_response(message=f"Deleted task {task_id} from view {view_id}")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in delete_task")
        return error_response(e)
