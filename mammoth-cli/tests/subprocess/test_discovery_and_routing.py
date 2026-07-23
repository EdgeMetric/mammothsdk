"""Subprocess tests for agent discovery and prefix-command routing (findings #1, #2).

These run the real ``mammoth`` entry point end to end (argv -> Typer -> handler)
and assert the exact behaviors a review found broken:

* the documented discovery commands ``schema get`` / ``capability get`` accept
  their id positional and return a well-formed envelope (finding #1);
* a command whose path is also the prefix of other commands
  (``dataset file-settings``) is invocable at an unambiguous leaf and never
  swallows its id as a subcommand name (finding #2);
* a machine-output failure at the Click layer (unknown command, an id read as a
  subcommand, a bad option value) is emitted as the stable JSON envelope, never
  Click prose or a traceback (finding #2).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

import pytest

pytestmark = pytest.mark.subprocess

_EXIT_OK = 0
_EXIT_USAGE = 2
# Any ambient Mammoth credentials are stripped so each subprocess starts logged
# out. There is no environment credential path; these names are cleared purely
# for test hygiene.
_MAMMOTH_ENV = (
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_SERVER_PREFIX",
)


def _run(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )


def _base_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in _MAMMOTH_ENV:
        env.pop(key, None)
    return env


def _envelope(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """Parse the JSON envelope from a machine-mode run, asserting no traceback."""
    assert "Traceback" not in result.stderr, result.stderr
    return json.loads(result.stdout or result.stderr)


# --- finding #1: discovery commands accept their id positional -----------------


def test_schema_get_accepts_command_id_positional() -> None:
    """The exact documented command returns the schema record, not a usage error."""
    result = _run(
        ["schema", "get", "view.transform.bulk-replace", "--output", "json", "--no-input"],
        env=_base_env(),
    )
    assert result.returncode == _EXIT_OK, result.stderr
    payload = _envelope(result)
    assert payload.get("error") is None
    assert payload["data"]["command_id"] == "view.transform.bulk-replace"


def test_capability_get_accepts_operation_id_positional() -> None:
    """``capability get`` (keyed by operation id) accepts its positional."""
    result = _run(
        ["capability", "get", "AddTask", "--output", "json", "--no-input"],
        env=_base_env(),
    )
    assert result.returncode == _EXIT_OK, result.stderr
    payload = _envelope(result)
    assert payload.get("error") is None
    assert payload["data"]["operation_id"] == "AddTask"


def test_schema_get_without_id_is_a_clean_missing_argument() -> None:
    """Omitting the id yields the stable missing-argument envelope, not a crash."""
    result = _run(["schema", "get", "--output", "json", "--no-input"], env=_base_env())
    assert result.returncode == _EXIT_USAGE, result.stderr
    payload = _envelope(result)
    assert payload["error"]["code"] == "missing_argument"


# --- finding #2: prefix-command routing + machine envelope on Click errors ------


def test_file_settings_get_is_invocable_at_the_leaf() -> None:
    """``dataset file-settings get ID`` routes to the handler (not 'No such command').

    Without credentials it stops at a handler-level error (a missing active
    project), but crucially it is NOT rejected as an unexpected positional and is
    NOT mistaken for a subcommand -- proving the leaf/parent ambiguity is gone.
    """
    result = _run(
        ["dataset", "file-settings", "get", "123", "--output", "json", "--no-input"],
        env=_base_env(),
    )
    payload = _envelope(result)
    code = payload["error"]["code"]
    assert code not in {"unexpected_argument", "usage_error"}, payload


def test_old_file_settings_form_is_a_machine_envelope() -> None:
    """The retired ``dataset file-settings ID`` form fails as JSON, not Click prose."""
    result = _run(
        ["dataset", "file-settings", "123", "--output", "json", "--no-input"],
        env=_base_env(),
    )
    assert result.returncode == _EXIT_USAGE, result.stderr
    payload = _envelope(result)
    assert payload["error"]["code"] == "usage_error"


def test_unknown_command_is_a_machine_envelope() -> None:
    """An unknown command under --output json is the JSON envelope, not a traceback."""
    result = _run(["frobnicate", "--output", "json"], env=_base_env())
    assert result.returncode == _EXIT_USAGE, result.stderr
    payload = _envelope(result)
    assert payload["error"]["code"] == "usage_error"


def test_bad_option_value_is_a_machine_envelope() -> None:
    """A malformed option value at the Click layer is the JSON envelope too."""
    result = _run(
        ["dataset", "list", "--project", "notanint", "--output", "json", "--no-input"],
        env=_base_env(),
    )
    assert result.returncode == _EXIT_USAGE, result.stderr
    payload = _envelope(result)
    assert payload["error"]["code"] == "usage_error"


def test_unknown_command_human_mode_stays_click_prose() -> None:
    """Human output is unchanged: Click's own usage message, not a JSON envelope."""
    result = _run(["frobnicate"], env=_base_env())
    assert result.returncode == _EXIT_USAGE
    assert "Traceback" not in result.stderr
    combined = result.stdout + result.stderr
    assert "Usage:" in combined
    with pytest.raises(json.JSONDecodeError):
        json.loads(combined)
