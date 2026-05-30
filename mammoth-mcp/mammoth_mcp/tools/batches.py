"""Batch tools — manage dataset batch imports."""

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
async def list_batches(
    ctx: Context,
    dataset_id: int,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List all batches for a dataset.

    Args:
        dataset_id: The dataset ID.
        limit: Maximum number of batches to return (default 50).
        offset: Number of batches to skip for pagination.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.batches.list, dataset_id, limit=limit, offset=offset)
    return success_response(result, "Listed batches")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_batch(
    ctx: Context,
    dataset_id: int,
    batch_id: int,
) -> dict[str, Any]:
    """Get details of a specific batch.

    Args:
        dataset_id: The dataset ID.
        batch_id: The batch ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.batches.get, dataset_id, batch_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def create_batch(
    ctx: Context,
    dataset_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new batch import for a dataset.

    Args:
        dataset_id: The dataset ID to add the batch to.
        config: Batch configuration (source, mapping, schedule, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.batches.create, dataset_id, config)
    return success_response(result, f"Created batch for dataset {dataset_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def update_batch(
    ctx: Context,
    dataset_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Update an existing batch configuration.

    Args:
        dataset_id: The dataset ID.
        config: Updated batch configuration.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.batches.update, dataset_id, config)
    return success_response(result, f"Updated batch for dataset {dataset_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def delete_batch(
    ctx: Context,
    dataset_id: int,
    batch_id: int,
) -> dict[str, Any]:
    """Delete a batch from a dataset.

    Args:
        dataset_id: The dataset ID.
        batch_id: The batch ID to delete.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.batches.delete, dataset_id, batch_id)
    return success_response(result, f"Deleted batch {batch_id}")
