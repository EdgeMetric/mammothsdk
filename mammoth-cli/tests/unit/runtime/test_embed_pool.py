"""``EmbedRuntime``: one host-owned loop and HTTP pool shared by embedded calls."""

from __future__ import annotations

import asyncio
import dataclasses
import threading
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.embed import EmbedRuntime, invoke, shared_pool
from mammoth_cli.runtime import embed_pool
from mammoth_cli.services import sdk_service

_WORKSPACE_OF_TOKEN: dict[str, int] = {}


@pytest.fixture(autouse=True)
def _server_names_the_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        resolver,
        "resolve_token_workspace",
        lambda _base_url, token, _timeout: _WORKSPACE_OF_TOKEN[token],
    )


def _login(workspace_id: int, user: str) -> ExplicitLogin:
    token = f"mm_{user}"
    _WORKSPACE_OF_TOKEN[token] = workspace_id
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
        api_token=token,
        server_prefix="box",
        headers={"Cookie": f"session={user}", "X-Forwarded-For-User": user},
    )


class _Server:
    """Answers every API call and keeps the requests it saw."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.lock = threading.Lock()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        with self.lock:
            self.requests.append(request)
        return httpx.Response(200, json={"projects": [], "limit": 100, "offset": 0, "next": ""})


def _runtime_on(server: _Server) -> EmbedRuntime:
    """A runtime whose pool answers from ``server`` instead of the network."""
    runtime = EmbedRuntime()
    original = runtime.http_client
    runtime.run(original.aclose())
    runtime.http_client = httpx.AsyncClient(transport=httpx.MockTransport(server))
    return runtime


@pytest.fixture
def server() -> _Server:
    return _Server()


@pytest.fixture
def runtime(server: _Server) -> Iterator[EmbedRuntime]:
    pool = _runtime_on(server)
    yield pool
    pool.close()


def test_concurrent_users_on_one_runtime_never_cross_headers(
    runtime: EmbedRuntime, server: _Server
) -> None:
    users = {f"user{n}": 100 + n for n in range(8)}
    start = threading.Barrier(len(users), timeout=20)
    results: dict[str, dict[str, Any]] = {}

    def _call(user: str, workspace_id: int) -> None:
        login = _login(workspace_id, user)
        start.wait()
        for _ in range(3):
            results[user] = invoke(["project", "list"], login=login, runtime=runtime)

    threads = [threading.Thread(target=_call, args=item) for item in users.items()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)

    assert all("data" in envelope for envelope in results.values()), results
    assert len(results) == len(users)
    api_calls = [r for r in server.requests if "/projects" in r.url.path]
    assert len(api_calls) >= len(users) * 3
    for request in api_calls:
        user = request.headers["Cookie"].removeprefix("session=")
        assert request.headers["Authorization"] == f"Bearer mm_{user}"
        assert request.headers["X-Forwarded-For-User"] == user
        assert str(users[user]) in request.url.path
    # The shared pool itself carries nothing of any user.
    for name in ("Authorization", "Cookie", "X-Forwarded-For-User", "X-Mammoth-Agent-Run"):
        assert name not in runtime.http_client.headers
    assert len(runtime.http_client.cookies) == 0


def test_the_agent_run_header_is_per_call_not_on_the_shared_pool(
    runtime: EmbedRuntime, server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An embedded call takes its run from the login's headers, never the environment.
    monkeypatch.setenv(sdk_service.AGENT_RUN_ENV, "run-env")
    ann = _login(5, "ann")
    ann = dataclasses.replace(
        ann, headers={**(ann.headers or {}), sdk_service.AGENT_RUN_HEADER: "run-7"}
    )
    assert "data" in invoke(["project", "list"], login=ann, runtime=runtime)
    assert "data" in invoke(["project", "list"], login=_login(6, "ben"), runtime=runtime)
    calls = [r for r in server.requests if "/projects" in r.url.path]
    assert calls[0].headers[sdk_service.AGENT_RUN_HEADER] == "run-7"
    assert sdk_service.AGENT_RUN_HEADER not in calls[1].headers
    assert sdk_service.AGENT_RUN_HEADER not in runtime.http_client.headers


def test_the_shared_pool_is_not_closed_by_a_call_and_runs_on_one_loop(
    runtime: EmbedRuntime, server: _Server
) -> None:
    loops: set[int] = set()
    threads: set[str] = set()

    async def _where() -> None:
        loops.add(id(asyncio.get_running_loop()))
        threads.add(threading.current_thread().name)

    for user in ("a", "b"):
        invoke(["project", "list"], login=_login(1, user), runtime=runtime)
        runtime.run(_where())
    assert not runtime.http_client.is_closed
    assert len(loops) == 1
    assert threads == {"mammoth-embed-runtime"}


def test_a_call_inside_a_running_loop_starts_no_helper_thread(
    runtime: EmbedRuntime, server: _Server
) -> None:
    before = {t.ident for t in threading.enumerate()}

    async def _host() -> dict[str, Any]:
        return invoke(["project", "list"], login=_login(3, "carl"), runtime=runtime)

    envelope = asyncio.run(_host())
    assert "data" in envelope
    assert {t.ident for t in threading.enumerate()} <= before


def test_close_stops_the_loop_thread_and_the_pool_and_is_idempotent(server: _Server) -> None:
    pool = _runtime_on(server)
    thread = pool._thread
    client = pool.http_client
    assert pool.is_open
    pool.close()
    pool.close()
    assert not pool.is_open
    assert client.is_closed
    assert not thread.is_alive()
    with pytest.raises(RuntimeError, match="closed"):
        pool.run(asyncio.sleep(0))


def test_a_closed_runtime_falls_back_to_a_client_of_the_calls_own(
    server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    pool = _runtime_on(server)
    pool.close()
    own = _Server()
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real(**{**kw, "transport": httpx.MockTransport(own)})
    )
    envelope = invoke(["project", "list"], login=_login(4, "dee"), runtime=pool)
    assert "data" in envelope
    assert own.requests and not server.requests


def test_an_sdk_without_default_headers_is_never_shared(
    runtime: EmbedRuntime, server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The PyPI floor writes headers to ``session.headers``; sharing would leak them."""
    monkeypatch.setattr(embed_pool, "sdk_takes_default_headers", lambda: False)
    monkeypatch.setattr(sdk_service, "sdk_takes_default_headers", lambda: False)
    assert not runtime.shares_safely
    own = _Server()
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real(**{**kw, "transport": httpx.MockTransport(own)})
    )
    envelope = invoke(["project", "list"], login=_login(8, "eve"), runtime=runtime)
    assert "data" in envelope
    assert not server.requests
    assert [r.headers["Cookie"] for r in own.requests if "/projects" in r.url.path] == [
        "session=eve"
    ]


