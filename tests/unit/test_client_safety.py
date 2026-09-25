"""Safety boundaries for authenticated API requests and signed downloads."""

from __future__ import annotations

from typing import Any

import pytest
from unittest.mock import AsyncMock

import httpx

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError


class _RedirectAdapter(httpx.AsyncBaseTransport):
    """In-memory transport which records every request the client attempts."""

    def __init__(self, status_code: int, location: str) -> None:
        self.status_code = status_code
        self.location = location
        self.seen: list[dict[str, object]] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(
            {
                "url": str(request.url),
                "api_key": request.headers.get("X-API-KEY"),
                "api_secret": request.headers.get("X-API-SECRET"),
            }
        )
        return httpx.Response(
            self.status_code,
            headers={"Location": self.location},
            content=b"redirect",
            request=request,
        )


@pytest.mark.parametrize("status_code", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "location",
    [
        "https://api.example.test/api/v2/redirected",  # same origin
        "https://other.example.test/receive",  # cross origin
        "http://api.example.test/api/v2/redirected",  # HTTPS downgrade
    ],
)
async def test_authenticated_requests_never_follow_redirects(
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
    # Keep the credentials the real session carries; swap only the wire.
    client.session = httpx.AsyncClient(
        transport=adapter, headers=client.session.headers, follow_redirects=False
    )

    with pytest.raises(MammothAPIError) as raised:
        await client._request("POST", "/datasets", json={"name": "once"})

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
    await client.close()


async def test_authenticated_request_rejects_redirect_opt_in() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    with pytest.raises(ValueError, match="do not support redirects"):
        await client._request("GET", "/projects", allow_redirects=True)

    await client.close()


async def test_authenticated_request_rejects_cross_origin_endpoint() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    with pytest.raises(ValueError, match="configured API origin"):
        await client._request("GET", "https://other.example.test/receive")

    await client.close()


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
async def test_client_rejects_insecure_or_invalid_base_url_by_default(base_url: str) -> None:
    with pytest.raises(ValueError, match="base_url must use HTTPS"):
        MammothClient("dummy-key", "dummy-secret", workspace_id=4, base_url=base_url)


@pytest.mark.parametrize(
    "base_url", ["http://localhost:8080", "http://127.0.0.1:8080", "http://[::1]:8080"]
)
async def test_client_allows_explicit_loopback_http_for_development(base_url: str) -> None:
    client = MammothClient(
        "dummy-key",
        "dummy-secret",
        workspace_id=4,
        base_url=base_url,
        allow_insecure_loopback_http=True,
    )

    assert client.base_url == f"{base_url}/api/v2"
    await client.close()


async def test_client_rejects_nonloopback_http_even_with_development_opt_in() -> None:
    with pytest.raises(ValueError, match="loopback"):
        MammothClient(
            "dummy-key",
            "dummy-secret",
            workspace_id=4,
            base_url="http://api.example.test/api/v2",
            allow_insecure_loopback_http=True,
        )


async def test_invalid_base_url_is_rejected_before_session_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_session() -> None:
        raise AssertionError("credential-bearing session must not be created")

    monkeypatch.setattr("mammoth.client.httpx.AsyncClient", unexpected_session)

    with pytest.raises(ValueError, match="base_url must use HTTPS"):
        MammothClient(
            "dummy-key",
            "dummy-secret",
            workspace_id=4,
            base_url="http://api.example.test/api/v2",
        )


@pytest.mark.parametrize("status_code", [500, 502, 504])
async def test_mutation_server_error_is_outcome_unknown_with_recovery_metadata(
    status_code: int,
) -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = httpx.Response(
        status_code,
        content=b'{"detail": "gateway failure"}',
        headers={"X-Request-ID": "req-gateway"},
    )
    client.session.request = AsyncMock(return_value=response)

    with pytest.raises(MammothAPIError) as raised:
        await client._request("PATCH", "/datasets/9", json={"name": "changed"})

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.method == "PATCH"
    assert error.endpoint == "/datasets/9"
    assert error.request_id == "req-gateway"
    await client.close()


async def test_mutation_malformed_success_is_outcome_unknown_with_recovery_metadata() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = httpx.Response(201, content=b"not-json", headers={"X-Request-ID": "req-malformed"})
    client.session.request = AsyncMock(return_value=response)

    with pytest.raises(MammothAPIError) as raised:
        await client._request("POST", "/datasets", json={"name": "once"})

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.method == "POST"
    assert error.endpoint == "/datasets"
    assert error.request_id == "req-malformed"
    assert error.status_code == 201
    await client.close()


@pytest.mark.parametrize(
    ("body", "parsed"), [(b"[]", []), (b"null", None), (b'"Accepted"', "Accepted"), (b"7", 7)]
)
async def test_mutation_2xx_with_non_dict_body_is_success_with_body_preserved(
    body: bytes, parsed: object
) -> None:
    """A 2xx is the server's confirmation of the write.

    Routes that declare no response schema (202 "processing continues
    off-line" deletes, PATCH /workspace segments, DELETE file_settings) answer
    with null or a scalar; reporting those as outcome_unknown told operators a
    committed delete was unconfirmed.
    """
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = httpx.Response(202, content=body)
    client.session.request = AsyncMock(return_value=response)

    assert await client._request_json("DELETE", "/datasets/9") == {
        "status_code": 202,
        "response": parsed,
    }
    await client.close()


async def test_effectful_get_timeout_is_outcome_unknown() -> None:
    """Webhook ingestion is a mutation even though its legacy route uses GET."""
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    client.session.request = lambda *args, **kwargs: (_ for _ in ()).throw(
        httpx.ReadTimeout("timed out")
    )

    with pytest.raises(MammothAPIError) as raised:
        await client.webhooks.send_data_get("ingest", {"record": "one"})

    assert raised.value.method == "GET"
    assert raised.value.operation_state == "outcome_unknown"
    await client.close()


async def test_effectful_get_server_error_is_outcome_unknown() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = httpx.Response(502, content=b'{"detail": "gateway failure"}')
    client.session.request = AsyncMock(return_value=response)

    with pytest.raises(MammothAPIError) as raised:
        await client.webhooks.send_data_get("ingest", {"record": "one"})

    assert raised.value.method == "GET"
    assert raised.value.operation_state == "outcome_unknown"
    await client.close()


async def test_list_wrapper_preserves_single_dict_and_empty_success_is_list() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    single = httpx.Response(200, content=b'{"id": 7}')
    client.session.request = AsyncMock(return_value=single)
    assert await client._request_list("GET", "/workflows") == [{"id": 7}]

    empty = httpx.Response(204, content=b"")
    client.session.request = AsyncMock(return_value=empty)
    assert await client._request_list("GET", "/workflows") == []
    await client.close()


async def test_mutation_list_wrapper_keeps_scalar_success_body() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)
    response = httpx.Response(200, content=b"7")
    client.session.request = AsyncMock(return_value=response)

    assert await client._request_list("POST", "/batch-operation", json={"ids": [1]}) == [
        {"status_code": 200, "response": 7}
    ]
    await client.close()


