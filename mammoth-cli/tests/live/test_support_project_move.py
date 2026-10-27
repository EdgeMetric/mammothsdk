"""Live checks: the `support` project-move reads run for a tech admin and the server refuses others.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=... \\
        pytest tests/live/test_support_project_move.py -m live -v

The test identity may be an ordinary user: the server then refuses the call (the CLI must have
accepted its arguments first); with a tech-admin token the reads return data. Nothing here
starts or purges a move. The server needs mvc-service's project-move routes (#6910).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

_USAGE_ERRORS = ("invalid_argument", "missing_argument", "missing_field", "unknown_command")


def _run(live_cli: LiveCli, *args: str) -> dict[str, Any] | None:
    """The command's data for a tech admin; None when the server refused an ordinary user."""
    envelope = live_cli.run(*args)
    if "error" in envelope:
        assert envelope["error"]["code"] not in _USAGE_ERRORS, envelope["error"]
        return None
    data: dict[str, Any] = envelope["data"]
    return data


def test_project_list_holds_the_scratch_project(live_cli: LiveCli, scratch_project: int) -> None:
    workspace = live_cli.ok("workspace", "current")[0]["id"]
    data = _run(live_cli, "support", "workspace", "project", "list", str(workspace))
    if data is not None:
        assert scratch_project in [row["id"] for row in data["projects"]]


def test_move_check_lists_blockers_and_warnings(live_cli: LiveCli, scratch_project: int) -> None:
    workspace = live_cli.ok("workspace", "current")[0]["id"]
    data = _run(
        live_cli,
        *("support", "workspace", "project", "move-check", str(workspace), str(scratch_project)),
        *("--input", json.dumps({"target_workspace_id": workspace})),
    )
    if data is not None:
        assert {"blockers", "warnings", "summary"} <= set(data["check"])


def test_an_unknown_move_is_not_found_or_refused(live_cli: LiveCli) -> None:
    envelope = live_cli.run("support", "project-move", "get", "999999999")
    assert "error" in envelope and envelope["error"]["code"] not in _USAGE_ERRORS
