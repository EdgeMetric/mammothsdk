"""Every declared ``output_schema`` resolves to a valid, self-contained JSON Schema (#315)."""

from __future__ import annotations

import json

import jsonschema
import pytest

from mammoth_cli.commands.schema import OUTPUT_SCHEMA_OPENAPI, output_schema
from mammoth_cli.manifest.loader import command_by_id, load_commands

_DECLARED = sorted(
    record["command_id"]
    for record in load_commands()
    if record.get("output_schema") == OUTPUT_SCHEMA_OPENAPI
)


def test_read_commands_declare_output_schemas() -> None:
    assert len(_DECLARED) >= 80


@pytest.mark.parametrize("command_id", _DECLARED)
def test_a_declared_schema_is_a_read_with_a_resolvable_schema(command_id: str) -> None:
    record = command_by_id(command_id) or {}
    assert record.get("mutation_class") == "read"
    schema = output_schema(record)
    assert schema is not None
    jsonschema.Draft202012Validator.check_schema(schema)
    defs = schema.get("$defs", {})
    for ref in _refs(schema):
        assert ref.startswith("#/$defs/") and ref.rsplit("/", 1)[-1] in defs, ref


def test_a_command_without_a_declaration_has_none() -> None:
    assert output_schema(command_by_id("view.get") or {}) is None


def _refs(value: object) -> set[str]:
    text = json.dumps(value)
    found: set[str] = set()
    marker = '"$ref": "'
    start = text.find(marker)
    while start != -1:
        end = text.index('"', start + len(marker))
        found.add(text[start + len(marker) : end])
        start = text.find(marker, end)
    return found
