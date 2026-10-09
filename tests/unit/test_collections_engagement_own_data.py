"""Collections, board engagement and own-data: the wire each SDK method sends, and its input checks.

Runs against a real loopback HTTP server that records every request.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError


class _RecordingServer(HTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.requests: list[dict[str, object]] = []
        self.status = 200


class _Handler(BaseHTTPRequestHandler):
    server: _RecordingServer

    def _answer(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        parts = urlsplit(self.path)
        content_type = self.headers.get("Content-Type", "")
        self.server.requests.append(
            {
                "method": self.command,
                "path": parts.path.removeprefix("/api/v2"),
                "query": {k: v[0] for k, v in parse_qs(parts.query).items()},
                "body": json.loads(raw) if raw and "json" in content_type else raw,
            }
        )
        self.send_response(self.server.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.server.status != 204:
            self.wfile.write(b'{"ok": true}')

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _answer  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def server() -> Iterator[_RecordingServer]:
    srv = _RecordingServer()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def client(server: _RecordingServer) -> MammothClient:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.set_project_id(25654)
    return c


async def test_create_collection_posts_name_project_and_boards(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.collections.create("Q3 pack", dashboard_ids=[331, 7])
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/collections")
    assert sent["body"] == {
        "project_id": 25654,
        "name": "Q3 pack",
        "description": None,
        "dashboard_ids": [331, 7],
    }


async def test_delete_collection_reports_deleted_on_an_empty_204(
    server: _RecordingServer, client: MammothClient
) -> None:
    server.status = 204
    result = await client.collections.delete(9)
    assert (server.requests[0]["method"], server.requests[0]["path"]) == (
        "DELETE",
        "/collections/9",
    )
    assert result == {"collection_id": 9, "deleted": True}


async def test_share_posts_the_emails_to_the_collection(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.collections.share(9, ["a@example.com", "b@example.com"])
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/collections/9/share")
    assert sent["body"] == {"emails": ["a@example.com", "b@example.com"]}


async def test_collections_for_dashboard_reads_the_for_dashboard_route(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.collections.for_dashboard(331)
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("GET", "/collections/for-dashboard/331")


async def test_upload_files_sends_multipart_and_the_append_target(
    server: _RecordingServer, client: MammothClient, tmp_path: Path
) -> None:
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    await client.collections.upload_files(9, [str(csv)], append_to_ds_id=44)
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/collections/9/files")
    assert sent["query"] == {"append_to_ds_id": "44"}
    assert b'name="files"' in sent["body"] and b"a,b" in sent["body"]  # type: ignore[operator]


async def test_collection_inputs_are_refused_before_any_request(
    server: _RecordingServer, client: MammothClient
) -> None:
    with pytest.raises(MammothValidationError):
        await client.collections.create("")
    with pytest.raises(MammothValidationError):
        await client.collections.share(9, [])
    with pytest.raises(MammothValidationError):
        await client.collections.update(9)
    with pytest.raises(MammothValidationError):
        await client.collections.get(0)
    assert server.requests == []


async def test_engagement_asks_for_the_window_and_viewer_filter(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.dashboards.engagement(331, days=7, viewers="named")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("GET", "/dashboards/331/engagement")
    assert sent["query"] == {"days": "7", "viewers": "named"}


async def test_engagement_remind_posts_the_user_ids(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.dashboards.engagement_remind(331, [5, 6])
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/dashboards/331/engagement/remind")
    assert sent["body"] == {"user_ids": [5, 6]}


async def test_engagement_refuses_a_window_the_server_does_not_offer(
    server: _RecordingServer, client: MammothClient
) -> None:
    with pytest.raises(MammothValidationError):
        await client.dashboards.engagement(331, days=14)
    with pytest.raises(MammothValidationError):
        await client.dashboards.engagement_remind(331, [])
    assert server.requests == []


async def test_own_data_start_wraps_the_one_source_in_params(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.dashboards.own_data_start(12, dataview_id=79643, file_name="sales.csv")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/dashboards/v3/12/own-data")
    assert sent["body"] == {"params": {"dataview_id": 79643, "file_name": "sales.csv"}}


async def test_own_data_start_needs_exactly_one_source(
    server: _RecordingServer, client: MammothClient
) -> None:
    with pytest.raises(MammothValidationError):
        await client.dashboards.own_data_start(12)
    with pytest.raises(MammothValidationError):
        await client.dashboards.own_data_start(12, dataset_id=1, dataview_id=2)
    assert server.requests == []


async def test_own_data_accept_and_dismiss_use_their_own_routes(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.dashboards.own_data_accept(12, choice="proposal", exclude=["Region"])
    await client.dashboards.own_data_dismiss(12)
    accept, dismiss = server.requests
    assert accept["path"] == "/dashboards/v3/12/own-data/accept"
    assert accept["body"] == {"params": {"choice": "proposal", "exclude": ["Region"]}}
    assert (dismiss["method"], dismiss["path"]) == ("POST", "/dashboards/v3/12/own-data/dismiss")


async def test_active_job_reads_the_in_flight_upload_route(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.collections.active_job(9)
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("GET", "/collections/9/active-job")


async def test_job_polls_one_upload_job_of_the_collection(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.collections.job(9, 4)
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("GET", "/collections/9/jobs/4")


async def test_job_refuses_a_non_positive_job_id_before_any_request(
    server: _RecordingServer, client: MammothClient
) -> None:
    with pytest.raises(MammothValidationError):
        await client.collections.job(9, 0)
    assert server.requests == []


async def test_attachment_create_posts_the_workbook_as_multipart(
    server: _RecordingServer, client: MammothClient, tmp_path: Path
) -> None:
    workbook = tmp_path / "sales.twb"
    workbook.write_bytes(b"<workbook>sales-marker</workbook>")
    await client.dashboards.attachment_create(workbook)
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/dashboards/v3/attachments")
    assert b'filename="sales.twb"' in sent["body"] and b"sales-marker" in sent["body"]  # type: ignore[operator]


async def test_attachment_create_refuses_a_missing_file_before_any_request(
    server: _RecordingServer, client: MammothClient, tmp_path: Path
) -> None:
    with pytest.raises(MammothValidationError):
        await client.dashboards.attachment_create(tmp_path / "missing.pbix")
    assert server.requests == []