async def test_signed_download_session_has_no_api_credentials() -> None:
    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    assert "X-API-KEY" not in client.download_session.headers
    assert "X-API-SECRET" not in client.download_session.headers
    await client.close()


async def test_binary_wrapper_describes_png_and_returns_html_as_text() -> None:
    # Artifact routes (og-card PNG, PDF, MP4, share page HTML) are not JSON;
    # parsing them used to raise JSONDecodeError on a successful 200.
    import base64
    import hashlib

    client = MammothClient("dummy-key", "dummy-secret", workspace_id=4)

    png = httpx.Response(
        200, content=b"\x89PNG\r\n\x1a\nfake", headers={"Content-Type": "image/png"}
    )
    client.session.request = AsyncMock(return_value=png)
    assert await client._request_binary("GET", "/dashboards/48/og-card") == {
        "content_type": "image/png",
        "size_bytes": len(png._content),
        "sha256": hashlib.sha256(png._content).hexdigest(),
        "content_base64": base64.b64encode(png._content).decode("ascii"),
    }

    html = httpx.Response(
        200, content=b"<html>share</html>", headers={"Content-Type": "text/html; charset=utf-8"}
    )
    client.session.request = AsyncMock(return_value=html)
    described = await client._request_binary("GET", "/dashboards/url/x/share")
    assert described["text"] == "<html>share</html>"
    assert "content_base64" not in described
    await client.close()


async def test_signed_download_session_has_no_bearer_token() -> None:
    client = MammothClient(api_token="mm_dummy", workspace_id=4)

    assert "Authorization" not in client.download_session.headers
    assert client.session.headers["Authorization"] == "Bearer mm_dummy"
    await client.close()
