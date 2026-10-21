"""Shared fixtures for bespoke command tests: a fake service seam."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.context import resolver
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    """Patch the single service-construction seam with a network-free fake."""
    service = FakeMammothService()

    def _build(
        auth: Any,
        *,
        timeout: float | None = None,
        job_timeout: float | None = None,
        pipeline_timeout: float | None = None,
        project_id: int | None = None,
        profile: str | None = None,
        progress: bool = False,
    ) -> FakeMammothService:
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    # A token names its workspace and the CLI learns it from the server; no network here.
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)
    return service


@pytest.fixture
def block_real_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail closed: a request that would leave the machine raises instead of being sent.

    The SDK's default base URL is production (``https://app.mammoth.io/api/v2``) and the login
    helpers use a dummy token, so a dry-run probe whose target reads are not faked really reaches
    production and is answered 401. Only loopback hosts (the ``_loopback`` test server) pass.
    """
    import httpx

    real_async = httpx.AsyncHTTPTransport.handle_async_request
    real_sync = httpx.HTTPTransport.handle_request

    def _check(request: httpx.Request) -> None:
        if request.url.host not in {"127.0.0.1", "localhost", "::1"}:
            raise AssertionError(f"test tried to reach the network: {request.method} {request.url}")

    async def _async(self: httpx.AsyncHTTPTransport, request: httpx.Request) -> httpx.Response:
        _check(request)
        return await real_async(self, request)

    def _sync(self: httpx.HTTPTransport, request: httpx.Request) -> httpx.Response:
        _check(request)
        return real_sync(self, request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", _async)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", _sync)
