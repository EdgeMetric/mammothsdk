"""Offline REL-335 CLI-to-HTTP controls for blank dashboard creation."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation


def _invocation(input_file: str, **kwargs: Any) -> Invocation:
    return Invocation(
        "dashboard.create-blank",
        output="json",
        no_input=True,
        input_file=input_file,
        **kwargs,
    )


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, service: Any):
    @contextmanager
    def context(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(dashboard_cmd, "open_service", context)
    yield


def test_rel335_approved_cli_emits_exact_wire_and_returns_response(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    api.default(201, {"id": 88, "sequence": 1})
    payload = {
        "params": {"dataview_id": 42, "style": "presentation", "title": "Revenue"}
    }
    source = tmp_path / "blank.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with _bind(monkeypatch, service):
        data, _meta = dashboard_cmd.generated_dashboard(_invocation(str(source)))
    request = api.last()
    assert request.method == "POST"
    assert request.path.removeprefix("/api/v2") == "/dashboards/v3/blank"
    assert request.json_body == payload
    assert data == {"id": 88, "sequence": 1}


def test_rel335_create_blank_needs_no_confirmation_flag(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service()
    source = tmp_path / "blank.json"
    source.write_text(json.dumps({"params": {"dataview_id": 42}}), encoding="utf-8")
    with _bind(monkeypatch, service):
        dashboard_cmd.generated_dashboard(_invocation(str(source)))
    assert len(api.requests) == 1
