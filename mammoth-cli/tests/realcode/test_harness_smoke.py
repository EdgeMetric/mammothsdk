"""Smoke test proving the real-code harness runs everything but the socket.

This exercises the genuine dispatch path (``resolve_sdk_method`` → bound
sub-client method → ``MammothClient._request`` → ``requests``) with only the
HTTP transport faked, and asserts on the request the real code emitted.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.errors.envelope import CliError

ServiceFactory = Callable[..., Any]


def test_real_dispatch_emits_real_http_request(real_service: ServiceFactory) -> None:
    """A generic ``call`` reaches the API as a real, correctly shaped request."""
    service, api = real_service()
    api.on("GET", r"/projects", 200, {"projects": [{"id": 1, "name": "p"}]})

    result = service.call("ProjectsAPI.list")

    assert api.requests, "no HTTP request was emitted"
    assert api.last().method == "GET"
    assert api.last().path.endswith("/projects")
    assert result == {"projects": [{"id": 1, "name": "p"}]}


def test_real_error_status_maps_through_real_sdk(real_service: ServiceFactory) -> None:
    """A 404 flows through the real SDK exception mapping, not a mock."""
    service, api = real_service()
    api.default(404, {"detail": "nope"})

    try:
        service.call("ProjectsAPI.get", project=999999)
    except CliError as exc:
        assert exc.exit_status == 5  # resource_not_found
    else:  # pragma: no cover - the call must raise
        raise AssertionError("expected a CliError for a 404 response")
