"""Helper utilities for Mammoth MCP tools."""

from __future__ import annotations

import asyncio
import functools
import inspect
import json
import logging
import time
from typing import Any

from mammoth import (
    CompoundCondition,
    Condition,
    Operator,
)
from mammoth.exceptions import MammothAPIError, MammothColumnError
from mcp.server.fastmcp import Context
from mcp.types import CallToolResult, TextContent

from mammoth_mcp.state import ClientManager

logger = logging.getLogger("mammoth_mcp.tools")


# ── Async helper for sync SDK calls ─────────────────────────


async def run_sync(fn, *args, **kwargs):
    """Run a synchronous SDK function in a thread to avoid blocking the event loop.

    Sync SDK calls use ``time.sleep()`` for polling, which blocks the asyncio
    event loop and causes SSE keepalive failures in MCP remote mode. This
    helper offloads them to a thread pool via ``asyncio.to_thread()``.
    """
    return await asyncio.to_thread(fn, *args, **kwargs)


# ── Recovery hints by error type ─────────────────────────────

_RECOVERY_HINTS: dict[type, str] = {
    MammothColumnError: (
        "Column not found. Call get_view to see current column names — "
        "they may have changed after a transformation."
    ),
}


def _get_recovery_hint(error: Exception) -> str | None:
    """Return an actionable recovery hint for known error types."""
    # Exact type match first
    hint = _RECOVERY_HINTS.get(type(error))
    if hint:
        return hint

    # Check MammothAPIError status codes
    if isinstance(error, MammothAPIError):
        status = getattr(error, "status_code", None)
        if status == 401:
            return "Authentication failed. Check API key and secret."
        if status == 403:
            return "Permission denied. Check workspace access."
        if status == 404:
            return "Resource not found. Verify the view/dataset ID exists."
        if status in (429, 503):
            return "Service temporarily unavailable. Try again in a moment."
        if status and status >= 500:
            return "Server error. Try again or use a simpler operation."

    # Timeout errors
    if isinstance(error, TimeoutError) or "timeout" in str(error).lower():
        return "Operation timed out. Try a smaller dataset or simpler transformation."

    return None


# ── MCP-standard error/success responses ─────────────────────


def error_result(error: Exception) -> CallToolResult:
    """Create an MCP-standard error result with isError=True and recovery hint."""
    body: dict[str, Any] = {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
    }
    hint = _get_recovery_hint(error)
    if hint:
        body["recovery_hint"] = hint
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(body))],
        isError=True,
    )


def success_response(data: Any = None, message: str | None = None) -> dict[str, Any]:
    """Create a structured success response dict.

    FastMCP's convert_result will serialize this as TextContent with isError=False.
    """
    result: dict[str, Any] = {"success": True}
    if message:
        result["message"] = message
    if data is not None:
        result["data"] = data
    return result


# ── @handle_errors decorator ─────────────────────────────────


def handle_errors(fn):
    """Decorator that catches exceptions and returns MCP-standard isError responses.

    Eliminates the need for try/except boilerplate in every tool function.
    Expected exceptions (API errors, validation errors) are returned as
    structured error results. Unexpected exceptions are logged and returned.
    """

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except (MammothAPIError, MammothColumnError) as e:
            return error_result(e)
        except (ValueError, KeyError, TypeError) as e:
            return error_result(e)
        except Exception as e:
            logger.exception("Unexpected error in %s", fn.__name__)
            return error_result(e)

    return wrapper


# ── Logging decorator ────────────────────────────────────────


