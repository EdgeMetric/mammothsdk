"""Every HTTP attempt is logged with its status, retry wait and gateway headers (mammothsdk#431)."""

from __future__ import annotations

import logging

import httpx
import pytest

from mammoth import client as sdk_client
from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError


class _Gateway(httpx.AsyncBaseTransport):
    """Answers the first request with a CDN 502, then 200s."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.requests = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests += 1
        if self.requests <= self.failures:
            return httpx.Response(
                502,
                content=b"{}",
                headers={
                    "Server": "CloudFront",
                    "Via": "1.1 abc.cloudfront.net (CloudFront)",
                    "X-Cache": "Error from cloudfront",
                    "X-Amz-Cf-Id": "cf-id-1",
                    "Retry-After": "0",
                    "Set-Cookie": "secret=1",
                },
                request=request,
            )
        return httpx.Response(200, content=b"{}", request=request)


def _client(transport: _Gateway, **kwargs: bool) -> MammothClient:
    made = MammothClient(
        api_key="k",
        api_secret="s",
        workspace_id=4,
        base_url="https://api.example.test/api/v2",
        **kwargs,
    )
    made.session = httpx.AsyncClient(transport=transport, headers=made.session.headers)
    return made


def _http_records(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    return [r.mammoth for r in caplog.records if hasattr(r, "mammoth")]  # type: ignore[attr-defined]


async def test_a_retried_502_logs_its_attempt_wait_and_gateway_headers(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sdk_client, "_RETRY_BACKOFF_S", 0.0)
    transport = _Gateway(failures=1)
    made = _client(transport)
    with caplog.at_level(logging.INFO, logger="mammoth.http"):
        await made._request_json("GET", "/workspaces/4/projects")
    await made.close()

    retry, final = _http_records(caplog)
    assert transport.requests == 2
    assert (retry["status"], retry["outcome"], retry["attempt"]) == (502, "retry", 1)
    assert retry["retry_wait_ms"] == 0
    assert retry["headers"] == {
        "Server": "CloudFront",
        "Via": "1.1 abc.cloudfront.net (CloudFront)",
        "X-Cache": "Error from cloudfront",
        "X-Amz-Cf-Id": "cf-id-1",
        "Retry-After": "0",
    }
    assert (final["status"], final["outcome"]) == (200, "ok")
    assert "headers" not in final


async def test_a_final_non_2xx_keeps_the_gateway_headers(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sdk_client, "_RETRY_BACKOFF_S", 0.0)
    transport = _Gateway(failures=99)
    made = _client(transport, retry_gateway_errors=False)
    with (
        caplog.at_level(logging.INFO, logger="mammoth.http"),
        pytest.raises(MammothAPIError),
    ):
        await made._request_json("GET", "/workspaces/4/projects")
    await made.close()

    [only] = _http_records(caplog)
    assert transport.requests == 1  # no retry: one attempt, one line
    assert (only["status"], only["outcome"]) == (502, "error")
    assert only["headers"]["X-Cache"] == "Error from cloudfront"  # type: ignore[index]
    assert "Set-Cookie" not in only["headers"]  # type: ignore[operator]
