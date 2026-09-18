"""Safety boundaries for authenticated API requests and signed downloads."""

from __future__ import annotations

from typing import Any

import pytest
import requests
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


@pytest.mark.parametrize(
    "base_url",
    [
        "http://api.example.test/api/v2",
        "http://127.0.0.1:8080/api/v2",
        "http://localhost.evil.test/api/v2",
        "ftp://api.example.test/api/v2",
        "https:///api/v2",
        "https://user:password@api.example.test/api/v2",
        "https://api.example.test/api/v2?tenant=wrong",
        "https://api.example.test/api/v2#fragment",
    ],
)
def test_client_rejects_insecure_or_invalid_base_url_by_default(base_url: str) -> None:
    with pytest.raises(ValueError, match="base_url must use HTTPS"):
        MammothClient("dummy-key", "dummy-secret", workspace_id=4, base_url=base_url)


@pytest.mark.parametrize(
    "base_url", ["http://localhost:8080", "http://127.0.0.1:8080", "http://[::1]:8080"]
)
def test_client_allows_explicit_loopback_http_for_development(base_url: str) -> None:
    client = MammothClient(
        "dummy-key",
        "dummy-secret",
        workspace_id=4,
        base_url=base_url,
        allow_insecure_loopback_http=True,
    )

    assert client.base_url == f"{base_url}/api/v2"
    client.close()


def test_client_rejects_nonloopback_http_even_with_development_opt_in() -> None:
    with pytest.raises(ValueError, match="loopback"):
        MammothClient(
            "dummy-key",
            "dummy-secret",
            workspace_id=4,
            base_url="http://api.example.test/api/v2",
            allow_insecure_loopback_http=True,
        )


def test_invalid_base_url_is_rejected_before_session_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_session() -> None:
        raise AssertionError("credential-bearing session must not be created")

    monkeypatch.setattr("mammoth.client.requests.Session", unexpected_session)

    with pytest.raises(ValueError, match="base_url must use HTTPS"):
        MammothClient(
            "dummy-key",
            "dummy-secret",
            workspace_id=4,
            base_url="http://api.example.test/api/v2",
        )


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


@pytest.mark.parametrize(
    ("body", "parsed"), [(b"[]", []), (b"null", None), (b'"Accepted"', "Accepted"), (b"7", 7)]
)
def test_mutation_2xx_with_non_dict_body_is_success_with_body_preserved(
    body: bytes, parsed: object
) -> None:
    """A 2xx is the server's confirmation of the write.

    Routes that declare no response schema (202 "processing continues
    off-line" deletes, PATCH /workspace segments, DELETE file_settings) answer
    with null or a scalar; reporting those as outcome_unknown told operators a
    committed delete was unconfirmed.
    """
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = Response()
    response.status_code = 202
    response._content = body
    client.session.request = lambda *args, **kwargs: response  # type: ignore[method-assign]

    assert client._request_json("DELETE", "/datasets/9") == {
        "status_code": 202,
        "response": parsed,
    }
    client.close()


def test_effectful_get_timeout_is_outcome_unknown() -> None:
    """Webhook ingestion is a mutation even though its legacy route uses GET."""
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    client.session.request = lambda *args, **kwargs: (_ for _ in ()).throw(
        requests.exceptions.ReadTimeout()
    )

    with pytest.raises(MammothAPIError) as raised:
        client.webhooks.send_data_get("ingest", {"record": "one"})

    assert raised.value.method == "GET"
    assert raised.value.operation_state == "outcome_unknown"
    client.close()


def test_effectful_get_server_error_is_outcome_unknown() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = Response()
    response.status_code = 502
    response._content = b'{"detail": "gateway failure"}'
    client.session.request = lambda *args, **kwargs: response  # type: ignore[method-assign]

    with pytest.raises(MammothAPIError) as raised:
        client.webhooks.send_data_get("ingest", {"record": "one"})

    assert raised.value.method == "GET"
    assert raised.value.operation_state == "outcome_unknown"
    client.close()


def test_list_wrapper_preserves_single_dict_and_empty_success_is_list() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    single = Response()
    single.status_code = 200
    single._content = b'{"id": 7}'
    client.session.request = lambda *args, **kwargs: single  # type: ignore[method-assign]
    assert client._request_list("GET", "/workflows") == [{"id": 7}]

    empty = Response()
    empty.status_code = 204
    empty._content = b""
    client.session.request = lambda *args, **kwargs: empty  # type: ignore[method-assign]
    assert client._request_list("GET", "/workflows") == []
    client.close()


def test_mutation_list_wrapper_keeps_scalar_success_body() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = Response()
    response.status_code = 200
    response._content = b"7"
    client.session.request = lambda *args, **kwargs: response  # type: ignore[method-assign]

    assert client._request_list("POST", "/batch-operation", json={"ids": [1]}) == [
        {"status_code": 200, "response": 7}
    ]
    client.close()


def test_signed_download_session_has_no_api_credentials() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    assert "X-API-KEY" not in client.download_session.headers
    assert "X-API-SECRET" not in client.download_session.headers
    client.close()


def test_binary_wrapper_describes_png_and_returns_html_as_text() -> None:
    # Artifact routes (og-card PNG, PDF, MP4, share page HTML) are not JSON;
    # parsing them used to raise JSONDecodeError on a successful 200.
    import base64
    import hashlib

    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    png = Response()
    png.status_code = 200
    png._content = b"\x89PNG\r\n\x1a\nfake"
    png.headers["Content-Type"] = "image/png"
    client.session.request = lambda *args, **kwargs: png  # type: ignore[method-assign]
    assert client._request_binary("GET", "/dashboards/48/og-card") == {
        "content_type": "image/png",
        "size_bytes": len(png._content),
        "sha256": hashlib.sha256(png._content).hexdigest(),
        "content_base64": base64.b64encode(png._content).decode("ascii"),
    }

    html = Response()
    html.status_code = 200
    html._content = b"<html>share</html>"
    html.headers["Content-Type"] = "text/html; charset=utf-8"
    client.session.request = lambda *args, **kwargs: html  # type: ignore[method-assign]
    described = client._request_binary("GET", "/dashboards/url/x/share")
    assert described["text"] == "<html>share</html>"
    assert "content_base64" not in described
    client.close()
