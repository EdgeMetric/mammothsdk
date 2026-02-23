"""Progressive disclosure — tool groups that can be enabled on demand.

Core tools (connection, discovery, views, data, pipeline, help) are always
loaded.  Additional tools are organized into 4 groups that Claude can enable
via the ``list_tool_groups`` / ``enable_tool_group`` meta-tools.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


@dataclass
class ToolGroup:
    """A group of tool modules that can be enabled on demand."""

    name: str
    description: str
    modules: list[str]
    tool_names: list[str] = field(default_factory=list)
    enabled: bool = False


TOOL_GROUPS: dict[str, ToolGroup] = {
    "transformations": ToolGroup(
        name="transformations",
        description=(
            "Data transformation tools — create/delete views, filter rows, set values, "
            "math, text transforms, date operations, joins, pivot, window, crosstab, "
            "AI transforms, SQL queries, draft mode, and undo tasks. "
            "Enable when the user wants to modify, clean, reshape, or enrich data."
        ),
        modules=[
            "views_management",
            "columns",
            "values",
            "aggregate",
            "advanced",
            "ai",
            "draft_mode",
        ],
    ),
    "import": ToolGroup(
        name="import",
        description=(
            "Data import tools — webhooks (push data via HTTP), cloud connectors "
            "(Salesforce, Snowflake, etc.), file management (list, delete, extract sheets, "
            "passwords), and batch imports. "
            "Enable when the user wants to ingest data from external sources."
        ),
        modules=[
            "webhooks",
            "connectors",
            "files_extended",
            "batches",
        ],
    ),
    "exports": ToolGroup(
        name="exports",
        description=(
            "Database and file export tools — export to PostgreSQL, MySQL, BigQuery, "
            "Redshift, Elasticsearch, FTP/SFTP servers. List and delete configured exports, "
            "publish views to internal database for dashboards. "
            "Enable when the user wants to send data to external databases or servers."
        ),
        modules=[
            "export",
        ],
    ),
    "admin": ToolGroup(
        name="admin",
        description=(
            "Workspace administration tools — folders, projects, datasets, user management, "
            "dashboards, automations, schedules, API keys, client apps, AI profiling, "
            "activity logs, and reports. "
            "Enable when the user wants to manage workspace settings, users, or dashboards."
        ),
        modules=[
            "organization",
            "dashboards",
            "automations",
            "admin",
            "client_apps",
            "ai_extended",
        ],
    ),
}


def _load_group(mcp: FastMCP, group: ToolGroup) -> list[str]:
    """Import a group's modules and return the names of newly registered tools."""
    before = set(mcp._tool_manager._tools.keys())
    for module_name in group.modules:
        importlib.import_module(f"mammoth_mcp.tools.{module_name}")
    after = set(mcp._tool_manager._tools.keys())
    new_tools = sorted(after - before)
    group.tool_names = new_tools
    group.enabled = True
    return new_tools


def register_meta_tools(mcp: FastMCP) -> None:
    """Register the two progressive-disclosure meta-tools on the server."""

    @mcp.tool()
    async def list_tool_groups(ctx: Context) -> dict[str, Any]:
        """List available tool groups that can be enabled on demand.

        The server starts with ~15 core tools (connection, discovery, views, data,
        pipeline, help). Additional capabilities are organized into groups that you
        can enable when needed. Call enable_tool_group to activate a group.
        """
        groups = []
        for group in TOOL_GROUPS.values():
            info: dict[str, Any] = {
                "name": group.name,
                "description": group.description,
                "enabled": group.enabled,
            }
            if group.enabled:
                info["tool_count"] = len(group.tool_names)
                info["tools"] = group.tool_names
            groups.append(info)
        return {"success": True, "data": groups}

    @mcp.tool()
    async def enable_tool_group(ctx: Context, group_name: str) -> dict[str, Any]:
        """Enable a tool group, making its tools available for use.

        Args:
            group_name: Name of the group to enable (transformations, import, exports, admin).
        """
        if group_name not in TOOL_GROUPS:
            return {
                "success": False,
                "error": f"Unknown group '{group_name}'. Available: {list(TOOL_GROUPS.keys())}",
            }

        group = TOOL_GROUPS[group_name]
        if group.enabled:
            return {
                "success": True,
                "message": f"Group '{group_name}' is already enabled",
                "data": {"tools": group.tool_names},
            }

        new_tools = _load_group(mcp, group)
        logger.info("Enabled tool group '%s' — %d tools added", group_name, len(new_tools))

        # Notify the client that the tool list has changed
        session = ctx.session
        if session and hasattr(session, "send_tool_list_changed"):
            try:
                await session.send_tool_list_changed()
            except Exception:
                logger.debug("Could not send tool_list_changed notification", exc_info=True)

        return {
            "success": True,
            "message": f"Enabled '{group_name}' — {len(new_tools)} tools added",
            "data": {"tools": new_tools},
        }
