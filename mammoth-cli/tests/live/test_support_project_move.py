"""Live checks: the `support` project-move reads are refused for an ordinary user.

    MAMMOTH_EVAL_TOKEN_FILE=... MAMMOTH_SERVER_PREFIX=... \\
        pytest tests/live/test_support_project_move.py -m live -v

The test identity is a normal user, not a tech admin, so the server refuses every call here
(the CLI must have accepted its arguments first, so the refusal is the server's, not a usage
error). A tech admin would get data instead; that is not what these tests run as. Nothing here
starts or purges a move. The server needs mvc-service's project-move routes (#6910).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

_USAGE_ERRORS = ("invalid_argument", "missing_argument", "missing_field", "unknown_command")


def _refusal(live_cli: LiveCli, *args: str) -> dict[str, Any]:
    """The server's refusal of an ordinary user; a usage error or a success fails the test."""
    envelope = live_cli.run(*args)
    assert "error" in envelope, envelope
    error: dict[str, Any] = envelope["error"]
    assert error["code"] not in _USAGE_ERRORS, error
    return error


def test_project_list_is_refused_for_an_ordinary_user(live_cli: LiveCli) -> None:
    workspace = live_cli.ok("workspace", "current")[0]["id"]
    _refusal(live_cli, "support", "workspace", "project", "list", str(workspace))


def test_move_check_is_refused_for_an_ordinary_user(
    live_cli: LiveCli, scratch_project: int
) -> None:
    workspace = live_cli.ok("workspace", "current")[0]["id"]
    _refusal(
        live_cli,
        *("support", "workspace", "project", "move-check", str(workspace), str(scratch_project)),
        *("--input", json.dumps({"target_workspace_id": workspace})),
    )


def test_an_unknown_move_is_refused_for_an_ordinary_user(live_cli: LiveCli) -> None:
    _refusal(live_cli, "support", "project-move", "get", "999999999")
