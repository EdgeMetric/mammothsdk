"""What the server records about a call, so the launch can be measured.

One JSON line per event, on its own logger, so a deployment ships these to its
own analytics without parsing the server's ordinary logs.

What is recorded is the shape of the traffic: which tool ran, from which
client, how long it took and whether it failed. What is never recorded is what
the call was about. A tool's arguments carry the user's own data — column
names, filter values, file names — so the name of the tool is kept and the
arguments are dropped on the floor. No token, no id and no row ever reaches an
event.
"""

import json
import logging
import time
from typing import Any

from mcp.server.context import HandlerResult, ServerRequestContext

EVENT_LOGGER = "mammoth_mcp_server.events"
_log = logging.getLogger(EVENT_LOGGER)


class Events:
    """The events this server emits, and the outcomes a call can have."""

    INITIALIZE = "mcp_initialize"
    TOOL_CALLED = "mcp_tool_called"
    OK = "ok"
    FAILED = "failed"


class TelemetryFields:
    """The keys an event carries. Analytics reads these names."""

    EVENT = "event"
    TOOL = "tool"
    CLIENT = "client"
    CLIENT_VERSION = "client_version"
    DURATION_MS = "duration_ms"
    OUTCOME = "outcome"
    ERROR = "error"


# The JSON-RPC methods worth an event of their own.
_INITIALIZE = "initialize"
_TOOL_CALL = "tools/call"


def record(event: str, **fields: Any) -> None:
    """Emit one event, as a single JSON line."""
    _log.info(json.dumps({TelemetryFields.EVENT: event, **fields}))


class Telemetry:
    """A `ServerMiddleware` that records each call without changing it.

    It times the handler, records the outcome and re-raises whatever was
    raised: an error the server would have reported must still be reported,
    and measuring it must never be the reason it is swallowed.
    """

    async def __call__(self, ctx: ServerRequestContext[Any, Any], call_next: Any) -> HandlerResult:
        if ctx.method == _INITIALIZE:
            return await self._handshake(ctx, call_next)
        if ctx.method == _TOOL_CALL:
            return await self._tool_call(ctx, call_next)
        return await call_next(ctx)

    async def _handshake(
        self, ctx: ServerRequestContext[Any, Any], call_next: Any
    ) -> HandlerResult:
        """Who connected, which is the only place a client names itself."""
        client = (ctx.params or {}).get("clientInfo") or {}
        record(
            Events.INITIALIZE,
            **{
                TelemetryFields.CLIENT: client.get("name"),
                TelemetryFields.CLIENT_VERSION: client.get("version"),
            },
        )
        return await call_next(ctx)

    async def _tool_call(
        self, ctx: ServerRequestContext[Any, Any], call_next: Any
    ) -> HandlerResult:
        """Which tool ran, how long it took, and whether it worked."""
        # The name only. `arguments` is the user's own data and is not read.
        tool = (ctx.params or {}).get("name")
        started = time.monotonic()
        outcome, error = Events.OK, None
        try:
            return await call_next(ctx)
        except BaseException as failed:
            outcome, error = Events.FAILED, type(failed).__name__
            raise
        finally:
            record(
                Events.TOOL_CALLED,
                **{
                    TelemetryFields.TOOL: tool,
                    TelemetryFields.CLIENT: _who(ctx),
                    TelemetryFields.DURATION_MS: round((time.monotonic() - started) * 1000),
                    TelemetryFields.OUTCOME: outcome,
                    TelemetryFields.ERROR: error,
                },
            )


def _who(ctx: ServerRequestContext[Any, Any]) -> str | None:
    """The client that opened this session, when the session remembers one.

    Stateless HTTP gives each request its own session, so a tool call often
    carries no handshake to read. The `mcp_initialize` event is what ties a
    client to its traffic there.
    """
    params = getattr(getattr(ctx, "session", None), "client_params", None)
    info = getattr(params, "clientInfo", None)
    return getattr(info, "name", None)
