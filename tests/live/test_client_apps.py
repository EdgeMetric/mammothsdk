"""Live checks of ``client_apps`` against a real apiv2 (QA W7-17).

The SDK once modelled these payloads wrongly, so a create succeeded on the server and
then raised in the SDK with its one-time token never shown. Real SDK, real server, no
doubles. Keys are named ``uqa-live-*`` and revoked in teardown; no assertion carries a
token or key. Client-app management needs a signed-in session, not an ``mm_`` token, so
the auth headers come from a factory. Tests are plain functions driving ``asyncio.run``
so they also run where pytest-asyncio is not installed::

    MAMMOTH_LIVE_BASE_URL=http://localhost:8260 MAMMOTH_LIVE_API_ROOT= \\
    MAMMOTH_LIVE_WORKSPACE_ID=4 \\
    MAMMOTH_LIVE_AUTH_FACTORY=api.agents.evals.session_login:get_caller_auth_headers \\
        pytest tests/live/test_client_apps.py -v
"""

from __future__ import annotations

import asyncio
import importlib
import os
import time
import warnings
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import pytest

from mammoth import MammothClient

_ENV = ("MAMMOTH_LIVE_BASE_URL", "MAMMOTH_LIVE_WORKSPACE_ID", "MAMMOTH_LIVE_AUTH_FACTORY")


@asynccontextmanager
async def _client() -> AsyncIterator[MammothClient]:
    if missing := [name for name in _ENV if not os.environ.get(name)]:
        pytest.skip(f"live config not set: {', '.join(missing)}")
    module, _, name = os.environ["MAMMOTH_LIVE_AUTH_FACTORY"].partition(":")
    headers = dict(getattr(importlib.import_module(module), name)())
    bearer = headers.pop("Authorization").split(" ", 1)[1]
    base = os.environ["MAMMOTH_LIVE_BASE_URL"]
    live = MammothClient(
        token_provider=lambda: bearer,
        workspace_id=int(os.environ["MAMMOTH_LIVE_WORKSPACE_ID"]),
        base_url=base,
        api_root=os.environ.get("MAMMOTH_LIVE_API_ROOT", "/api/v2"),
        allow_insecure_loopback_http=base.startswith(("http://127.0.0.1", "http://localhost")),
    )
    live.session.headers.update(headers)
    try:
        yield live
    finally:
        await live.session.aclose()


def _run(body: Callable[[MammothClient, list[str]], Awaitable[None]]) -> None:
    """Run ``body`` with a live client; revoke every key it registers, even on failure."""

    async def main() -> None:
        async with _client() as client:
            keys: list[str] = []
            try:
                await body(client, keys)
            finally:
                # Also sweep by name: a create that raised after the server made the key
                # never reached ``keys``.
                for app in (await client.client_apps.list(limit=100)).result:
                    if app.app_key and (
                        app.app_key in keys or (app.app_name or "").startswith(f"uqa-live-{_RUN}-")
                    ):
                        await client.client_apps.delete(client_key=app.app_key)
            left = (await client.client_apps.list(limit=100)).result
            assert not [a for a in left if (a.app_name or "").startswith(f"uqa-live-{_RUN}-")]

    asyncio.run(main())


_RUN = time.time_ns()


def _name() -> str:
    return f"uqa-live-{_RUN}-{time.time_ns()}"


def test_list_parses_the_live_payload() -> None:
    async def body(client: MammothClient, keys: list[str]) -> None:
        apps = (await client.client_apps.list()).result
        assert apps
        for app in apps:
            assert isinstance(app.id, int)
            assert isinstance(app.app_name, str)
            assert isinstance(app.app_key, str)
            assert app.type in ("token", "legacy")
            assert isinstance(app.workspace_id, int)

    _run(body)


def test_list_with_fields_returns_only_those_fields() -> None:
    async def body(client: MammothClient, keys: list[str]) -> None:
        apps = (await client.client_apps.list(fields="id,app_name,description")).result
        assert apps
        assert apps[0].id is not None and apps[0].app_name is not None
        assert apps[0].app_key is None

    _run(body)


def test_create_with_description_returns_the_token() -> None:
    async def body(client: MammothClient, keys: list[str]) -> None:
        name = _name()
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # a model-drift warning is a failure here
            created = await client.client_apps.create(app_name=name, description="uqa live test")
        keys.append(created.app_key)
        assert created.app_name == name
        assert created.description == "uqa live test"
        assert created.token.startswith("mm_")

    _run(body)


def test_create_without_description_succeeds() -> None:
    async def body(client: MammothClient, keys: list[str]) -> None:
        name = _name()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            created = await client.client_apps.create(app_name=name)
        keys.append(created.app_key)
        assert created.app_name == name
        assert created.description == ""
        assert created.token.startswith("mm_")

    _run(body)


def test_get_and_revoke() -> None:
    async def body(client: MammothClient, keys: list[str]) -> None:
        created = await client.client_apps.create(app_name=_name())
        keys.append(created.app_key)
        fetched = await client.client_apps.get(client_key=created.app_key)
        assert fetched.app_name == created.app_name
        assert fetched.type == "token"
        await client.client_apps.delete(client_key=created.app_key)
        keys.remove(created.app_key)
        left = (await client.client_apps.list(limit=100)).result
        assert created.app_key not in [a.app_key for a in left]

    _run(body)
