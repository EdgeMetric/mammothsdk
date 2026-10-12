"""The agent run instance, units, retry, request-kind and plan commands: reachable and gated."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.testing import login_default_profile, make_runner

_IDS = [
    "agent.run.units.list",
    "agent.run.instance.list",
    "agent.run.instance.messages",
    "agent.run.instance.transcript",
    "agent.run.retry",
    "agent.message.set-request-kind",
    "agent.plan.edit-proposal",
]


@pytest.mark.parametrize("command_id", _IDS)
def test_the_command_is_registered_and_reachable_from_the_cli(command_id: str) -> None:
    assert command_id in HANDLERS
    record = command_by_id(command_id)
    assert record is not None
    result = make_runner().invoke([*record["command_path"].split(), "--help"])
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("command_id", "confirmation", "mutation_class"),
    [
        ("agent.run.retry", "prompt_or_yes", "benign_mutation"),
        ("agent.run.units.list", "none", "read"),
        ("agent.run.instance.transcript", "none", "read"),
        ("agent.message.set-request-kind", "none", "benign_mutation"),
    ],
)
def test_the_manifest_gates_each_command_by_what_it_does(
    command_id: str, confirmation: str, mutation_class: str
) -> None:
    record = command_by_id(command_id)
    assert record is not None
    assert (record["confirmation"], record["mutation_class"]) == (confirmation, mutation_class)


def test_retry_without_yes_stops_at_the_gate(isolated_cli_config: Path) -> None:
    login_default_profile()
    result = make_runner().invoke(
        [
            "agent",
            "run",
            "retry",
            "7",
            "--session",
            "s-1",
            "--project",
            "1",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code != 0
    assert "confirmation_required" in result.output


def test_request_kind_without_the_field_is_refused_before_any_request(
    isolated_cli_config: Path,
) -> None:
    login_default_profile()
    result = make_runner().invoke(
        [
            "agent",
            "message",
            "set-request-kind",
            "m-9",
            "--session",
            "s-1",
            "--input",
            json.dumps({}),
            "--project",
            "1",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code != 0
    assert "missing_field" in result.output
