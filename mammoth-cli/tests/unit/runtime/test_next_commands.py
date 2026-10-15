"""``meta.next_commands``: one to three filled-in next steps after a main-flow command.

The suggestions come from a small data map (``discovery/next_commands.json``),
filled in from the result's ids and the command's positionals. A write that did
not verify gets none, and human output prints them as one ``Next:`` line.
"""

from __future__ import annotations

import json
import re

import pytest

from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime import executor
from mammoth_cli.runtime.next_commands import load_map, next_commands

_PATHS = {
    str(record["command_path"])
    for record in load_commands()
    if record.get("disposition") != "alias"
}


def test_every_template_and_key_names_a_real_command() -> None:
    ids = {str(record["command_id"]) for record in load_commands()}
    for key, templates in load_map().items():
        if key.endswith(".*"):
            assert any(command_id.startswith(key[:-1]) for command_id in ids), key
        else:
            assert key in ids, key
        assert 1 <= len(templates) <= 3, key
        for template in templates:
            if template.startswith("{"):
                continue  # a command the result itself carries
            words = re.sub(r"\{[^}]*\}|--.*$", " ", template).split()[1:]
            assert any(" ".join(words[:n]) in _PATHS for n in range(1, len(words) + 1)), template


def test_a_ready_upload_suggests_reading_its_view() -> None:
    data = {
        "status": "ready",
        "dataset_ids": [5],
        "dataset_id": 5,
        "datasets": [{"id": 5, "status": "ready", "view": {"view_id": 11, "rows": 3}}],
    }
    assert next_commands("file.upload", data, {}) == ["mammoth view data get 11 5"]


def test_an_upload_that_needs_input_suggests_its_own_recovery_command() -> None:
    data = {
        "status": "need_action",
        "datasets": [
            {
                "id": 5,
                "status": "need_action",
                "next_command": "mammoth dataset file-settings get 5",
            }
        ],
    }
    assert next_commands("file.upload", data, {}) == ["mammoth dataset file-settings get 5"]


def test_a_transform_suggests_reading_the_view_back_with_its_dataset() -> None:
    assert next_commands(
        "view.transform.filter", {"status": "ok"}, {"view_id": 7}, known_dataset_id=5
    ) == ["mammoth view data get 7 5"]
    assert next_commands("view.transform.batch", {}, {"view_id": 7}) == ["mammoth view data get 7"]


def test_a_new_dashboard_suggests_reading_it_and_adding_a_figure() -> None:
    found = next_commands("dashboard.v3.generate", {"dashboard_id": 42}, {})
    assert found[0] == "mammoth dashboard get 42"
    assert found[1].startswith('mammoth dashboard figure add 42 --input \'{"intent"')


def test_figure_add_suggests_reading_the_dashboard() -> None:
    assert next_commands("dashboard.figure.add", {"figure_id": 3}, {"dashboard_id": 42}) == [
        "mammoth dashboard get 42"
    ]


@pytest.mark.parametrize(
    "data",
    [
        {"verify": {"outcome": "failed"}},
        {"verify": {"outcome": "partial"}},
        {"verify": {"verified": False}},
        {"status": "failed"},
        {"status": "partial"},
    ],
)
def test_a_write_that_did_not_verify_gets_no_suggestion(data: dict[str, object]) -> None:
    assert next_commands("view.transform.filter", data, {"view_id": 7}) == []


def test_a_command_outside_the_map_gets_none_and_ids_that_do_not_resolve_are_skipped() -> None:
    assert next_commands("project.list", {"projects": []}, {}) == []
    assert next_commands("dashboard.v3.generate", {"status": "ok"}, {}) == []


def test_next_commands_are_a_stable_meta_field_in_the_machine_envelope(
    capsys: pytest.CaptureFixture[str],
) -> None:
    executor.emit_success(
        "view.transform.filter", {"ok": True}, "json", next_commands=["mammoth view data get 7"]
    )
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["meta"]["next_commands"] == ["mammoth view data get 7"]


def test_human_output_prints_one_next_line_on_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    executor.emit_success(
        "dashboard.v3.generate",
        {"dashboard_id": 42},
        "table",
        next_commands=["mammoth dashboard get 42", "mammoth dashboard figure add 42"],
    )
    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line.startswith("Next:")]
    assert lines == ["Next: mammoth dashboard get 42; mammoth dashboard figure add 42"]
    assert "Next:" not in captured.out


def test_no_suggestions_leave_meta_without_the_field(capsys: pytest.CaptureFixture[str]) -> None:
    executor.emit_success("project.list", [], "json")
    assert "next_commands" not in json.loads(capsys.readouterr().out)["meta"]
