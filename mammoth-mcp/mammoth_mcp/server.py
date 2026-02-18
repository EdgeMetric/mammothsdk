"""Mammoth Analytics MCP Server — entry point and lifespan."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from mammoth_mcp.config import MammothConfig
from mammoth_mcp.state import ClientManager


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Create the ClientManager from env vars and expose it to all tools."""
    config = MammothConfig.from_env()
    manager = ClientManager(config)
    yield {"manager": manager}


mcp = FastMCP("Mammoth Analytics", lifespan=lifespan)


# ── Resources ────────────────────────────────────────────────

@mcp.resource("mammoth://config")
def get_config() -> str:
    """Current Mammoth connection configuration (no secrets)."""
    import os

    config = {
        "workspace_id": os.environ.get("MAMMOTH_WORKSPACE_ID", ""),
        "project_id": os.environ.get("MAMMOTH_PROJECT_ID", ""),
        "base_url": os.environ.get("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
        "job_timeout": os.environ.get("MAMMOTH_JOB_TIMEOUT", "120"),
        "api_key_set": bool(os.environ.get("MAMMOTH_API_KEY")),
        "api_secret_set": bool(os.environ.get("MAMMOTH_API_SECRET")),
    }
    return json.dumps(config, indent=2)


@mcp.resource("mammoth://enums")
def get_enums() -> str:
    """All valid enum values for Mammoth SDK operations."""
    from mammoth import (
        AggregateFunction,
        ColumnType,
        DateComponent,
        DateDiffUnit,
        FillDirection,
        FilterType,
        JoinType,
        JsonType,
        MathOperator,
        Operator,
        SortDirection,
        SubstringDirection,
        TextCase,
        WindowFunction,
        WindowRange,
    )

    enums = {
        "Operator": [e.value for e in Operator],
        "ColumnType": [e.value for e in ColumnType],
        "JoinType": [e.value for e in JoinType],
        "TextCase": [e.value for e in TextCase],
        "DateComponent": [e.value for e in DateComponent],
        "DateDiffUnit": [e.value for e in DateDiffUnit],
        "WindowFunction": [e.value for e in WindowFunction],
        "WindowRange": [e.value for e in WindowRange],
        "FillDirection": [e.value for e in FillDirection],
        "AggregateFunction": [e.value for e in AggregateFunction],
        "FilterType": [e.value for e in FilterType],
        "SortDirection": [e.value for e in SortDirection],
        "MathOperator": [e.value for e in MathOperator],
        "SubstringDirection": [e.value for e in SubstringDirection],
        "JsonType": [e.value for e in JsonType],
    }
    return json.dumps(enums, indent=2)


# ── Register tools from submodules ───────────────────────────

from mammoth_mcp.tools import (  # noqa: E402
    advanced,
    aggregate,
    ai,
    columns,
    connection,
    data,
    discovery,
    export,
    pipeline,
    values,
    views,
)


def main() -> None:
    """Run the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
