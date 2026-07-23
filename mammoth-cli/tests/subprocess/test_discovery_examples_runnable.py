"""The advertised discovery examples actually run, and required ids render right.

Review finding (fifth pass):

* ``schema get --help`` / ``capability get --help`` advertised a runnable example
  whose id placeholder was the literal ``example`` -- which resolves to nothing,
  so copy-pasting the advertised command exited non-zero (``schema_not_found`` /
  ``capability_not_found``). The generated example for every *offline discovery*
  command must now execute to exit zero.
* required positional ids were rendered as optional strings. ``dataset get
  --help`` must show a required ``<int>`` id, not an optional ``[...] <str>``.

Both run the real ``mammoth`` entry point end to end.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys

import pytest

from mammoth_cli.context.resolver import (
    ENV_API_KEY,
    ENV_API_SECRET,
    ENV_SERVER_PREFIX,
    ENV_WORKSPACE_ID,
)
from mammoth_cli.manifest.loader import command_by_id

pytestmark = pytest.mark.subprocess

# Commands whose handler answers entirely from the in-process catalog -- no
# network, no credentials, no filesystem mutation -- so their advertised example
# must run to exit zero anywhere, including a clean machine.
_DISCOVERY_COMMANDS = ["schema.list", "schema.get", "capability.list", "capability.get"]
_MAMMOTH_ENV = (ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID, ENV_SERVER_PREFIX)


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in _MAMMOTH_ENV:
        env.pop(key, None)
    # A wide, fixed width so rich never wraps the help panels under test.
    env["COLUMNS"] = "200"
    return env


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=_clean_env(),
    )


@pytest.mark.parametrize("command_id", _DISCOVERY_COMMANDS)
def test_advertised_discovery_example_runs_to_exit_zero(command_id: str) -> None:
    """The command's generated ``agent_example`` executes successfully offline."""
    record = command_by_id(command_id)
    assert record is not None, command_id
    example = record["agent_example"]
    tokens = shlex.split(example)
    assert tokens[0] == "mammoth", example
    result = _run(tokens[1:])
    assert result.returncode == 0, f"{example!r}\nstdout={result.stdout}\nstderr={result.stderr}"


def test_dataset_get_help_shows_required_integer_id() -> None:
    """A required int id renders as required + ``<int>``, not optional ``<str>``."""
    result = _run(["dataset", "get", "--help"])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "DATASET_ID" in out
    assert "<int>" in out
    assert "[required]" in out
    # The old, misleading optional/string rendering must be gone.
    assert "[DATASET_ID]" not in out
