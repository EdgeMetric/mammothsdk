"""The ``auto`` output default: a table on a terminal, JSON when piped.

``--output`` defaults to ``auto`` so neither a human nor an agent needs a flag.
The alias resolves once, at :class:`~mammoth_cli.runtime.invocation.Invocation`
construction, from whether stdout is a terminal.
"""

from __future__ import annotations

import json

import pytest

from mammoth_cli.output.policy import SELECTABLE_OUTPUTS, resolve_output
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.testing import make_runner


def test_resolve_output_auto_on_a_terminal_is_a_table() -> None:
    assert resolve_output("auto", is_tty=True) == "table"


def test_resolve_output_auto_when_piped_is_json() -> None:
    assert resolve_output("auto", is_tty=False) == "json"


@pytest.mark.parametrize("mode", ["table", "json", "yaml", "ndjson", "plain"])
def test_resolve_output_leaves_a_concrete_mode_unchanged(mode: str) -> None:
    assert resolve_output(mode, is_tty=True) == mode
    assert resolve_output(mode, is_tty=False) == mode


def test_auto_is_a_selectable_output_value() -> None:
    assert "auto" in SELECTABLE_OUTPUTS


def test_invocation_resolves_auto_from_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """``Invocation`` resolves ``auto`` against ``sys.stdout.isatty()``."""
    import sys

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert Invocation(command_id="project.list", output="auto").output == "table"
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert Invocation(command_id="project.list", output="auto").output == "json"


def test_default_output_is_json_when_not_a_terminal(isolated_cli_config: object) -> None:
    """With no ``--output`` flag and a non-terminal stdout, output is JSON.

    The in-process runner is never a terminal, so an unflagged invocation must
    produce the machine envelope an agent or pipeline can parse.
    """
    result = make_runner().invoke(["auth", "status"])
    assert result.exit_code == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["data"]["has_credentials"] is False
