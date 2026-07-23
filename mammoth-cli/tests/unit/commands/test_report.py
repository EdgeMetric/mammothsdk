"""Unit tests for the ``report`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import report as report_cmd
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_LIST = "mammoth.api.reports.ReportsAPI.list"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_list_with_no_input_forwards_nothing(fake_service: FakeMammothService) -> None:
    report_cmd.report_list(_inv("report.list"))
    assert fake_service.call_log == [(_LIST, {})]


def test_list_forwards_limit_and_offset(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 10, "offset": 20}), encoding="utf-8")
    report_cmd.report_list(_inv("report.list", input_file=str(doc)))
    assert fake_service.call_log == [(_LIST, {"limit": 10, "offset": 20})]


def test_list_forwards_limit_only(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"limit": 5}), encoding="utf-8")
    report_cmd.report_list(_inv("report.list", input_file=str(doc)))
    assert fake_service.call_log == [(_LIST, {"limit": 5})]


def test_list_returns_meta_with_no_project_scope(fake_service: FakeMammothService) -> None:
    fake_service.responses[_LIST] = {"reports": []}
    data, meta = report_cmd.report_list(_inv("report.list"))
    assert data == {"reports": []}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": None}
