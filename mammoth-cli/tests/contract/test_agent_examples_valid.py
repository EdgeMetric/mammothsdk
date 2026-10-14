"""Every command's ``agent_example`` must be safe to copy and run.

A generated example once carried the literal ``"sample"`` for string fields, so
``view transform pivot`` grouped by a column named ``sample`` and
``dataset file-settings update`` set the delimiter to ``sample``; and
``view transform lookup`` omitted the field the command requires, so it was
refused with ``invalid_arguments``. This walks every command schema and runs
each example's ``--input`` through the command's own local validation (unknown
fields, scalar types, required fields); no network.
"""

from __future__ import annotations

import copy
import json
import shlex
from typing import Any

import pytest

from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.command_contract import resolve_command_contract
from mammoth_cli.services.positionals import resolve_positionals

#: ``mammoth schema get ID``: a blocked raw request shape hands over to the schema lookup.
_HANDOFF = "mammoth schema get "
#: Never synthesized: a credential document.
_NOT_SYNTHESIZED = {"auth.login"}
#: Resolved from the active dataset/project, not typed by the caller.
_RESOLVED_FIELDS = {"dataset_id"}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in _strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    return []


def example_problems(record: dict[str, Any]) -> list[str]:
    """What is wrong with one record's ``agent_example`` (empty when it is runnable)."""
    command_id = record["command_id"]
    example = record["agent_example"]
    if command_id in _NOT_SYNTHESIZED or example.startswith(_HANDOFF):
        return []
    tokens = shlex.split(example)
    problems: list[str] = []
    if any(token.lower() == "sample" for token in tokens):
        problems.append("positional placeholder is the literal 'sample'")
    document: dict[str, Any] | None = None
    if "--input" in tokens:
        raw = tokens[tokens.index("--input") + 1]
        if not raw.startswith("{"):
            # A protected ``--input FILE`` carries the (secret) fields; nothing to check here.
            return problems
        try:
            document = json.loads(raw)
        except ValueError:
            return [*problems, "--input is not valid JSON"]
    if document is not None and any(s.lower() == "sample" for s in _strings(document)):
        problems.append("an --input string is the literal 'sample'")
    contract = resolve_command_contract(command_id)
    if contract is None:
        return problems
    given = set(document or {})
    covered = {p.name for p in resolve_positionals(command_id)} | _RESOLVED_FIELDS
    for field in contract.accepted_fields:
        if field.required and field.name not in given and field.name not in covered:
            problems.append(f"required field '{field.name}' is missing")
    if document is None:
        return problems
    try:
        validate_input_fields(command_id, copy.deepcopy(document))
    except Exception as error:  # noqa: BLE001 -- any rejection is a broken example
        problems.append(f"local validation: {getattr(error, 'code', error)}")
    return problems


def test_every_agent_example_is_runnable() -> None:
    broken = {
        record["command_id"]: problems
        for record in load_commands()
        if record.get("disposition") != "alias" and (problems := example_problems(record))
    }
    assert broken == {}


@pytest.mark.parametrize(
    ("command_id", "expected"),
    [
        ("view.transform.lookup", ("new_column", "existing_column")),
    ],
)
def test_examples_name_the_field_the_command_requires_one_of(
    command_id: str, expected: tuple[str, ...]
) -> None:
    record = next(r for r in load_commands() if r["command_id"] == command_id)
    document = json.loads(
        shlex.split(record["agent_example"])[
            shlex.split(record["agent_example"]).index("--input") + 1
        ]
    )
    assert any(name in document for name in expected)


def test_file_settings_example_uses_single_character_delimiters() -> None:
    record = next(r for r in load_commands() if r["command_id"] == "dataset.file-settings.update")
    tokens = shlex.split(record["agent_example"])
    document = json.loads(tokens[tokens.index("--input") + 1])
    assert len(document["delimiter"]) == 1 and len(document["quotechar"]) == 1


def test_the_checker_flags_the_old_broken_examples() -> None:
    base = {"disposition": "command", "agent_example": ""}
    lookup = {
        **base,
        "command_id": "view.transform.lookup",
        "agent_example": "mammoth view transform lookup 123 --input "
        + shlex.quote(
            json.dumps({"source": "A", "lookup_view_id": 1, "key": "A", "value": "sample"})
        ),
    }
    assert example_problems(lookup)
    pivot = {
        **base,
        "command_id": "view.transform.pivot",
        "agent_example": "mammoth view transform pivot 123 --input "
        + shlex.quote(json.dumps({"group_by": ["sample"], "aggregations": []})),
    }
    assert "an --input string is the literal 'sample'" in example_problems(pivot)
