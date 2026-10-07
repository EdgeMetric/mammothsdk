"""``view export live-link`` against a real loopback HTTPS server (no doubles).

Only the base-URL resolver is patched, to point the CLI at the local server; the
server's self-signed certificate is trusted through ``SSL_CERT_FILE``.
"""

from __future__ import annotations

import datetime
import ipaddress
import json
import ssl
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.context import resolver
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import login_default_profile

_EXPORTS_PATH = "/api/v2/workspaces/4/projects/180/datasets/9/dataviews/7/pipeline/exports"
_LIVE_URL = "https://files.example/view_7_export_Ab12Cd34Ef56Gh78.csv"
_PLAN_ERROR = {"error": {"code": "4FEAT001", "message": "Live links are not part of this plan."}}


def _job(status: str, response: dict[str, Any]) -> dict[str, Any]:
    return {
        "job": {
            "id": 55,
            "status": status,
            "response": response,
            "last_updated_at": "2026-10-07T10:00:00",
            "created_at": "2026-10-07T10:00:00",
            "path": "/pipeline/exports",
            "operation": "add_action",
        }
    }


class _Handler(BaseHTTPRequestHandler):
    posted: list[dict[str, Any]]
    paths: list[str]
    refuse: bool

    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        type(self).paths.append(self.path)
        if self.path == "/api/v2/workspaces/current":
            self._send(200, {"id": 4})
        elif self.path == "/api/v2/workspaces/4/projects/180/datasets/9/dataviews/7":
            self._send(200, {"id": 7, "name": "Sales", "dataset_id": 9, "metadata": []})
        elif self.path.endswith("/jobs/55"):
            self._send(200, _job("success", {"url": _LIVE_URL}))
        else:
            self._send(404, {"error": {"message": f"unexpected GET {self.path}"}})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        type(self).paths.append(self.path)
        if self.path != _EXPORTS_PATH:
            self._send(404, {"error": {"message": f"unexpected POST {self.path}"}})
            return
        type(self).posted.append(body)
        if type(self).refuse:
            self._send(403, _PLAN_ERROR)
            return
        self._send(200, _job("processing", {}))

    def log_message(self, *args: object) -> None:
        return


def _self_signed(directory: Path) -> tuple[Path, Path]:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path, key_path = directory / "cert.pem", directory / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


@pytest.fixture
def server(
    isolated_cli_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[type[_Handler]]:
    login_default_profile()
    cert_path, key_path = _self_signed(tmp_path)
    _Handler.posted, _Handler.paths, _Handler.refuse = [], [], False
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base_url = f"https://127.0.0.1:{httpd.server_port}/api/v2"
    monkeypatch.setenv("SSL_CERT_FILE", str(cert_path))
    monkeypatch.setattr(resolver, "resolve_base_url", lambda _prefix: base_url)
    yield _Handler
    httpd.shutdown()


def _invoke(tmp_path: Path, payload: dict[str, object]) -> Any:
    document = tmp_path / "input.json"
    document.write_text(json.dumps(payload), encoding="utf-8")
    invocation = Invocation(
        command_id="view.export.live-link",
        project=180,
        extra_args=["7", "9"],
        input_file=str(document),
        yes=True,
    )
    return view_cmd.view_export_specialized(invocation)


def test_live_link_posts_a_flagged_s3_export_and_returns_the_url(
    server: type[_Handler], tmp_path: Path
) -> None:
    data, _meta = _invoke(tmp_path, {"file_name": "report_Ab12Cd34Ef56Gh78.csv"})

    assert data == {"url": _LIVE_URL}
    (spec,) = server.posted
    assert spec["handler_type"] == "s3"
    assert spec["additional_properties"] == {"liveLink": True}
    assert spec["target_properties"]["file"] == "report_Ab12Cd34Ef56Gh78.csv"


def test_a_caller_additional_property_is_kept_next_to_the_live_link_flag(
    server: type[_Handler], tmp_path: Path
) -> None:
    _invoke(tmp_path, {"additional_properties": {"note": "q3"}})

    assert server.posted[0]["additional_properties"] == {"note": "q3", "liveLink": True}


def test_a_plan_without_live_links_returns_the_backend_error(
    server: type[_Handler], tmp_path: Path
) -> None:
    server.refuse = True

    with pytest.raises(CliError) as error:
        _invoke(tmp_path, {})

    assert "Live links are not part of this plan." in json.dumps(error.value.to_envelope())
