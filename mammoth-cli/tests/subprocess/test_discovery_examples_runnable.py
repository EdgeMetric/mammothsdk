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
import re
import shlex
import subprocess
import sys

import pytest

from mammoth_cli.manifest.loader import command_by_id

pytestmark = pytest.mark.subprocess

# Matches CSI SGR/escape sequences Rich emits for styling.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _normalize(text: str) -> str:
    """Strip ANSI styling and collapse all whitespace to single spaces.

    Rich renders ``--help`` into a bordered panel whose exact wrapping depends
    on the effective terminal width, which is not reliably controllable in a
    non-TTY subprocess (a CI runner can wrap or truncate where a local shell
    does not). Normalizing away styling and layout whitespace lets the test
    assert the *semantic* content (name, metavar, required marker) instead of a
    brittle byte-for-byte panel rendering.
    """
    return " ".join(_ANSI_RE.sub("", text).split())

# Commands whose handler answers entirely from the in-process catalog -- no
# network, no credentials, no filesystem mutation -- so their advertised example
# must run to exit zero anywhere, including a clean machine.
_DISCOVERY_COMMANDS = ["schema.list", "schema.get", "capability.list", "capability.get"]
# Ambient Mammoth credentials are stripped so each subprocess starts logged out.
# There is no environment credential path; these names are cleared for hygiene.
_MAMMOTH_ENV = (
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_SERVER_PREFIX",
)


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in _MAMMOTH_ENV:
        env.pop(key, None)
    # Force a wide, deterministic help width. typer reads TERMINAL_WIDTH and, when
    # set, builds its help Console with that explicit width -- overriding the
    # tty/COLUMNS/GITHUB_ACTIONS auto-detection in typer.rich_utils that otherwise
    # makes rich wrap and ellipsis-truncate argument cells differently on a CI
    # runner than in a local shell (which silently dropped the "<int>" metavar in
    # CI). COLUMNS is set too as a belt-and-braces fallback for other tools.
    env["TERMINAL_WIDTH"] = "1000"
    env["COLUMNS"] = "1000"
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
    # Normalize away rich styling and layout whitespace so the assertions test
    # the semantic help content, not a width-dependent panel rendering.
    out = _normalize(result.stdout)
    assert "DATASET_ID" in out, out
    # The metavar proves the id is typed as an int, not a bare string.
    assert "<int>" in out, out
    assert "[required]" in out, out
    # The required id renders in the usage line as {DATASET_ID}; the old,
    # misleading optional rendering ([DATASET_ID] / a bare <str>) must be gone.
    assert "{DATASET_ID}" in out, out
    assert "[DATASET_ID]" not in out
