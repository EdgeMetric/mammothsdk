"""Shared pieces for the MCP server's unit tests: a caller, a loop and a fake API.

No test here reaches Mammoth. The SDK client is real and so is the tool; only
the HTTP transport under the client is replaced, so a test sees the requests a
tool sends and decides what the API answers.
"""

import asyncio
import contextvars
import json
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import httpx
from mammoth.client import MammothClient
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken

from mammoth_mcp_server.config import MCP_RESOURCE_URL
from mammoth_mcp_server.consts import TokenClaims
from mammoth_mcp_server.sdk import set_api_url
from mammoth_mcp_server.server import mcp_server, register_tools

API_URL = "http://127.0.0.1:1"
WORKSPACE = 7
TOKEN = "mm_test_token"

_RUNNER = asyncio.Runner()


def run(awaitable: Any) -> Any:
    """Run one awaitable on the tests' loop, in the caller's context."""
    return _RUNNER.run(awaitable, context=contextvars.copy_context())


@contextmanager
def as_caller(token: str = TOKEN, workspace_id: int = WORKSPACE) -> Generator[None]:
    """Run the block as a caller whose token Mammoth issued for this server."""
    access = AccessToken(
        token=token,
        client_id="a-client",
        scopes=[],
        resource=MCP_RESOURCE_URL,
        claims={TokenClaims.WORKSPACE_ID: workspace_id},
    )
    reset = auth_context_var.set(AuthenticatedUser(access))
    try:
        yield
    finally:
        auth_context_var.reset(reset)


class FakeApi:
    """A Mammoth API that answers what a test tells it to, and keeps what it was sent."""

    def __init__(self) -> None:
        self.answers: dict[tuple[str, str], list[tuple[int, Any]]] = {}
        self.requests: list[httpx.Request] = []

    def answer(self, method: str, path: str, payload: Any, status: int = 200) -> None:
        """Answer the next call to `path` with `payload`; the last answer repeats."""
        self.answers.setdefault((method, path), []).append((status, payload))

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        queued = self.answers.get((request.method, request.url.path))
        if not queued:
            return httpx.Response(404, json={"message": f"no fake for {request.url.path}"})
        status, payload = queued[0] if len(queued) == 1 else queued.pop(0)
        return httpx.Response(status, json=payload)

    def sent(self, method: str, path: str) -> list[httpx.Request]:
        """Every request a tool sent to one route, oldest first."""
        return [r for r in self.requests if (r.method, r.url.path) == (method, path)]

    @staticmethod
    def body(request: httpx.Request) -> Any:
        return json.loads(request.content)


@contextmanager
def a_fake_api() -> Generator[FakeApi]:
    """Send every SDK client a tool builds to a fake API, for the block."""
    api = FakeApi()

    class ClientOverAFake(MammothClient):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            headers = dict(self.session.headers)
            self.session = httpx.AsyncClient(
                transport=httpx.MockTransport(api.handle), headers=headers
            )

    set_api_url(API_URL)
    with patch("mammoth_mcp_server.sdk.MammothClient", ClientOverAFake):
        yield api


def call_tool(name: str, **arguments: object) -> Any:
    """Call one tool through the MCP server, as a client does, and return its result."""
    register_tools()
    result = run(mcp_server.call_tool(name, dict(arguments)))
    assert result.structured_content is not None
    return dict(result.structured_content)


def lends(client: Any) -> Callable[..., Any]:
    """Stand in for `build_client`, which hands its client out of an `async with`."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lend(*_: object, **__: object) -> Any:
        yield client

    return lend


class FakeRedis:
    """Just enough of Redis: one value per key, and how long each was given."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.seconds: dict[str, int] = {}

    async def set(self, key: str, value: str, ex: int | None = None, keepttl: bool = False) -> None:
        self.values[key] = value
        if not keepttl:
            self.seconds[key] = ex or 0

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)


@contextmanager
def a_fake_store() -> Generator[FakeRedis]:
    """Keep the server's records in memory for the block, sealed with a key of its own."""
    from cryptography.fernet import Fernet

    from mammoth_mcp_server import store

    fake = FakeRedis()
    store.use(fake)  # type: ignore[arg-type]
    try:
        with patch.object(store, "ENCRYPTION_KEY", Fernet.generate_key().decode()):
            yield fake
    finally:
        store.use(None)


GOOD_TOKEN = "mm_good"


def knows_the_token(
    api: FakeApi,
    workspace_id: int = WORKSPACE,
    resource: str | None = MCP_RESOURCE_URL,
) -> None:
    """Have the fake Mammoth say what a bearer token is for."""
    issued: dict[str, Any] = {"id": workspace_id}
    if resource is not None:
        issued["resource"] = resource
    api.answer("GET", "/workspaces/current", issued)
