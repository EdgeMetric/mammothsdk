"""A tool call answers before the edge cuts it off, whatever it was waiting on.

CloudFront ends a response after 30 seconds of silence, and the client then tells
the user the server is down. The job waits stop themselves in time, but a single
request to Mammoth does not: some routes answer with a result rather than a job,
so there is nothing to poll. This stop covers those. Mammoth may finish the work
after the call has given up, so the answer says the outcome is unknown rather
than that the call failed.
"""

import asyncio
from typing import Any

from mcp.server.context import HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent

from .consts import CALL_HARD_STOP_SECONDS

_TOOL_CALL = "tools/call"


class CallLimit:
    """A `ServerMiddleware` that answers for a tool call that has run too long."""

    async def __call__(self, ctx: ServerRequestContext[Any, Any], call_next: Any) -> HandlerResult:
        """Run the call, or report that its outcome is unknown once time is up.

        Args:
            ctx: The request being handled.
            call_next: The rest of the middleware chain and the handler.

        Returns:
            What the call returned, or an error result if it ran out of time.
        """
        if ctx.method != _TOOL_CALL:
            return await call_next(ctx)
        try:
            return await asyncio.wait_for(call_next(ctx), CALL_HARD_STOP_SECONDS)
        except TimeoutError:
            return outcome_unknown(str((ctx.params or {}).get("name")))


def outcome_unknown(tool: str) -> CallToolResult:
    """What the caller gets back for a tool call that ran out of time.

    Args:
        tool: The tool that was called.

    Returns:
        An error result saying the work may have gone through.
    """
    text = (
        f"{tool} took too long to answer, so its outcome is unknown: Mammoth may still"
        " be working on it. Read the data it would have changed before calling it again."
    )
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=True)
