"""Agent run instances, units, retry, request-kind and plan proposal: the wire each method sends.

Runs against a real loopback HTTP server that records every request.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError


class _RecordingServer(HTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.requests: list[dict[str, object]] = []


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
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    do_GET = do_POST = do_PATCH = _answer  # noqa: N815

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
    return MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )


async def test_units_list_sends_only_the_filters_it_was_given(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.run_units_list("s-1", "7", step=2, state="failed")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("GET", "/agents/sessions/s-1/runs/7/units")
    assert sent["query"] == {"step": "2", "state": "failed"}


async def test_units_list_with_no_filters_sends_no_query(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.run_units_list("s-1", "7")
    assert server.requests[0]["query"] == {}


async def test_instances_list_reads_the_run_instances_route(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.run_instances_list("s-1", "7")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("GET", "/agents/sessions/s-1/runs/7/instances")


async def test_instance_messages_names_the_run_and_the_instance(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.run_instance_messages("s-1", "7", "i-3")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == (
        "GET",
        "/agents/sessions/s-1/runs/7/instances/i-3/messages",
    )


async def test_instance_transcript_names_the_run_and_the_instance(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.run_instance_transcript("s-1", "7", "i-3")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == (
        "GET",
        "/agents/sessions/s-1/runs/7/instances/i-3/transcript",
    )


async def test_retry_posts_to_the_run_retry_route(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.run_retry("s-1", "7")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/agents/sessions/s-1/runs/7/retry")


async def test_set_request_kind_patches_the_kind_onto_the_message(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.agents.message_set_request_kind("s-1", "m-9", "build")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == (
        "PATCH",
        "/agents/sessions/s-1/messages/m-9/request-kind",
    )
    assert sent["body"] == {"request_kind": "build"}


async def test_plan_rename_sends_the_name(server: _RecordingServer, client: MammothClient) -> None:
    await client.agents.plan_edit_proposal("s-1", "p-1", "rename", "step-2", name="Sales")
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("PATCH", "/agents/sessions/s-1/plan/proposal")
    assert sent["body"] == {"plan_id": "p-1", "action": "rename", "key": "step-2", "name": "Sales"}


async def test_plan_remove_sends_no_name(server: _RecordingServer, client: MammothClient) -> None:
    await client.agents.plan_edit_proposal("s-1", "p-1", "remove", "step-2")
    assert server.requests[0]["body"] == {"plan_id": "p-1", "action": "remove", "key": "step-2"}


async def test_an_empty_run_id_is_refused_before_any_request(
    server: _RecordingServer, client: MammothClient
) -> None:
    with pytest.raises(MammothValidationError):
        await client.agents.run_retry("s-1", "")
    assert server.requests == []
