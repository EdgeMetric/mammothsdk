"""Shared fixtures for the Mammoth CLI test suite.

Both ``mammoth-io`` (SDK) and ``mammoth-cli`` are installed as editable
packages in the development and CI environments, so no ``sys.path``
manipulation is needed to import them.

The :func:`real_service` fixture builds a genuine
:class:`~mammoth_cli.services.sdk_service.SdkMammothService` whose only faked
element is the external HTTP transport. Every layer above the socket — CLI
dispatch, the service, SDK sub-clients, the rich ``View``, its mixins, and the
payload builders — runs for real, so tests exercise production code rather than
mocks of it.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import keyring
import keyring.backends.fail
import pytest

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.sdk_service import SdkMammothService

#: Environment that makes a real browser unreachable from any test or child process.
#: ``BROWSER=true`` makes ``webbrowser.open`` run ``true``; with no display variable
#: there is nothing for a desktop browser to draw on either.
NO_BROWSER_ENV = {"BROWSER": "true"}
DISPLAY_VARIABLES = ("DISPLAY", "WAYLAND_DISPLAY")


def pytest_configure(config: pytest.Config) -> None:
    """Cut the test process, and every child it spawns, off from the desktop browser.

    Runs before collection, so a test that spawns ``auth login`` (OAuth opens the
    system browser) can never open one, however the suite is invoked.
    """
    os.environ.update(NO_BROWSER_ENV)
    for name in DISPLAY_VARIABLES:
        os.environ.pop(name, None)


#: Keyring backend child processes use in tests: no keyring at all.
NO_KEYRING_BACKEND = "keyring.backends.fail.Keyring"

Route = Callable[["RecordedRequest"], "tuple[int, Any]"]


@pytest.fixture(autouse=True)
def isolated_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep every test, and every subprocess it spawns, off the real credentials.

    HOME and the XDG directories move into ``tmp_path`` so no config or credential
    file under the developer's home is read or written. The OS keyring is reached
    through the D-Bus session, so that address is dropped and the keyring backend
    is the always-failing one: a child process (which ignores the in-process
    keyring the unit and realcode fixtures install) finds no keyring and can never
    log in, log out or delete a stored profile on the real one.
    """
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name, leaf in (
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_DATA_HOME", "data"),
        ("XDG_STATE_HOME", "state"),
        ("XDG_CACHE_HOME", "cache"),
    ):
        monkeypatch.setenv(name, str(home / leaf))
    monkeypatch.delenv("DBUS_SESSION_BUS_ADDRESS", raising=False)
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", NO_KEYRING_BACKEND)
    keyring.set_keyring(keyring.backends.fail.Keyring())


