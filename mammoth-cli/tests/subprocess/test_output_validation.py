"""Subprocess coverage for invalid output modes at the CLI boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.subprocess


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    for key in (
        "MAMMOTH_API_KEY",
        "MAMMOTH_API_SECRET",
        "MAMMOTH_WORKSPACE_ID",
        "MAMMOTH_SERVER_PREFIX",
    ):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )


def test_invalid_output_mode_on_redirected_stdout_is_machine_error() -> None:
    """A redirected invocation emits only the parseable error envelope on stderr."""
    result = _run(["project", "list", "--output", "bogus"])

    assert result.returncode == 2
    assert result.stdout == ""
    assert "error [invalid_output_mode]" not in result.stderr
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_output_mode"


def test_invalid_output_mode_in_explicit_agent_mode_is_machine_error() -> None:
    """``--no-input`` keeps an invalid-mode failure machine-readable for agents."""
    result = _run(["project", "list", "--output", "bogus", "--no-input"])

    assert result.returncode == 2
    assert result.stdout == ""
    envelope = json.loads(result.stderr)
    assert envelope["error"]["code"] == "invalid_output_mode"
