"""Removed features (data apps, schedule create) fail fast with no API call."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands.capability import capability_entries, find_capabilities
from mammoth_cli.commands.schema import find_schemas
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.mark.parametrize(
    "argv",
    [
        ["data-app", "list"],
        ["data-app", "get", "5"],
        ["data-app", "delete", "5", "--yes"],
        ["schedule", "create", "--yes", "--input", '{"spec": {}}'],
    ],
)
def test_removed_commands_fail_with_feature_unavailable_and_no_api_call(
    fake_service: FakeMammothService, argv: list[str]
) -> None:
    result = make_runner().invoke([*argv, "--output", "json", "--no-input"])
    assert result.exit_code != 0
    err = json.loads(result.output)["error"]
    assert err["code"] == "feature_unavailable"
    assert err["recovery_commands"]
    assert fake_service.calls == []


def test_data_app_message_and_schedule_replacement() -> None:
    out = make_runner().invoke(["data-app", "list", "--output", "json", "--no-input"]).output
    assert "Data apps were removed from Mammoth" in out
    out = make_runner().invoke(["schedule", "create", "--output", "json", "--no-input"]).output
    assert "mammoth automation create" in out


def test_removed_commands_are_hidden_from_find_and_marked_in_capabilities() -> None:
    for query in ("data app", "data-app list", "schedule create", "create schedule"):
        ids = {m["command_id"] for m in find_schemas(query)["matches"]}
        assert not {i for i in ids if i.startswith("data-app.") or i == "schedule.create"}, query
        caps = {m["canonical_command"] for m in find_capabilities(query)["matches"]}
        assert not {c for c in caps if c and (c.startswith("data-app.") or c == "schedule.create")}
    flagged = {e["canonical_command"] for e in capability_entries() if e["unavailable"]}
    assert "schedule.create" in flagged


def test_manifest_marks_every_removed_command_blocked() -> None:
    for record in load_commands():
        cid = record["command_id"]
        if cid.startswith("data-app.") or cid == "schedule.create":
            assert str(record["known_restrictions"]).startswith("BLOCKED["), cid


def test_schedule_create_says_what_to_do_for_file_datasets_without_going_in_a_circle() -> None:
    out = make_runner().invoke(
        ["schedule", "create", "--yes", "--input", '{"spec": {}}', "--output", "json", "--no-input"]
    )
    err = json.loads(out.output)["error"]
    assert "append_to_ds_id" in err["hint"]
    assert "cloud" in err["hint"]
