"""What the server records about a call, so the launch can be measured.

One JSON line per event, on its own logger, so a deployment ships these to its
own analytics without parsing the server's ordinary logs. Each event is also
sent to Mammoth's user events with the caller's own token, so Mammoth stores it
with the user, as it stores the web app's events.

What is recorded is the shape of the traffic: which tool ran, from which
client, how long it took and whether it failed. What is never recorded is what
the call was about. A tool's arguments carry the user's own data — column
names, filter values, file names — so the name of the tool is kept and the
arguments are dropped on the floor. No token, no id and no row ever reaches an
event. One argument is kept: the connector a user connects, which is a name
from Mammoth's own list of connectors, not the user's data.
"""

import asyncio
import base64
import hashlib
import json
import logging
import sys
import time
from typing import Any, TextIO
from urllib.parse import urlsplit

from mammoth.exceptions import MammothError
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.context import HandlerResult, ServerRequestContext

from . import sdk
from .config import SERVER_URL
from .consts import TokenClaims

EVENT_LOGGER = "mammoth_mcp_server.events"
_log = logging.getLogger(EVENT_LOGGER)
# Not the events logger: its every line is an event.
_problems = logging.getLogger(__name__)


class Events:
    """The events this server emits, and the outcomes a call can have."""

    INITIALIZE = "mcp_initialize"
    TOOL_CALLED = "mcp_tool_called"
    SOURCE_LINKED = "mcp_source_linked"
    SOURCE_CONNECTED = "mcp_source_connected"
    NEW_DATASETS = "mcp_new_datasets"
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
    CONNECTOR = "connector"
    STATUS = "status"
    DATASETS = "datasets"


# The JSON-RPC methods worth an event of their own.
_INITIALIZE = "initialize"
_TOOL_CALL = "tools/call"


class _EventsHandler(logging.StreamHandler[TextIO]):
    """The handler `write_events` adds, so a second call can find it."""


def write_events() -> None:
    """Send the events to stdout, one JSON line each.

    Nothing else configures this logger: uvicorn configures only its own, so
    without this the level stays WARNING and every event is dropped. Calling it
    again changes nothing.
    """
    if any(isinstance(one, _EventsHandler) for one in _log.handlers):
        return
    _log.addHandler(_EventsHandler(sys.stdout))
    _log.setLevel(logging.INFO)
    # The line is already the whole event; the root logger would add a second copy.
    _log.propagate = False


# What Mammoth's user events call the part of the product an event came from.
_ORIGIN = "mcp"
_USER_EVENTS_PATH = "/workspaces/{workspace_id}/mm-ue"
# Kept until done: the event loop holds a task only weakly.
_sending: set[asyncio.Task[None]] = set()


def record(event: str, **fields: Any) -> None:
    """Emit one event, as a single JSON line, and send it to Mammoth."""
    _log.info(json.dumps({TelemetryFields.EVENT: event, **fields}))
    caller = get_access_token()
    if caller is None:
        return
    # In the background: the caller waits on the tool, not on its measurement.
    task = asyncio.get_running_loop().create_task(_send(caller, event, fields))
    _sending.add(task)
    task.add_done_callback(_sending.discard)


async def sending() -> None:
    """Wait until every event on its way to Mammoth got there or failed."""
    await asyncio.gather(*_sending)


async def _send(caller: AccessToken, event: str, fields: dict[str, Any]) -> None:
    """Store one event in Mammoth as the caller's own. A failure is logged, never raised."""
    path = _USER_EVENTS_PATH.format(workspace_id=(caller.claims or {})[TokenClaims.WORKSPACE_ID])
    encoded = base64.b64encode(json.dumps(_user_event(caller, event, fields)).encode()).decode()
    try:
        async with sdk.client_with(caller.token) as client:
            # The SDK has no method for this route; one would need a mammoth-io release.
            await client._request("POST", path, json={"encoded_data": encoded})
    except MammothError:
        _problems.warning("Mammoth did not store the %s event", event, exc_info=True)


def _user_event(caller: AccessToken, event: str, fields: dict[str, Any]) -> dict[str, Any]:
    """The event as Mammoth's user events take it. Mammoth adds the user from the token."""
    return {
        "event_name": event,
        "event_origin": _ORIGIN,
        "event_context": {},
        "additional_info": fields,
        # The fields a browser fills in. Here the client stands in for the browser.
        "browser_name": fields.get(TelemetryFields.CLIENT) or "",
        "browser_version": fields.get(TelemetryFields.CLIENT_VERSION) or "",
        "browser_size": {},
        "device_info": sdk.USER_AGENT,
        "domain": urlsplit(SERVER_URL).netloc,
        "os_name": "",
        # Empty: Mammoth fills in the caller's own email.
        "email_id": "",
        "user_name": "",
        "timestamp": time.time(),
        # Without it Mammoth keeps the token's first characters. A hash of the
        # token groups one connection's calls and keeps no part of the secret.
        "session_identifier": hashlib.sha256(caller.token.encode()).hexdigest()[:32],
    }


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
