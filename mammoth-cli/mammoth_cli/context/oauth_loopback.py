"""The loopback listener a browser sign-in receives its authorization code on.

Kept out of :mod:`mammoth_cli.context.oauth` so a command that only refreshes a token does
not import ``http.server`` (about 30 ms); only ``auth login`` opens a listener.
"""

from __future__ import annotations

import contextlib
import html
import http.server
import urllib.parse
from collections.abc import Iterator

from mammoth_cli.context.oauth import CALLBACK_PATH

_PAGE = (
    "<!doctype html><meta charset=utf-8><title>Mammoth CLI</title>"
    "<body style='font-family:system-ui;margin:3rem'><h2>{title}</h2><p>{body}</p>"
)


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server's naming
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_error(404)
            return
        params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        server = self.server
        assert isinstance(server, CallbackServer)
        server.params = params
        failed = "error" in params or "code" not in params
        title = "Sign-in failed" if failed else "Signed in"
        body = (
            "Return to the terminal for details."
            if failed
            else "You can close this tab and return to the terminal."
        )
        payload = _PAGE.format(title=html.escape(title), body=html.escape(body)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class CallbackServer(http.server.HTTPServer):
    params: dict[str, str] | None = None


@contextlib.contextmanager
def loopback_listener() -> Iterator[CallbackServer]:
    """Listen on 127.0.0.1 on a random free port, for one callback."""
    server = CallbackServer(("127.0.0.1", 0), CallbackHandler)
    try:
        yield server
    finally:
        server.server_close()
