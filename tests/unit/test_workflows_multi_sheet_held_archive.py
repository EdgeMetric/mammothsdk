"""Workflow save, archive, attach, held resolve and multi-sheet file calls: the wire each sends.

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
        self.server.requests.append(
            {
                "method": self.command,
                "path": parts.path.removeprefix("/api/v2"),
                "query": {k: v[0] for k, v in parse_qs(parts.query).items()},
                "body": json.loads(raw) if raw else None,
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
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


async def test_save_posts_the_chosen_keys_and_expected_version(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.workflows.save(12, keys=["change-1"], expected_version=7)
    assert server.requests[-1] == {
        "method": "POST",
        "path": "/workspaces/1/projects/25654/workflows/12/save",
        "query": {},
        "body": {"keys": ["change-1"], "expected_version": 7},
    }


async def test_save_without_keys_sends_no_body_fields(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.workflows.save(12)
    assert server.requests[-1]["body"] == {}


async def test_archive_puts_the_flag_and_the_datasets_to_the_archived_route(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.workflows.set_archived(12, archived=True, dataset_ids=[3, 4])
    assert server.requests[-1] == {
        "method": "PUT",
        "path": "/workspaces/1/projects/25654/workflows/12/archived",
        "query": {},
        "body": {"archived": True, "dataset_ids": [3, 4]},
    }


async def test_attach_dataset_posts_the_datasource_id(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.workflows.attach_dataset(12, datasource_id=415)
    assert server.requests[-1] == {
        "method": "POST",
        "path": "/workspaces/1/projects/25654/workflows/12/datasets",
        "query": {},
        "body": {"datasource_id": 415},
    }


async def test_resolve_held_posts_the_key_and_whether_it_is_built(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.workflows.resolve_held(12, key="held-1", built=False, expected_version=2)
    assert server.requests[-1] == {
        "method": "POST",
        "path": "/workspaces/1/projects/25654/workflows/12/held/resolve",
        "query": {},
        "body": {"key": "held-1", "built": False, "expected_version": 2},
    }


async def test_multi_sheet_preview_posts_the_sheet_to_the_preview_route(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.files.preview_multi_sheet(9, sheet_name="Sales 2", block_id="b1")
    assert server.requests[-1] == {
        "method": "POST",
        "path": "/workspaces/1/projects/25654/files/9/sheets/interpretation/preview",
        "query": {},
        "body": {"sheet_name": "Sales 2", "block_id": "b1"},
    }


async def test_multi_sheet_extract_posts_the_tables_and_the_delete_flag(
    server: _RecordingServer, client: MammothClient
) -> None:
    table = {"sheet_name": "Sales 2", "dataset_name": "Sales 2", "structure_map": {"h": 1}}
    await client.files.create_datasets_from_multi_sheet(9, [table], delete_file_after_extract=False)
    assert server.requests[-1] == {
        "method": "POST",
        "path": "/workspaces/1/projects/25654/files/9/multi-sheet-extraction",
        "query": {},
        "body": {"tables": [table], "delete_file_after_extract": False},
    }
