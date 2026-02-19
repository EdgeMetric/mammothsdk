"""AI-powered transformation tools."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from mammoth.exceptions import MammothAPIError, MammothColumnError
from mammoth_mcp.helpers import error_response, format_view_info, success_response
from mammoth_mcp.server import mcp
from mammoth_mcp.state import ClientManager

logger = logging.getLogger(__name__)


def _get_manager(ctx: Context) -> ClientManager:
    try:
        return ctx.request_context.lifespan_context["manager"]
    except KeyError:
        raise RuntimeError("MCP server not initialized — check environment variables")


@mcp.tool()
def ai_transform(
    ctx: Context,
    view_id: int,
    prompt: str,
    context_columns: list[str],
    new_column: str = "AI Result",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Use AI to generate a new column based on a natural language prompt and existing column data.

    Args:
        view_id: The dataview ID.
        prompt: Natural language instruction for the AI (e.g. "Classify the sentiment of the review").
        context_columns: List of column display names to provide as context to the AI.
        new_column: Name for the AI output column (default "AI Result").
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = _get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)
        view.gen_ai(
            prompt=prompt,
            context_columns=context_columns,
            new_column=new_column,
        )
        return success_response(format_view_info(view), "AI transform applied")
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in ai_transform")
        return error_response(e)


@mcp.tool()
def sql_query(
    ctx: Context,
    view_id: int,
    intent: str | None = None,
    raw_sql: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Transform data using SQL — either natural language intent or raw SQL.

    Provide either `intent` (natural language, auto-generates SQL) or `raw_sql` (direct SQL query).

    Args:
        view_id: The dataview ID.
        intent: Natural language description of the query (e.g. "count employees by department").
        raw_sql: Raw SQL query string to apply directly.
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    try:
        manager = _get_manager(ctx)
        view = manager.get_view(view_id, dataset_id)

        if intent:
            generated_sql = view.generate_sql(intent)
            return success_response(
                {"generated_sql": generated_sql, "view": format_view_info(view)},
                "SQL generated and applied",
            )
        elif raw_sql:
            view.add_sql(raw_sql)
            return success_response(format_view_info(view), "SQL query applied")
        else:
            return error_response(ValueError("Either intent or raw_sql must be provided"))
    except (MammothAPIError, MammothColumnError) as e:
        return error_response(e)
    except (ValueError, KeyError, TypeError) as e:
        return error_response(e)
    except Exception as e:
        logger.exception("Unexpected error in sql_query")
        return error_response(e)
