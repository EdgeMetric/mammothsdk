"""Every declared ``output_schema`` resolves to a valid, self-contained JSON Schema (#315)."""

from __future__ import annotations

import json

import jsonschema
import pytest

from mammoth_cli.commands.schema import OUTPUT_SCHEMA_OPENAPI, OUTPUT_SCHEMA_REF, output_schema
from mammoth_cli.manifest.loader import command_by_id, load_commands, load_output_schemas

_RECORDS = sorted(load_commands(), key=lambda record: record["command_id"])
_READS = [record for record in _RECORDS if record["mutation_class"] == "read"]
_DECLARED = [record["command_id"] for record in _RECORDS if record.get("output_schema")]

#: Writes that declare nothing yet (their examples need inputs the sampled responses cannot
#: supply, so none could be checked). A new write must declare one; lower this as they do.
MAX_UNDECLARED_WRITES = 176


def test_every_read_command_declares_an_output_schema() -> None:
    undeclared = [r["command_id"] for r in _READS if not r.get("output_schema")]
    assert not undeclared, undeclared


def test_undeclared_writes_do_not_grow() -> None:
    undeclared = [
        r["command_id"]
        for r in _RECORDS
        if r["mutation_class"] != "read" and not r.get("output_schema")
    ]
    assert len(undeclared) <= MAX_UNDECLARED_WRITES, len(undeclared)


@pytest.mark.parametrize("command_id", _DECLARED)
def test_a_declared_schema_resolves_to_a_valid_self_contained_schema(command_id: str) -> None:
    record = command_by_id(command_id) or {}
    schema = output_schema(record)
    assert schema is not None
    jsonschema.Draft202012Validator.check_schema(schema)
    defs = schema.get("$defs", {})
    for ref in _refs(schema):
        assert ref.startswith("#/$defs/") and ref.rsplit("/", 1)[-1] in defs, ref


def test_an_openapi_declaration_is_only_for_a_command_that_has_an_api_response() -> None:
    for record in _RECORDS:
        if record.get("output_schema") == OUTPUT_SCHEMA_OPENAPI:
            assert record.get("operation_ids"), record["command_id"]


def test_every_named_schema_is_used_and_every_use_is_defined() -> None:
    named = load_output_schemas()["schemas"]
    used = {
        record["output_schema"][OUTPUT_SCHEMA_REF]
        for record in _RECORDS
        if isinstance(record.get("output_schema"), dict)
        and OUTPUT_SCHEMA_REF in record["output_schema"]
    }
    assert used <= set(named), sorted(used - set(named))
    assert set(named) <= used, sorted(set(named) - used)


def test_a_command_without_a_declaration_has_none() -> None:
    undeclared = next(r for r in _RECORDS if not r.get("output_schema"))
    assert output_schema(undeclared) is None


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