@pytest.fixture(autouse=True)
def isolated_run_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Send every test's run log to a disposable directory.

    The CLI logs each invocation to the platform state directory; tests must
    never write there. Subprocess-based tests inherit the variable.
    """
    log_dir = tmp_path / "mammoth-run-log"
    monkeypatch.setenv("MAMMOTH_LOG_DIR", str(log_dir))
    # The daily update check must never reach PyPI from a test, nor read the
    # developer's real cache; tests of the check itself re-enable it.
    monkeypatch.setenv("MAMMOTH_NO_UPDATE_CHECK", "1")
    monkeypatch.setenv("MAMMOTH_UPDATE_CACHE", str(tmp_path / "update-check.json"))
    # Session defaults from the developer's shell must not leak into tests.
    for name in (
        "MAMMOTH_PROFILE",
        "MAMMOTH_PROJECT",
        "MAMMOTH_OUTPUT",
        "MAMMOTH_NO_INPUT",
        "MAMMOTH_JSON_PRETTY",
    ):
        monkeypatch.delenv(name, raising=False)
    # The skill install state is per machine; doctor and sync must never read
    # or refresh the developer's real installs.
    monkeypatch.setattr(
        "mammoth_cli.skills.installer._state_path",
        lambda: tmp_path / "skill-state" / "install-state-v1.json",
    )
    # The view-parent memory is per machine; tests start with an empty one.
    monkeypatch.setenv("MAMMOTH_PARENT_CACHE", str(tmp_path / "view-parents.json"))
    return log_dir


@pytest.fixture(autouse=True)
def _stable_help_width(monkeypatch: pytest.MonkeyPatch) -> None:
    """Render CLI help at a stable width regardless of the host terminal.

    Rich derives its console width from ``COLUMNS`` (falling back to the
    detected terminal size), so a narrow or differing value on a CI runner can
    wrap option names and break help-text assertions that pass locally.
    Pinning a wide width keeps rendered help deterministic everywhere.
    """
    monkeypatch.setenv("COLUMNS", "200")


@dataclass
class RecordedRequest:
    """One HTTP request the real code emitted through the faked transport."""

    method: str
    url: str
    path: str
    query: dict[str, list[str]]
    json_body: Any


class FakeApi(httpx.AsyncBaseTransport):
    """An httpx transport that fakes the external Mammoth API only.

    Register responses with :meth:`on`; inspect emitted requests with
    :attr:`requests`. Unmatched requests get the default response (200 ``{}``)
    unless :meth:`default` changed it.
    """

    def __init__(self) -> None:
        """Initialize a transport with no routes and a 200/empty default."""
        self.requests: list[RecordedRequest] = []
        self._routes: list[tuple[str, re.Pattern[str], Route]] = []
        self._default: tuple[int, Any] = (200, {})

    def on(
        self,
        method: str,
        path_regex: str,
        status: int = 200,
        body: Any = None,
        handler: Route | None = None,
    ) -> FakeApi:
        """Register a response for requests matching ``method`` and ``path_regex``.

        Args:
            method: HTTP method to match (case-insensitive).
            path_regex: Regex searched against the request URL path.
            status: Status code to return when no ``handler`` is given.
            body: JSON body to return when no ``handler`` is given.
            handler: Optional callable mapping the request to ``(status, body)``.

        Returns:
            This adapter, to allow chaining.
        """
        route: Route = handler or (lambda _req: (status, {} if body is None else body))
        self._routes.append((method.upper(), re.compile(path_regex), route))
        return self

    def default(self, status: int, body: Any) -> FakeApi:
        """Set the response for requests that match no registered route."""
        self._default = (status, body)
        return self

    def last(self) -> RecordedRequest:
        """Return the most recently emitted request."""
        return self.requests[-1]

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Record the request and return the matching canned response."""
        parsed = urlparse(str(request.url))
        body: Any = None
        # A streaming request (a multipart upload) refuses `.content` until it
        # has been read, and a transport is the thing that reads it.
        await request.aread()
        # httpx reports a bodyless request as empty bytes, where requests
        # reported None; the fixtures are written against "no body at all".
        raw = request.content or None
        if raw is not None:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            try:
                body = json.loads(raw)
            except (ValueError, TypeError):
                body = raw
        record = RecordedRequest(
            method=request.method,
            url=str(request.url),
            path=parsed.path,
            query=parse_qs(parsed.query),
            json_body=body,
        )
        self.requests.append(record)

        status, payload = self._default
        for method, pattern, route in self._routes:
            if method == request.method and pattern.search(parsed.path):
                status, payload = route(record)
                break

        return httpx.Response(
            status,
            content=b"" if payload is None else json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            request=request,
        )


ServiceFactory = Callable[..., "tuple[SdkMammothService, FakeApi]"]


@pytest.fixture
def real_service() -> ServiceFactory:
    """Return a factory that builds a real service with a faked HTTP transport.

    The factory accepts optional ``project_id``, ``base_url`` and ``api``
    keywords and returns ``(service, api)``: a genuine
    :class:`~mammoth_cli.services.sdk_service.SdkMammothService` and the
    :class:`FakeApi` given to its client. Pass ``api`` to mount an existing
    transport, so several services record into one. The base url is never
    contacted; it is only recorded.
    """

    def _factory(
        *,
        project_id: int | None = None,
        base_url: str = "https://fake.mammoth.test/api/v2",
        api: FakeApi | None = None,
    ) -> tuple[SdkMammothService, FakeApi]:
        auth = ResolvedAuth(api_key="k", api_secret="s", workspace_id=4, base_url=base_url)
        service = SdkMammothService(auth, project_id=project_id)
        api = api or FakeApi()
        # Keep the credentials the real session carries; swap only the wire.
        service._client.session = httpx.AsyncClient(
            transport=api, headers=service._client.session.headers, follow_redirects=False
        )
        return service, api

    return _factory
