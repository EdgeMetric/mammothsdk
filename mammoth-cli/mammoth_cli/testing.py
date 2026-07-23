"""Test helpers for driving the CLI in-process.

Kept in the package (not tests/) so contract tests and subprocess tests share
one runner and one envelope contract.
"""

from __future__ import annotations

import json
import re
from typing import Any

from typer.testing import CliRunner
from typer.testing import Result as CliResult

from mammoth_cli.app import app
from mammoth_cli.output.envelope import Meta, Result

# Control characters and common Rich markup that must never reach machine stdout.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x1b]")
_RICH_MARKUP = re.compile(r"\[/?[a-z][a-z0-9 _.#=-]*\]")


class Runner:
    def __init__(self) -> None:
        self._runner = CliRunner()

    def invoke(self, args: list[str], env: dict[str, str] | None = None) -> CliResult:
        return self._runner.invoke(app, args, env=env or {})

    def invoke_help(self, command_path: str) -> str:
        result = self.invoke([*command_path.split(), "--help"])
        return result.output


def make_runner() -> Runner:
    return Runner()


def login_default_profile(*, workspace_id: int = 4) -> None:
    """Persist a default profile and credentials for tests that need auth.

    Authentication requires a login; there is no environment credential path,
    so a test that needs an authenticated context calls this (under the
    ``isolated_cli_config`` fixture) instead of setting ``MAMMOTH_*`` variables.
    """
    from mammoth_cli.context import credentials, profiles

    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=workspace_id))
    credentials.store_credentials("default", "k", "s", storage="file")
    profiles.set_selected("default")


def sample_success_envelope() -> dict[str, Any]:
    result = Result(
        data={"id": 1, "name": "example"},
        meta=Meta(command="dataset list", profile="default", workspace_id=4, project_id=42),
    )
    return result.to_envelope()


def stdout_is_clean(envelope: dict[str, Any]) -> bool:
    """True if the JSON envelope carries no control codes or Rich markup."""
    text = json.dumps(envelope, ensure_ascii=False)
    if _CONTROL.search(text):
        return False
    if _RICH_MARKUP.search(text):
        return False
    return True
