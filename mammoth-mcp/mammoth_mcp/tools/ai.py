"""AI-powered transformation tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from mammoth_mcp.helpers import (
    format_view_info,
    get_manager,
    handle_errors,
    log_tool_call,
    success_response,
)
from mammoth_mcp.server import mcp


@mcp.tool()
@log_tool_call
@handle_errors
async def ai_transform(
    ctx: Context,
    view_id: int,
    prompt: str,
    context_columns: list[str],
    new_column: str = "AI Result",
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Use an OpenAI LLM to generate a NEW column from a prompt and context columns. Adds a reversible pipeline task (undo with delete_task).

    Best for: classification, sentiment analysis, entity extraction, enrichment, content generation, data standardization — tasks requiring language understanding.

    PREREQUISITE: Requires an OpenAI API key configured in workspace settings (Settings → Integrations → OpenAI). Calls fail without it.

    LIMITS: 50,000 rows max. For larger datasets, use filter_rows to batch first.
    TIMING: ~30-60 sec/10K rows (simple classification), ~2-5 min/10K rows (complex generation).
    COST: Consumes OpenAI API tokens — prefer structured tools (set_values, replace_values, bulk_replace) when deterministic logic suffices.

    Prompt tips: Be specific, constrain output values ("Output exactly one of: Positive, Negative, Neutral"), include examples, specify format. Null inputs → null outputs.

    Context columns: Include only what the AI needs (max 20). More columns = slower + more expensive.

    Call get_help("ai_transform") for detailed prompt engineering guide and examples.

    Args:
        view_id: The dataview ID.
        prompt: Natural language instruction for the AI (e.g. "Classify the sentiment of the review as Positive, Negative, or Neutral").
        context_columns: List of column display names to provide as context to the AI (max 20 — include only relevant columns).
        new_column: Name for the AI output column (default "AI Result").
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
    view = manager.get_view(view_id, dataset_id)
    view.gen_ai(
        prompt=prompt,
        context_columns=context_columns,
        new_column=new_column,
    )
    return success_response(format_view_info(view), "AI transform applied")


@mcp.tool()
@log_tool_call
@handle_errors
async def sql_query(
    ctx: Context,
    view_id: int,
    intent: str | None = None,
    raw_sql: str | None = None,
    dataset_id: int | None = None,
) -> dict[str, Any]:
    """Transform data using DuckDB SQL — either natural language intent or direct SQL. Adds a reversible pipeline task (undo with delete_task).

    INTENT mode: Describe what you want in plain English → Mammoth auto-generates DuckDB SQL (~20 sec generation time). Best for exploratory analysis.
    RAW SQL mode: Write DuckDB SQL directly. Reference columns by display name, enclose spaces in double quotes. Best for precise control.

    Must provide exactly one of `intent` or `raw_sql` (not both).

    When to use: Complex multi-step queries, subqueries, CTEs, CASE WHEN with many branches, GROUP BY + HAVING, window functions, set operations — anything that would require many individual pipeline steps.

    DuckDB supports: string concat (||), ILIKE, regex, date arithmetic, CTEs, window functions, COALESCE, CAST. No stored procedures or UDFs.

    Call get_help("sql_query") for full DuckDB dialect reference, examples, and decision guide.

    Args:
        view_id: The dataview ID.
        intent: Natural language description of the query (e.g. "show top 10 customers by total revenue with order count").
        raw_sql: Raw DuckDB SQL query string (e.g. "SELECT \"Name\", SUM(\"Sales\") as total FROM dataview GROUP BY \"Name\"").
        dataset_id: The dataset ID (auto-detected if not provided).
    """
    manager = await get_manager(ctx)
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
        raise ValueError("Either intent or raw_sql must be provided")
