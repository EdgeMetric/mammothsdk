"""``mammoth capabilities`` and ``schema find --unsupported``: what the CLI cannot do yet.

Each entry names the area, the limitation, what to do instead, the workaround
commands and the skill doc. Every workaround must be a real command, or the
list sends an agent to a dead end.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import capabilities as capabilities_cmd
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.testing import make_runner

_COMMANDS = {
    str(record["command_id"]): str(record["command_path"])
    for record in load_commands()
    if record.get("disposition") != "alias"
}
_SKILL = Path(capabilities_cmd.__file__).parents[1] / "bundled_skill" / "mammoth-cli"


def test_every_workaround_names_a_real_command_and_an_example_of_it() -> None:
    for entry in capabilities_cmd.load_limitations():
        assert entry["workarounds"], entry["id"]
        for item in entry["workarounds"]:
            assert item["command_id"] in _COMMANDS, (entry["id"], item["command_id"])
            assert item["example"].startswith(f"mammoth {_COMMANDS[item['command_id']]}")


def test_every_entry_links_a_doc_in_the_bundled_skill() -> None:
    for entry in capabilities_cmd.load_limitations():
        assert (_SKILL / entry["doc"]).is_file(), entry["doc"]


@pytest.mark.parametrize(
    "required",
    ["file-dataset-refresh", "multi-project-token", "workbook-synthetic-data"],
)
def test_the_known_gaps_are_listed(required: str) -> None:
    assert required in {entry["id"] for entry in capabilities_cmd.load_limitations()}


def test_capabilities_lists_each_entry_with_area_limitation_workarounds_and_doc() -> None:
    result = make_runner().invoke(["capabilities", "-o", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)["data"]
    assert data["count"] == len(data["limitations"]) == len(capabilities_cmd.load_limitations())
    for entry in data["limitations"]:
        assert {"area", "limitation", "instead", "workarounds", "doc"} <= set(entry)
        for item in entry["workarounds"]:
            assert item["command"] == f"mammoth {_COMMANDS[item['command_id']]}"


def test_schema_find_unsupported_returns_the_same_list() -> None:
    result = make_runner().invoke(["schema", "find", "--unsupported", "-o", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)["data"]
    assert [e["id"] for e in data["limitations"]] == [
        e["id"] for e in capabilities_cmd.load_limitations()
    ]


def test_schema_find_unsupported_with_words_narrows_the_list() -> None:
    result = make_runner().invoke(["schema", "find", "--unsupported", "token", "-o", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)["data"]
    assert [e["id"] for e in data["limitations"]] == ["multi-project-token"]


def test_words_no_limitation_matches_list_everything_and_say_so() -> None:
    data = capabilities_cmd.unsupported("join")
    assert data["count"] == len(capabilities_cmd.load_limitations())
    assert "No known limitation matched" in data["note"]


def test_the_skill_points_to_capabilities() -> None:
    assert "mammoth capabilities" in (_SKILL / "SKILL.md").read_text(encoding="utf-8")
