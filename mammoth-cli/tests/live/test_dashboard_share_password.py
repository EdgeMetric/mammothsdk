"""Live: share a dashboard behind a password, read it back, then restore ``mammoth`` sharing.

Marked ``live`` (deselected by default and in CI). It uses an existing dashboard of the
configured project, writes the password to a temporary file (never the command line), and
switches the share back to ``mammoth`` in a ``finally`` so the tenant is left as found.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live

PASSWORD = "live-test-password-1"


def _run(args: list[str], env: dict[str, str]) -> dict[str, Any]:
    """Invoke the CLI, assert a clean exit, and return the parsed envelope."""
    result = make_runner().invoke([*args, "--output", "json", "--no-input"], env=env)
    assert result.exit_code == 0, result.output
    assert PASSWORD not in result.output
    envelope: dict[str, Any] = json.loads(result.output)
    assert not envelope.get("error"), envelope.get("error")
    return envelope


def test_password_share_reads_back_has_password_and_no_hash(
    live_env: dict[str, str], live_project: str, tmp_path: Path
) -> None:
    """Share as password, see ``has_password`` true with no hash, then share as mammoth."""
    listed = _run(["dashboard", "list", "--project", live_project], live_env)["data"]
    items = listed.get("dashboards") if isinstance(listed, dict) else listed
    if not items:
        pytest.skip("no dashboard in the configured project to share")
    dashboard_id = str(items[0]["id"])
    password_file = tmp_path / "pw.txt"
    password_file.write_text(PASSWORD + "\n", encoding="utf-8")

    try:
        _run(
            [
                "dashboard",
                "share",
                dashboard_id,
                "--project",
                live_project,
                "--input",
                json.dumps({"type_of_auth": "password", "password_file": str(password_file)}),
                "--yes",
            ],
            live_env,
        )
        read = _run(["dashboard", "get", dashboard_id, "--project", live_project], live_env)
        share = json.dumps(read["data"].get("share", read["data"]))
        assert '"has_password": true' in share
        assert "hash" not in share.lower()
        assert PASSWORD not in json.dumps(read)
    finally:
        _run(
            [
                "dashboard",
                "share",
                dashboard_id,
                "--project",
                live_project,
                "--input",
                json.dumps({"type_of_auth": "mammoth"}),
                "--yes",
            ],
            live_env,
        )
