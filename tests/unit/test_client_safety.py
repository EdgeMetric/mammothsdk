"""Safety boundaries for authenticated API requests and signed downloads."""

from __future__ import annotations

from typing import Any

import pytest
from requests.adapters import BaseAdapter
from requests.models import Response

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError


class _RedirectAdapter(BaseAdapter):
    """In-memory transport which records every request Requests attempts."""

    def __init__(self, status_code: int, location: str) -> None:
        self.status_code = status_code
        self.location = location
        self.seen: list[dict[str, object]] = []

    def send(self, request: Any, **kwargs: Any) -> Response:  # noqa: ARG002
        self.seen.append(
            {
                "url": request.url,
                "api_key": request.headers.get("X-API-KEY"),
                "api_secret": request.headers.get("X-API-SECRET"),
            }
        )
        response = Response()
        response.status_code = self.status_code
        response.url = request.url
        response.request = request
        response.headers["Location"] = self.location
        response._content = b"redirect"
        return response

    def close(self) -> None:
        pass


@pytest.mark.parametrize("status_code", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "location",
    [
        "https://api.example.test/api/v2/redirected",  # same origin
        "https://other.example.test/receive",  # cross origin
        "http://api.example.test/api/v2/redirected",  # HTTPS downgrade
    ],
)
def test_authenticated_requests_never_follow_redirects(
    status_code: int, location: str
) -> None:
    """No redirect target is contacted, regardless of origin or redirect type."""
    client = MammothClient(
        api_key="dummy-key",
        api_secret="dummy-secret",
        workspace_id=4,
        base_url="https://api.example.test/api/v2",
    )
    adapter = _RedirectAdapter(status_code, location)
    client.session.mount("https://", adapter)
    client.session.mount("http://", adapter)

    with pytest.raises(MammothAPIError) as raised:
        client._request("POST", "/datasets", json={"name": "once"})

    assert raised.value.status_code == status_code
    assert raised.value.operation_state == "outcome_unknown"
    # The only credential-bearing request is the intended API request.  A
    # redirect target, including a same-origin one, is never contacted.
    assert adapter.seen == [
        {
            "url": "https://api.example.test/api/v2/datasets",
            "api_key": "dummy-key",
            "api_secret": "dummy-secret",
        }
    ]
    client.close()


def test_authenticated_request_rejects_redirect_opt_in() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    with pytest.raises(ValueError, match="do not support redirects"):
        client._request("GET", "/projects", allow_redirects=True)

    client.close()


def test_authenticated_request_rejects_cross_origin_endpoint() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    with pytest.raises(ValueError, match="configured API origin"):
        client._request("GET", "https://other.example.test/receive")

    client.close()


@pytest.mark.parametrize("status_code", [500, 502, 504])
def test_mutation_server_error_is_outcome_unknown_with_recovery_metadata(status_code: int) -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = Response()
    response.status_code = status_code
    response._content = b'{"detail": "gateway failure"}'
    response.headers["X-Request-ID"] = "req-gateway"
    client.session.request = lambda *args, **kwargs: response  # type: ignore[method-assign]

    with pytest.raises(MammothAPIError) as raised:
        client._request("PATCH", "/datasets/9", json={"name": "changed"})

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.method == "PATCH"
    assert error.endpoint == "/datasets/9"
    assert error.request_id == "req-gateway"
    client.close()


def test_mutation_malformed_success_is_outcome_unknown_with_recovery_metadata() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = Response()
    response.status_code = 201
    response._content = b"not-json"
    response.headers["X-Request-ID"] = "req-malformed"
    client.session.request = lambda *args, **kwargs: response  # type: ignore[method-assign]

    with pytest.raises(MammothAPIError) as raised:
        client._request("POST", "/datasets", json={"name": "once"})

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.method == "POST"
    assert error.endpoint == "/datasets"
    assert error.request_id == "req-malformed"
    assert error.status_code == 201
    client.close()


def test_signed_download_session_has_no_api_credentials() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    assert "X-API-KEY" not in client.download_session.headers
    assert "X-API-SECRET" not in client.download_session.headers
    client.close()
