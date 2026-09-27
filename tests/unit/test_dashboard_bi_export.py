"""Offline SDK contract tests for the dashboard-to-BI-file export surface.

Covers the four release routes: GET .../powerbi, GET .../powerbi/export,
GET .../tableau, GET .../tableau/export -- typed pre-flight parsing, the
disk-writing export methods, and the no-network URL builders used by the
embedded (in-product agent) path.
"""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError
from mammoth.models.dashboards import (
    PowerBiPreflightResponse,
    TableauPreflightResponse,
)

_PREFLIGHT_BODY = {
    "exportable": True,
    "blocked_reason": None,
    "figures_total": 5,
    "figures_exported": 4,
    "figures_refused": 1,
    "degraded": False,
    "refusals": [{"title": "Q&A board", "reason": "Q&A figures have no static export"}],
    "row_count": 1000,
    "column_count": 12,
}


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    client.base_url = "https://app.mammoth.io/api/v2"
    return DashboardsAPI(client), client


# ── Pre-flight ────────────────────────────────────────────────────────────────


def test_powerbi_preflight_gets_exact_route_and_types_response() -> None:
    api, client = _api()
    client._request_json.return_value = _PREFLIGHT_BODY
    result = api.powerbi_preflight(42)
    client._request_json.assert_called_once_with("GET", "/dashboards/42/powerbi")
    assert isinstance(result, PowerBiPreflightResponse)
    assert result.exportable is True
    assert result.figures_exported == 4
    assert result.figures_refused == 1
    assert result.degraded is False
    assert result.row_count == 1000
    assert result.column_count == 12
    assert result.refusals[0].title == "Q&A board"
    assert result.refusals[0].reason == "Q&A figures have no static export"


def test_tableau_preflight_gets_exact_route_and_types_response() -> None:
    api, client = _api()
    client._request_json.return_value = _PREFLIGHT_BODY
    result = api.tableau_preflight(42)
    client._request_json.assert_called_once_with("GET", "/dashboards/42/tableau")
    assert isinstance(result, TableauPreflightResponse)
    assert result.figures_total == 5


def test_powerbi_preflight_blocked_reason_surfaces() -> None:
    api, client = _api()
    client._request_json.return_value = {
        **_PREFLIGHT_BODY,
        "exportable": False,
        "blocked_reason": "Q&A boards have no static figures to export",
        "figures_total": 0,
        "figures_exported": 0,
        "figures_refused": 0,
        "refusals": [],
        "row_count": 0,
        "column_count": 0,
    }
    result = api.powerbi_preflight(42)
    assert result.exportable is False
    assert result.blocked_reason == "Q&A boards have no static figures to export"
    assert result.refusals == []


# ── Export (terminal mode: writes bytes to a local path) ────────────────────


def test_export_powerbi_writes_decoded_bytes_to_explicit_path(tmp_path: Path) -> None:
    api, client = _api()
    content = b"PK\x03\x04-fake-zip-bytes"
    client._request_binary.return_value = {
        "content_type": "application/zip",
        "size_bytes": len(content),
        "sha256": "irrelevant",
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
    destination = tmp_path / "board.zip"
    result = api.export_powerbi(42, output_path=destination)
    assert result == destination
    assert destination.read_bytes() == content
    assert list(tmp_path.glob("*.part")) == []
    client._request_binary.assert_called_once_with("GET", "/dashboards/42/powerbi/export")


def test_export_tableau_writes_decoded_bytes_to_explicit_path(tmp_path: Path) -> None:
    api, client = _api()
    content = b"<workbook>fake-twbx-bytes</workbook>"
    client._request_binary.return_value = {
        "content_type": "application/octet-stream",
        "size_bytes": len(content),
        "sha256": "irrelevant",
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
    destination = tmp_path / "board.twbx"
    result = api.export_tableau(42, output_path=destination)
    assert result == destination
    assert destination.read_bytes() == content
    client._request_binary.assert_called_once_with("GET", "/dashboards/42/tableau/export")


def test_export_powerbi_auto_generates_filename_in_cwd_when_no_output_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api, client = _api()
    content = b"zip-bytes"
    client._request_binary.return_value = {
        "content_type": "application/zip",
        "size_bytes": len(content),
        "sha256": "irrelevant",
        "content_base64": base64.b64encode(content).decode("ascii"),
    }
    monkeypatch.chdir(tmp_path)
    result = api.export_powerbi(7)
    assert result == Path("dashboard_7_powerbi.zip")
    assert result.read_bytes() == content


@pytest.mark.parametrize("dashboard_id", [0, -1, True, "7"])
def test_export_powerbi_rejects_invalid_id_without_request(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        api.export_powerbi(dashboard_id)
    client._request_binary.assert_not_called()


@pytest.mark.parametrize("dashboard_id", [0, -1, True, "7"])
def test_export_tableau_rejects_invalid_id_without_request(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        api.export_tableau(dashboard_id)
    client._request_binary.assert_not_called()
