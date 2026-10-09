"""``DashboardsAPI.render_figure_svg``: the request it sends and the SVG it returns.

Runs against a real loopback HTTP server that records every request and answers with the body
the test sets.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="620" height="360"></svg>'
_BAR = {
    "chart": "bar",
    "title": "MRR by Plan Type",
    "width": 620,
    "height": 360,
    "data": [{"label": "Enterprise", "value": 41487}, {"label": "Professional", "value": 20571}],
}


class _RecordingServer(HTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.requests: list[dict[str, object]] = []
        self.answer: bytes = json.dumps({"svg": _SVG}).encode()


class _Handler(BaseHTTPRequestHandler):
    server: _RecordingServer

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        self.server.requests.append(
            {
                "method": self.command,
                "path": urlsplit(self.path).path.removeprefix("/api/v2"),
                "body": json.loads(raw) if raw else None,
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.server.answer)

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


async def test_render_posts_the_spec_and_returns_the_svg_text(
    server: _RecordingServer, client: MammothClient
) -> None:
    svg = await client.dashboards.render_figure_svg(_BAR)
    sent = server.requests[0]
    assert (sent["method"], sent["path"]) == ("POST", "/dashboards/v3/render/svg")
    assert sent["body"] == {"spec": _BAR, "style_id": None}
    assert svg == _SVG


async def test_render_sends_the_style_id_when_one_is_given(
    server: _RecordingServer, client: MammothClient
) -> None:
    await client.dashboards.render_figure_svg(_BAR, style_id="style-7")
    assert server.requests[0]["body"] == {"spec": _BAR, "style_id": "style-7"}


async def test_render_refuses_a_response_with_no_svg(
    server: _RecordingServer, client: MammothClient
) -> None:
    server.answer = b'{"image": "not svg"}'
    with pytest.raises(MammothValidationError, match="no `svg` string"):
        await client.dashboards.render_figure_svg(_BAR)
