"""Extended AI tools — profiling, suggestions, data generation, query generation."""

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
async def generate_profile(
    ctx: Context,
    view_id: int,
) -> dict[str, Any]:
    """Generate an AI-powered data profile for a view (statistics, patterns, anomalies).

    Args:
        view_id: The dataview ID to profile.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.ai.generate_profile, view_id)
    return success_response(result, f"Generated profile for view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_suggestions(ctx: Context) -> dict[str, Any]:
    """Get AI-powered transformation suggestions for the current project."""
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.ai.get_suggestions)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def generate_data(
    ctx: Context,
    view_id: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Generate synthetic data for a view using AI.

    Args:
        view_id: The dataview ID to generate data for.
        config: Data generation configuration (row count, column rules, etc.).
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.ai.generate_data, view_id, config)
    return success_response(result, f"Generated data for view {view_id}")


@mcp.tool()
@log_tool_call
@handle_errors
async def get_data_gen_info(
    ctx: Context,
    view_id: int,
) -> dict[str, Any]:
    """Get data generation metadata for a view (column schemas, generation options).

    Args:
        view_id: The dataview ID.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.ai.get_data_gen_info, view_id)
    return success_response(result)


@mcp.tool()
@log_tool_call
@handle_errors
async def ai_query_gen(
    ctx: Context,
    connector_key: str,
    connection_key: str,
    prompt: str,
) -> dict[str, Any]:
    """Generate a database query from a natural language prompt using AI.

    Uses the schema of a connected database to generate an appropriate SQL query.

    Args:
        connector_key: The connector key (e.g. "postgres", "snowflake").
        connection_key: The connection key.
        prompt: Natural language description of the desired query.
    """
    manager = await get_manager(ctx)
    result = await run_sync(manager.client.ai.query_gen, connector_key, connection_key, prompt)
    return success_response(result, "Generated query from prompt")
