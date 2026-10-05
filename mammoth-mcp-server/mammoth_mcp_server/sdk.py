"""Build the SDK client a tool calls Mammoth through, as the signed-in caller.

A tool never re-implements a route, and it never spells one out either: it
calls the SDK's method for that route, and the SDK builds the path, sends the
request and waits for whatever job comes back. The SDK is the same one the CLI
and every customer script use, so a tool can only do what a customer could.

The client is built fresh for each call. It has to be: it carries the caller's
own credentials, and two MCP requests in flight belong to two different people.
Fresh per call means closed per call too, so `build_client` hands the client out
of an `async with` rather than returning one: a client holds two HTTP connection
pools, and a server that runs for weeks cannot leave them to the collector.
"""

from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from typing import TypeVar

from mammoth.client import MammothClient
from mammoth.exceptions import MammothError
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.mcpserver.exceptions import ToolError

from .config import API_ROOT, API_URL
from .consts import (
    JOB_POLL_SECONDS,
    JOB_TIMEOUT_SECONDS,
    ROUTE_TIMEOUT_SECONDS,
    UPLOAD_FIELD,
    TokenClaims,
)

type JsonValue = (dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None)

# One file in a multipart request: its name, its bytes and its media type.
type FileUpload = tuple[str, bytes, str]
type FileUploads = list[FileUpload]

API_ERROR_PREFIX = "Mammoth API error"
UNREADABLE_API_ERROR = "the API returned an error with no message"

_api_url = API_URL
_api_root = API_ROOT


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
        caller's own API token.

    Raises:
        RuntimeError: If called outside an authenticated MCP request.
        ToolError: If the call names a workspace the caller's token is not for.
    """
    access_token = get_access_token()
    if access_token is None:
        raise RuntimeError("no authenticated MCP caller for this tool call")
    claims = access_token.claims or {}
    own_workspace = int(str(claims[TokenClaims.WORKSPACE_ID]))
    if workspace_id is not None and workspace_id != own_workspace:
        # An API token belongs to one workspace, and the API refuses it for any
        # other. Said here, the model learns which workspace to name instead.
        raise ToolError(
            f"This sign-in is for workspace {own_workspace}, not {workspace_id}."
            " Use that workspace, or sign in again with a token for the other."
        )
    client = MammothClient(
        api_token=str(claims[TokenClaims.API_TOKEN]),
        base_url=_api_url,
        api_root=_api_root,
        # Plain HTTP is taken only for a loopback address: the SDK refuses it
        # for any other host.
        allow_insecure_loopback_http=True,
        timeout=ROUTE_TIMEOUT_SECONDS,
        job_timeout=JOB_TIMEOUT_SECONDS,
        # A person is waiting on this answer. The SDK's own default suits a
        # script that started a long build and would add whole seconds here.
        job_poll_seconds=JOB_POLL_SECONDS,
    )
    # The sign-in already asked the API which workspace the token is for. Left
    # unset, the client would ask again, with a request that blocks the server.
    client._workspace_id = own_workspace
    if project_id is not None:
        client.set_project_id(project_id)
    async with client:
        yield client


T = TypeVar("T")


async def read_sdk_errors(work: Awaitable[T]) -> T:
    """Await an SDK call, and turn a refusal into words the model can use.

    An exception raised inside a tool reaches the client as "Error executing
    tool <name>", which tells a model nothing and tells a user less. Mammoth's
    own message is the thing worth relaying, so it becomes the tool's error.

    Args:
        work: The SDK call to run.

    Raises:
        ToolError: Carrying whatever the API said, for the model to relay.
    """
    try:
        return await work
    except MammothError as refused:
        raise ToolError(
            f"{API_ERROR_PREFIX}: {str(refused).strip() or UNREADABLE_API_ERROR}"
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
        client._request_json(method, path, params=query, json=body, files=files)
    )
    return payload
