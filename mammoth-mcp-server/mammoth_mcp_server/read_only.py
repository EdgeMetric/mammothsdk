"""A connection the user limited to reading, enforced here rather than trusted.

A user who wants an assistant to look at their data but never change it says so
when they connect, and Mammoth puts that on the token as the `read` scope. A
token without the scope was never limited, which is every token Mammoth issues
today, so nothing changes for an existing connection.

What may run is decided by what each tool says it does — its own
`read_only_hint` annotation, the same one a client reads to decide whether to
ask the user first. So a tool added tomorrow is covered the day it is added,
and there is no second list to keep in step with the first. A name this server
does not know is refused rather than allowed: an unknown tool is not a way past
the limit.
"""

from typing import Any

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.context import HandlerResult, ServerRequestContext
from mcp.server.mcpserver.exceptions import ToolError

# What Mammoth puts on a token the user limited to reading.
READ_SCOPE = "read"
_TOOL_CALL = "tools/call"


def is_read_only() -> bool:
    """Whether this caller's token was limited to reading."""
    access_token = get_access_token()
    return access_token is not None and READ_SCOPE in (access_token.scopes or [])


def may_run(tool: str) -> bool:
    """Whether this caller may run `tool`.

    A caller who was never limited may run anything. A limited one may run
    only a tool that says it is read-only.
    """
    if not is_read_only():
        return True
    # Imported here: the server builds this middleware, so it cannot be
    # imported while this module is first read.
    from .server import mcp_server

    return any(
        offered.name == tool and bool(offered.annotations and offered.annotations.read_only_hint)
        for offered in await_tools(mcp_server)
    )


def await_tools(server: Any) -> list[Any]:
    """The tools the server offers, read without a running loop.

    `list_tools` is a coroutine for the protocol's sake; the registry behind it
    is plain data, so it is read directly rather than by starting a loop inside
    a request that already has one.
    """
    return list(server._tool_manager.list_tools())


class ReadOnly:
    """A `ServerMiddleware` that turns a write away on a read-only connection.

    Refused here rather than at Mammoth: Mammoth would refuse it too, but the
    model would read a failed call instead of the reason, and the write would
    have been attempted.
    """

    async def __call__(self, ctx: ServerRequestContext[Any, Any], call_next: Any) -> HandlerResult:
        if ctx.method == _TOOL_CALL:
            tool = str((ctx.params or {}).get("name"))
            if not may_run(tool):
                raise ToolError(
                    f"This connection is read-only, so {tool} cannot run."
                    " Reconnect without the read-only option to make changes."
                )
        return await call_next(ctx)
