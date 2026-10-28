"""Build the SDK client a tool calls Mammoth through, as the signed-in caller.

A tool never re-implements a route, and it never spells one out either: it
calls the SDK's method for that route, and the SDK builds the path, sends the
request and waits for whatever job comes back. The SDK is the same one the CLI
and every customer script use, so a tool can only do what a customer could.

The client is built fresh for each call. It has to be: it carries the caller's
own credentials, and two MCP requests in flight belong to two different people.
The connection pool is not fresh per call. Every client sends through one
process-wide `httpx.AsyncClient`, so a tool call does not pay a new TLS
handshake. That is safe because the SDK puts the caller's credentials on each
request and never on the shared client. `build_client` still hands the client
out of an `async with`: the block closes what the client owns (its download
session), and leaves the shared pool open.
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from http.cookiejar import DefaultCookiePolicy
from typing import TypeVar

import httpx
from mammoth.client import MammothClient
from mammoth.exceptions import MammothError
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver.exceptions import ToolError

from . import __version__
from .config import API_ROOT, API_URL
from .consts import (
    JOB_POLL_SECONDS,
    JOB_TIMEOUT_SECONDS,
    REFUSAL_HINTS,
    ROUTE_TIMEOUT_SECONDS,
    UPLOAD_FIELD,
    TokenClaims,
)
from .deadline import seconds_left, start_the_clock

type JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None

# One file in a multipart request: its name, its bytes and its media type.
type FileUpload = tuple[str, bytes, str]
type FileUploads = list[FileUpload]

# What Mammoth sees as the caller of every request, so MCP traffic can be told
# apart from the SDK's own.
USER_AGENT = f"mammoth-mcp-server/{__version__}"
NOT_FOUND = 404
API_ERROR_PREFIX = "Mammoth API error"
UNREADABLE_API_ERROR = "the API returned an error with no message"

_api_url = API_URL
_api_root = API_ROOT

# The one connection pool every client sends through, and the loop it opened on.
# A pool is tied to its loop, so a different loop (a test's, a restarted worker)
# gets a pool of its own rather than the stale one.
_http_client: httpx.AsyncClient | None = None
_http_client_loop: asyncio.AbstractEventLoop | None = None


def shared_http_client() -> httpx.AsyncClient:
    """The process-wide connection pool, opened on first use.

    It carries no credentials: each client the SDK builds on it sends its own
    caller's token with every request. It keeps no cookies either: a cookie one
    caller's response set would otherwise go out with the next caller's request.
    A pool left on a loop that is gone is not closed: its loop cannot run the close.
    """
    global _http_client, _http_client_loop
    loop = asyncio.get_running_loop()
    if _http_client is None or _http_client.is_closed or _http_client_loop is not loop:
        _http_client = httpx.AsyncClient(timeout=ROUTE_TIMEOUT_SECONDS, follow_redirects=False)
        _http_client.cookies.jar.set_policy(DefaultCookiePolicy(allowed_domains=[]))
        _http_client_loop = loop
    return _http_client


async def close_http_client() -> None:
    """Close the connection pool, when the server stops. Safe to call when none is open."""
    global _http_client, _http_client_loop
    pool, _http_client, _http_client_loop = _http_client, None, None
    if pool is not None:
        await pool.aclose()


def set_api_url(url: str, api_root: str | None = None) -> None:
    """Build clients against the Mammoth API at `url` — a test's own server, say.

    Args:
        url: The API's base URL.
        api_root: The path the API is served under there, or None when the
            server mounts its routes at their own paths.
    """
    global _api_url, _api_root
    _api_url = url
    _api_root = api_root


def api_url() -> str:
    """The Mammoth API this process calls."""
    return _api_url


def api_root() -> str | None:
    """The path that API is served under, or None when its routes are at their own paths."""
    return _api_root


@asynccontextmanager
async def build_client(
    workspace_id: int | None, project_id: int | None = None
) -> AsyncIterator[MammothClient]:
    """An SDK client that acts as the caller of the MCP request being served.

    Use it once, for as much of a tool call as one client can serve, and let
    the block end: leaving it closes the connections the client opened.

    Args:
        workspace_id: The workspace the tool call acts in. None only for the
            call made before one is known, which lists the caller's workspaces.
        project_id: The project it acts in. The SDK's pipeline methods read
            this off the client rather than taking it, and refuse a client
            that has none, so pass it for anything that touches a pipeline.

    Yields:
        A client pointed at this deployment's Mammoth API, carrying the
        caller's own token.

    Raises:
        RuntimeError: If called outside an authenticated MCP request.
        ToolError: If the call names a workspace or a project the caller's
            token is not for.
    """
    access_token = get_access_token()
    if access_token is None:
        raise RuntimeError("no authenticated MCP caller for this tool call")
    own_workspace = int((access_token.claims or {})[TokenClaims.WORKSPACE_ID])
    check_project(project_id)
    if workspace_id is not None and workspace_id != own_workspace:
        # A token belongs to one workspace, and the API refuses it for any
        # other. Said here, the model learns which workspace to name instead.
        raise ToolError(
            f"This sign-in is for workspace {own_workspace}, not {workspace_id}."
            " Use that workspace, or connect again and choose the other."
        )
    start_the_clock()
    client = client_with(access_token.token, job_timeout=max(1.0, seconds_left()))
    # Named here, the client does not spend a request asking the API which
    # workspace its bearer is for.
    client.set_workspace_id(own_workspace)
    if project_id is not None:
        client.set_project_id(project_id)
    async with client:
        yield client


def own_workspace() -> int:
    """The one workspace the caller's token belongs to.

    Mammoth issues a token for a single workspace and refuses it on every
    other, so this is not a preference to be overridden: it is the whole
    account this connection can see.

    Raises:
        RuntimeError: If no authenticated caller is in context, which is a bug
            in the server rather than anything the caller did.
    """
    access_token = get_access_token()
    if access_token is None:
        raise RuntimeError("no authenticated MCP caller for this tool call")
    return int((access_token.claims or {})[TokenClaims.WORKSPACE_ID])


def own_projects() -> list[int] | None:
    """The projects the caller may act in, sorted, or None for every project.

    The user settles this when they connect: picking projects fences the token
    to them, and Mammoth refuses the token on any other. Read it rather than
    ask the user again.
    """
    access_token = get_access_token()
    if access_token is None:
        raise RuntimeError("no authenticated MCP caller for this tool call")
    pinned = (access_token.claims or {}).get(TokenClaims.PROJECT_IDS)
    return [int(project) for project in pinned] if pinned else None


def only_project() -> int | None:
    """The project the caller may act in, when they may act in exactly one.

    A tool that must land somewhere uses it without asking. With several, or
    with every project, the model has to name one.
    """
    pinned = own_projects()
    return pinned[0] if pinned is not None and len(pinned) == 1 else None


def check_project(project_id: int | None) -> None:
    """Refuse a project the caller's token is fenced out of.

    Mammoth refuses it too, with an authorization error that reaches the user
    as a failed call and nothing more. Said here, the model learns which
    projects it may use.

    Raises:
        ToolError: If the token is pinned to other projects.
    """
    pinned = own_projects()
    if pinned is not None and project_id is not None and project_id not in pinned:
        raise ToolError(
            f"This connection is limited to {named_projects(pinned)}, not {project_id}."
            " Use one of those, or connect again and choose the other project too."
        )


def named_projects(pinned: list[int]) -> str:
    """The pinned projects as a person reads them: "project 3" or "projects 3, 7"."""
    listed = ", ".join(str(project) for project in pinned)
    return f"project {listed}" if len(pinned) == 1 else f"projects {listed}"


def client_with(bearer: str, job_timeout: float = JOB_TIMEOUT_SECONDS) -> MammothClient:
    """One client, pointed at the Mammoth API this process was told to call.

    Args:
        bearer: The caller's token.
        job_timeout: How long the SDK's own waits on a job may take.
    """
    client = MammothClient(
        api_token=bearer,
        base_url=_api_url,
        api_root=_api_root,
        # Plain HTTP is taken only for a loopback address: the SDK refuses it
        # for any other host.
        allow_insecure_loopback_http=True,
        timeout=ROUTE_TIMEOUT_SECONDS,
        job_timeout=job_timeout,
        # A person is waiting on this answer. The SDK's own default suits a
        # script that started a long build and would add whole seconds here.
        job_poll_seconds=JOB_POLL_SECONDS,
        user_agent=USER_AGENT,
        http_client=shared_http_client(),
    )
    return client


T = TypeVar("T")


async def read_sdk_errors(work: Awaitable[T], not_found: str | None = None) -> T:
    """Await an SDK call, and turn a refusal into words the model can use.

    An exception raised inside a tool reaches the client as "Error executing
    tool <name>", which tells a model nothing and tells a user less. Mammoth's
    own message is the thing worth relaying, so it becomes the tool's error.

    Args:
        work: The SDK call to run.
        not_found: What to say when the API answers 404, which names no id: the
            ids the call used and the `list_*` tool that shows the right ones.

    Raises:
        ToolError: Carrying whatever the API said, for the model to relay.
    """
    try:
        return await work
    except MammothError as refused:
        if not_found is not None and getattr(refused, "status_code", None) == NOT_FOUND:
            raise ToolError(f"{API_ERROR_PREFIX}: {not_found}") from refused
        body = getattr(refused, "response_body", None)
        code = body.get("error_code") if isinstance(body, dict) else None
        hint = f" {REFUSAL_HINTS[code]}" if code in REFUSAL_HINTS else ""
        raise ToolError(
            f"{API_ERROR_PREFIX}: {str(refused).strip() or UNREADABLE_API_ERROR}{hint}"
        ) from refused


async def request_api(
    client: MammothClient,
    method: str,
    path: str,
    *,
    query: dict[str, str | int] | None = None,
    body: dict[str, JsonValue] | None = None,
    upload: FileUploads | None = None,
) -> dict[str, JsonValue]:
    """Call a route the SDK has no method for, through the SDK's own client.

    The client carries the caller's credentials, its timeouts and its error
    handling, so such a call differs from an SDK method only in where its path
    is written down.

    Args:
        client: The caller's SDK client.
        method: HTTP method, e.g. "GET" or "POST".
        path: The route's path, e.g. "/workspaces".
        query: Query parameters.
        body: JSON request body.
        upload: Files to send instead of a JSON body, as one multipart body.

    Returns:
        The route's payload, which is a JSON object.

    Raises:
        ToolError: If the route refuses the call, in Mammoth's own words.
    """
    # Every file goes under the same field, which is what the API reads.
    files = [(UPLOAD_FIELD, one) for one in upload] if upload else None
    payload: dict[str, JsonValue] = await read_sdk_errors(
        client.request_json(method, path, params=query, json=body, files=files)
    )
    return payload