def log_tool_call(fn):
    """Decorator that logs every MCP tool invocation with timing and user identity."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        # Build a clean argument dict (skip 'ctx')
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        log_args = {k: v for k, v in bound.arguments.items() if k != "ctx"}

        # Try to extract user identity for audit logging (remote mode)
        user_id = _extract_user_id(bound.arguments.get("ctx"))

        extra = f" user={user_id}" if user_id else ""
        logger.info("TOOL_CALL %s%s args=%s", fn.__name__, extra, log_args)
        start = time.monotonic()
        try:
            result = await fn(*args, **kwargs)
            elapsed = time.monotonic() - start
            # Handle both dict results (success) and CallToolResult (error)
            if isinstance(result, CallToolResult):
                success = not result.isError
            elif isinstance(result, dict):
                success = result.get("success", False)
            else:
                success = True
            logger.info(
                "TOOL_RESULT %s%s success=%s elapsed=%.2fs",
                fn.__name__, extra, success, elapsed,
            )
            return result
        except Exception:
            elapsed = time.monotonic() - start
            logger.exception("TOOL_ERROR %s%s elapsed=%.2fs", fn.__name__, extra, elapsed)
            raise

    return wrapper


def _extract_user_id(ctx: Any) -> str | None:
    """Extract client_id from MCP auth context for audit logging."""
    if ctx is None:
        return None
    try:
        from mcp.server.auth.middleware.auth_context import get_access_token

        token = get_access_token()
        if token and hasattr(token, "client_id"):
            return token.client_id
    except Exception:
        pass
    return None


# ── Async helper for get_manager ─────────────────────────────


async def get_manager(ctx: Context) -> ClientManager:
    """Resolve per-user ClientManager from request context."""
    lc = ctx.request_context.lifespan_context
    registry = lc.get("registry")
    if registry:
        # Remote mode — resolve via bearer token from auth context
        from mcp.server.auth.middleware.auth_context import get_access_token

        access_token = get_access_token()
        if not access_token:
            raise RuntimeError("Not authenticated — missing access token")
        return await registry.get_manager(access_token.token)
    # Stdio mode — single manager from env vars
    manager = lc.get("manager")
    if not manager:
        raise RuntimeError("MCP server not initialized — check environment variables")
    return manager


# ── Condition builder ────────────────────────────────────────


def build_condition(d: dict[str, Any]) -> Condition | CompoundCondition:
    """Convert a JSON-friendly dict into SDK Condition objects.

    Supports two forms:
        Simple:   {"column": "Sales", "operator": "GTE", "value": 1000}
        Compound: {"logic": "AND", "conditions": [<cond>, <cond>]}

    Operator names match the Operator enum (GTE, IN_LIST, IS_EMPTY, etc.).
    """
    if "logic" in d:
        inner = [build_condition(c) for c in d["conditions"]]
        if d["logic"].upper() == "AND":
            result = inner[0]
            for c in inner[1:]:
                result = result & c
            return result
        else:
            result = inner[0]
            for c in inner[1:]:
                result = result | c
            return result

    op_str = d["operator"].upper()
    op = Operator(op_str)
    return Condition(
        column=d["column"],
        operator=op,
        value=d.get("value"),
    )


def parse_math_expression(expression: str) -> str:
    """Pass-through — the SDK's math() method handles string parsing internally."""
    return expression


# ── View info formatter ──────────────────────────────────────


def format_view_info(view: Any) -> dict[str, Any]:
    """Format a View object into a JSON-serializable summary."""
    info: dict[str, Any] = {
        "id": view.id,
        "name": view.name,
        "dataset_id": view.dataset_id,
        "columns": [
            {"name": name, "internal_name": view.columns[name], "type": view.column_types.get(name, "TEXT")}
            for name in view.display_names
        ],
        "column_count": len(view.display_names),
    }
    # Include row count if available
    row_count = getattr(view, "row_count", None)
    if row_count is not None:
        info["row_count"] = row_count
    return info


# ── Enum resolver ────────────────────────────────────────────


def resolve_enum(enum_cls: type, value: str) -> Any:
    """Resolve a string to an enum member, case-insensitive."""
    value_upper = value.upper()
    for member in enum_cls:
        if member.value == value_upper or member.name == value_upper:
            return member
    valid = [m.value for m in enum_cls]
    raise ValueError(f"Invalid value '{value}' for {enum_cls.__name__}. Valid: {valid}")


# ── Deprecated — kept for backward compatibility ─────────────


def error_response(error: Exception) -> dict[str, Any]:
    """Create a structured error response dict.

    DEPRECATED: Use error_result() for MCP-standard isError responses.
    Kept for tools that may still return dict errors (e.g. parse_mammoth_url
    which is sync).
    """
    body: dict[str, Any] = {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
    }
    hint = _get_recovery_hint(error)
    if hint:
        body["recovery_hint"] = hint
    return body