def test_shared_pool_is_one_runtime_until_closed() -> None:
    first = shared_pool()
    try:
        assert shared_pool() is first
        embed_pool.close_shared_pool()
        assert not first.is_open
        second = shared_pool()
        assert second is not first and second.is_open
    finally:
        embed_pool.close_shared_pool()


def test_default_calls_are_unchanged_without_a_runtime(server: _Server) -> None:
    own = _Server()
    real = httpx.AsyncClient
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            httpx, "AsyncClient", lambda **kw: real(**{**kw, "transport": httpx.MockTransport(own)})
        )
        assert "data" in invoke(["project", "list"], login=_login(9, "fay"))
    assert own.requests


def test_closing_fails_a_call_in_flight_promptly(server: _Server) -> None:
    pool = _runtime_on(server)
    started = threading.Event()
    outcome: list[BaseException | None] = []

    async def _long() -> None:
        started.set()
        await asyncio.sleep(30)

    def _worker() -> None:
        try:
            pool.run(_long())
            outcome.append(None)
        except BaseException as exc:  # noqa: BLE001
            outcome.append(exc)

    worker = threading.Thread(target=_worker)
    worker.start()
    assert started.wait(10)
    pool.close()
    worker.join(5)
    assert not worker.is_alive()
    assert isinstance(outcome[0], RuntimeError) and "closed" in str(outcome[0])


def test_run_from_the_runtimes_own_loop_thread_raises_instead_of_deadlocking(
    runtime: EmbedRuntime,
) -> None:
    async def _inner() -> None:
        return None

    async def _host_callback() -> str:
        try:
            runtime.run(_inner())
        except RuntimeError as exc:
            return str(exc)
        return "no error"

    assert "own loop thread" in runtime.run(_host_callback())


def test_service_close_survives_a_runtime_closed_first(
    server: _Server, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The download session still closes and no error escapes ``close()``."""
    pool = _runtime_on(server)
    seen: list[sdk_service.SdkMammothService] = []
    real_init = sdk_service.SdkMammothService.__init__

    def _spy(self: Any, *args: Any, **kwargs: Any) -> None:
        real_init(self, *args, **kwargs)
        seen.append(self)

    monkeypatch.setattr(sdk_service.SdkMammothService, "__init__", _spy)
    assert "data" in invoke(["project", "list"], login=_login(2, "gus"), runtime=pool)
    service = seen[0]
    # The call closed it; reopen the case: the runtime goes away first, then close().
    service._closed = False
    service._client.download_session = httpx.AsyncClient()
    pool.close()
    service.close()
    service.close()
    assert service._client.download_session.is_closed
