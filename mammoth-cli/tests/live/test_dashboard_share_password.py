"""Live: a password share is read back; a server that stores no password is refused.

Marked ``live`` (deselected by default and in CI). It makes its own throwaway dashboard in a
scratch project, writes the password to a private temporary file (never the command line) and
deletes the dashboard in a ``finally``, so no existing board's sharing is touched.

    pytest tests/live/test_dashboard_share_password.py -m live -v
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live

PASSWORD = "live-test-password-1"


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def test_password_share_is_read_back_or_refused_and_restored(
    live_cli: LiveCli, sales_data: SalesData, tmp_path: Path
) -> None:
    """With PRD-656 the board reads back ``has_password`` true and no hash; without it the
    CLI refuses with ``unsupported_by_server`` and the share is put back."""
    project = sales_data.project
    created, _ = live_cli.ok(
        "dashboard",
        "create-blank",
        *_input({"params": {"dataview_id": sales_data.view, "title": "Password share check"}}),
        "--yes",
        project=project,
    )
    board = str(int(created["id"]))
    password_file = tmp_path / "pw.txt"
    password_file.write_text(PASSWORD + "\n", encoding="utf-8")
    password_file.chmod(0o600)
    try:
        envelope = live_cli.run(
            "dashboard",
            "share",
            board,
            *_input({"type_of_auth": "password", "password_file": str(password_file)}),
            "--yes",
            project=project,
        )
        assert PASSWORD not in json.dumps(envelope)
        read, _ = live_cli.ok("dashboard", "get", board, project=project)
        share = read.get("share") or {}
        assert PASSWORD not in json.dumps(read)
        assert "hash" not in json.dumps(share).lower()
        if "error" not in envelope:
            assert share.get("type_of_auth") == "password", share
            assert (share.get("options") or {}).get("has_password") is True, share
        else:
            error = envelope["error"]
            assert error["code"] == "unsupported_by_server", error
            assert (error.get("details") or {}).get("share_restored") is True, error
            assert share.get("type_of_auth") != "password", share
    finally:
        live_cli.run(*("dashboard", "delete", board, "--yes", "--confirm", board), project=project)
