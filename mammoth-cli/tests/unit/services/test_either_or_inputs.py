"""Fields another input stands in for are listed as optional, so help and the
input contract never ask for both (``automation update`` told callers ``patch*``
beside ``add_datasets``, which the handler then refuses)."""

from __future__ import annotations

import json
import shlex
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.registry import _TARGETS as REGISTRY
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.command_contract import resolve_command_contract


@pytest.mark.parametrize(
    ("command_id", "replaced", "alternative"),
    [
        ("automation.update", "patch", "add_datasets"),
        ("view.export.update", "patches", "save_as_mode"),
        ("dashboard.figure.add", "figure", "intent"),
        ("dashboard.figure.add", "dataview_id", "intent"),
    ],
)
def test_a_replaced_field_is_optional(command_id: str, replaced: str, alternative: str) -> None:
    contract = resolve_command_contract(command_id)
    assert contract is not None
    fields = {field.name: field for field in contract.fields}
    assert alternative in fields
    assert fields[replaced].required is False


def test_a_field_the_handler_defaults_is_optional() -> None:
    contract = resolve_command_contract("automation.create")
    assert contract is not None
    optional = {field.name for field in contract.fields if not field.required}
    assert "description" in optional


def test_folder_create_takes_the_parent_as_folder_list_shows_it() -> None:
    contract = resolve_command_contract("folder.create")
    assert contract is not None
    names = {field.name for field in contract.fields}
    assert "parent_resource_id" in names
    assert "parent_folder_id" not in names


@pytest.mark.parametrize(
    ("command_id", "document"),
    [
        (
            "automation.update",
            {
                "patch": [
                    {"op": "replace", "path": "details", "value": {"name": "Daily revenue export"}}
                ]
            },
        ),
        ("view.export.update", {"save_as_mode": "APPEND_TO_DS"}),
    ],
)
def test_the_agent_example_sends_a_change_the_handler_takes(
    command_id: str, document: dict[str, Any]
) -> None:
    record = next(item for item in load_commands() if item["command_id"] == command_id)
    tokens = shlex.split(record["agent_example"])
    assert json.loads(tokens[tokens.index("--input") + 1]) == document


def _refusal(command_id: str, extra_args: list[str], tmp_path: Path) -> CliError:
    """Run a handler on an empty input and return the error it raises."""
    doc = tmp_path / "in.json"
    doc.write_text("{}", encoding="utf-8")
    module, _, name = REGISTRY[command_id].partition(":")
    handler = getattr(import_module(module), name)
    with pytest.raises(CliError) as excinfo:
        handler(
            Invocation(
                command_id=command_id,
                project=180,
                extra_args=extra_args,
                input_file=str(doc),
                yes=True,
            )
        )
    return excinfo.value


@pytest.mark.parametrize(
    ("command_id", "extra_args", "named"),
    [
        ("automation.update", ["1"], ["'patch'", "add_datasets", "remove_datasets", "'schedule'"]),
        ("view.export.update", ["1", "2"], ["'patches'", "save_as_mode"]),
        ("view.conditional-format.create", ["7", "9"], ["'rule'", "columns", "operator"]),
        ("view.conditional-format.replace", ["7", "9"], ["'rule'", "columns", "operator"]),
    ],
)
def test_an_empty_input_names_every_alternative(
    command_id: str,
    extra_args: list[str],
    named: list[str],
    tmp_path: Path,
) -> None:
    error = _refusal(command_id, extra_args, tmp_path)
    assert error.code == "missing_field"
    assert "This command requires the" not in error.message
    assert [word for word in named if word not in error.message] == []
    contract = resolve_command_contract(command_id)
    assert contract is not None
    optional = {field.name for field in contract.fields if not field.required}
    assert named[0].strip("'") in optional


@pytest.mark.parametrize(
    ("command_id", "extra_args", "fields"),
    [
        ("ai.suggestion.list", [], ["suggestion_type", "params"]),
        ("batch.bulk-delete", ["1"], ["ids"]),
        ("dataset.bulk-delete", [], ["dataset_ids"]),
        ("folder.bulk-delete", [], ["folder_ids"]),
        ("project.user.add", ["180"], ["user_ids", "role"]),
        ("view.conditional-format.delete-all", ["7", "9"], ["rule_id"]),
        ("view.task.update", ["1", "2"], ["task_spec"]),
    ],
)
def test_a_field_the_command_refuses_to_run_without_is_listed_as_required(
    command_id: str,
    extra_args: list[str],
    fields: list[str],
    tmp_path: Path,
) -> None:
    error = _refusal(command_id, extra_args, tmp_path)
    assert error.code == "missing_field"
    assert f"'{fields[0]}'" in error.message
    contract = resolve_command_contract(command_id)
    assert contract is not None
    required = {field.name for field in contract.fields if field.required}
    assert set(fields) <= required
