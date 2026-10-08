"""The request log must not carry a credential.

`/workspaces/<id>/clientapps/<app_key>` names the API token itself: the same
string a caller authenticates with, matched against `ClientApp.app_key` on the
server. The logger already keeps headers and bodies out; the path it writes has
to hide the token too, in the message and in the structured record alike.
"""

from __future__ import annotations

import json
import logging

import httpx
import pytest

from mammoth.client import REDACTED, MammothClient, safe_log_path

API_KEY = "mm_live_do_not_log_me"
CLIENT_APP_PATH = f"/workspaces/4/clientapps/{API_KEY}"


class _Answering(httpx.AsyncBaseTransport):
    """A transport that answers every request with the same empty object."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{}", request=request)


class TestThePathALogKeeps:
    def test_the_clientapps_segment_is_hidden(self) -> None:
        assert safe_log_path(CLIENT_APP_PATH) == f"/workspaces/4/clientapps/{REDACTED}"

    def test_a_path_with_no_credential_is_left_alone(self) -> None:
        assert safe_log_path("/workspaces/4/projects/9/datasets") == (
            "/workspaces/4/projects/9/datasets"
        )

    def test_the_clientapps_listing_itself_is_left_alone(self) -> None:
        assert safe_log_path("/workspaces/4/clientapps") == "/workspaces/4/clientapps"

    def test_a_query_string_is_dropped(self) -> None:
        # No caller embeds one today; a log is the wrong place to find out
        # that one started to.
        asked = "/workspaces/4/files?connection_key=s3cr3t"
        assert safe_log_path(asked) == "/workspaces/4/files"

    def test_both_are_handled_at_once(self) -> None:
        assert safe_log_path(f"{CLIENT_APP_PATH}?fields=__min") == (
            f"/workspaces/4/clientapps/{REDACTED}"
        )


@pytest.fixture
def client() -> MammothClient:
    made = MammothClient(
        api_key="dummy-key",
        api_secret="dummy-secret",
        workspace_id=4,
        base_url="https://api.example.test/api/v2",
    )
    made.session = httpx.AsyncClient(
        transport=_Answering(), headers=made.session.headers, follow_redirects=False
    )
    return made


class TestTheRequestLog:
    async def test_no_log_record_carries_the_api_key(
        self, client: MammothClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="mammoth.http"):
            await client._request_json("GET", CLIENT_APP_PATH)
        await client.close()

        assert caplog.records, "the request log said nothing at all"
        for record in caplog.records:
            assert API_KEY not in record.getMessage()
            assert API_KEY not in json.dumps(getattr(record, "mammoth", {}))

    async def test_the_structured_path_is_the_redacted_one(
        self, client: MammothClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="mammoth.http"):
            await client._request_json("GET", CLIENT_APP_PATH)
        await client.close()

        [structured] = [r for r in caplog.records if hasattr(r, "mammoth")]
        assert structured.mammoth["path"] == f"/workspaces/4/clientapps/{REDACTED}"

    async def test_an_ordinary_path_still_reaches_the_log_intact(
        self, client: MammothClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="mammoth.http"):
            await client._request_json("GET", "/workspaces/4/projects")
        await client.close()

        [structured] = [r for r in caplog.records if hasattr(r, "mammoth")]
        assert structured.mammoth["path"] == "/workspaces/4/projects"
