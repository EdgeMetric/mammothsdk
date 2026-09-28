"""Every confirmed command, driven through the real argv dispatch.

Most command tests build an ``Invocation`` by hand and call the handler, so a
break between the argv parser and the confirmation gate -- a renamed ``--yes``,
a handler that sends before it confirms -- shows up in none of them. This
sends each command that needs confirmation through ``make_runner`` without
``--yes`` and checks its own request never went out. A command that needs
``--input`` stops earlier, at its own validation, which sends nothing either.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

#: Where a command without ``--yes`` may stop: the gate, or its own input checks.
_STOPS = frozenset(
    {
        "confirmation_required",
        "missing_field",
        "missing_argument",
        "invalid_argument",
        "unsupported_contract",
    }
)

_CONFIRMED = sorted(
    (
        c
        for c in load_commands()
        if c.get("confirmation") not in (None, "none")
        # a service request; ``upgrade`` is local and asks PyPI instead
        and c["sdk_symbol"].startswith("mammoth.")
    ),
    key=lambda c: c["command_id"],
)


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _argv(command: dict[str, Any]) -> list[str]:
    positionals = [
        "1" if p.get("type") == "int" else "x"
        for p in command.get("positionals", [])
        if p.get("required")
    ]
    return [
        *command["command_path"].split(),
        *positionals,
        "--project",
        "1",
        "--output",
        "json",
        "--no-input",
    ]


@pytest.mark.parametrize("command", _CONFIRMED, ids=lambda c: c["command_id"])
def test_a_confirmed_command_sends_nothing_without_yes(
    command: dict[str, Any], fake_service: FakeMammothService
) -> None:
    result = make_runner().invoke(_argv(command))

    start = result.output.find("{")
    assert start != -1, result.output
    error = json.loads(result.output[start:])["error"]
    assert result.exit_code != 0
    assert error["code"] in _STOPS, error
    assert command["sdk_symbol"] not in {symbol for symbol, _ in fake_service.call_log}
