"""The collection, engagement and own-data commands: reachable from argv and gated by class."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import _read_invocation
from mammoth_cli.testing import login_default_profile, make_runner

_IDS = [
    "collection.list",
    "collection.get",
    "collection.get-by-url",
    "collection.create",
    "collection.update",
    "collection.delete",
    "collection.dashboards.add",
    "collection.dashboards.remove",
    "collection.share",
    "collection.members.remove",
    "collection.for-dashboard",
    "collection.activity",
    "collection.pipeline-changes",
    "collection.files.upload",
    "collection.active-job",
    "collection.job",
    "dashboard.attachment-create",
    "dashboard.engagement.get",
    "dashboard.engagement.person",
    "dashboard.engagement.remind",
    "dashboard.own-data.start",
    "dashboard.own-data.status",
    "dashboard.own-data.preview",
    "dashboard.own-data.accept",
    "dashboard.own-data.dismiss",
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
        ("collection.delete", "prompt_or_yes", "destructive"),
        ("collection.share", "yes_always", "external_effect"),
        ("dashboard.engagement.remind", "yes_always", "external_effect"),
        ("dashboard.own-data.accept", "confirm_target", "benign_mutation"),
        ("dashboard.own-data.start", "none", "benign_mutation"),
        ("dashboard.engagement.get", "none", "read"),
        ("collection.job", "none", "read"),
        ("dashboard.attachment-create", "none", "benign_mutation"),
    ],
)
def test_the_manifest_gates_each_command_by_what_it_does(
    command_id: str, confirmation: str, mutation_class: str
) -> None:
    record = command_by_id(command_id)
    assert record is not None
    assert (record["confirmation"], record["mutation_class"]) == (confirmation, mutation_class)


def test_remind_without_yes_stops_at_the_gate(isolated_cli_config: Path) -> None:
    login_default_profile()
    result = make_runner().invoke(
        [
            "dashboard",
            "engagement",
            "remind",
            "331",
            "--input",
            json.dumps({"user_ids": [1]}),
            "--project",
            "1",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code != 0
    assert "confirmation_required" in result.output


def test_a_write_read_back_hands_the_read_its_id_as_an_int() -> None:
    """``collection delete 5`` names its id as text; the read-back SDK call refuses text."""
    read = _read_invocation(
        "collection.get", {"collection_id": "5"}, Invocation(command_id="collection.update")
    )
    assert read.positionals == {"collection_id": 5}
