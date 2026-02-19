"""Discovery tools — projects, datasets, file upload."""

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
def list_projects(ctx: Context) -> dict[str, Any]:
    """List all projects in the current workspace."""
    try:
        manager = _get_manager(ctx)
        projects = manager.client.projects.list()
        items = projects if isinstance(projects, list) else projects.get("projects", [])
        result = [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description", ""),
            }
            for p in items
        ]
        return success_response(result, f"Found {len(result)} projects")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in list_projects")
        return error_response(e)


@mcp.tool()
def list_datasets(ctx: Context) -> dict[str, Any]:
    """List all datasets in the current project."""
    try:
        manager = _get_manager(ctx)
        datasets = manager.client.datasets.list()
        items = datasets if isinstance(datasets, list) else datasets.get("datasets", [])
        result = [
            {
                "id": d.get("id"),
                "name": d.get("name"),
                "description": d.get("description", ""),
                "dataview_count": d.get("dataview_count", 0),
            }
            for d in items
        ]
        return success_response(result, f"Found {len(result)} datasets")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in list_datasets")
        return error_response(e)


@mcp.tool()
def get_dataset(ctx: Context, dataset_id: int) -> dict[str, Any]:
    """Get detailed info about a dataset, including its views.

    Args:
        dataset_id: The dataset ID.
    """
    try:
        manager = _get_manager(ctx)
        ds = manager.client.datasets.get(dataset_id)
        return success_response(ds)
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in get_dataset")
        return error_response(e)


@mcp.tool()
def upload_file(ctx: Context, file_path: str) -> dict[str, Any]:
    """Upload a CSV or Excel file to create a new dataset.

    Args:
        file_path: Absolute path to the file on the local filesystem.
    """
    try:
        manager = _get_manager(ctx)
        result = manager.client.files.upload(file_path)
        return success_response(
            {"dataset_ids": result if isinstance(result, list) else [result]},
            "File uploaded successfully",
        )
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in upload_file")
        return error_response(e)
