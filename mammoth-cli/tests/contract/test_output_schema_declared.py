"""Every declared ``output_schema`` resolves to a valid, self-contained JSON Schema (#315)."""

from __future__ import annotations

import json

import jsonschema
import pytest

from mammoth_cli.commands.schema import (
    OUTPUT_SCHEMA_OPENAPI,
    OUTPUT_SCHEMA_REF,
    dry_run_output_schema,
    output_schema,
)
from mammoth_cli.manifest.loader import command_by_id, load_commands, load_output_schemas

_RECORDS = sorted(load_commands(), key=lambda record: record["command_id"])
_DECLARED = [record["command_id"] for record in _RECORDS if record.get("output_schema")]


def test_every_command_declares_an_output_schema() -> None:
    """Reads and writes alike: a new command must say what its ``data`` is."""
    undeclared = [r["command_id"] for r in _RECORDS if not r.get("output_schema")]
    assert not undeclared, undeclared
    assert len(_DECLARED) == len(_RECORDS) >= 851


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


def test_a_record_without_a_declaration_has_no_schema() -> None:
    assert output_schema({"command_id": "x", "mutation_class": "read"}) is None


def test_a_write_exposes_the_dry_run_report_a_read_has_none() -> None:
    read = next(r for r in _RECORDS if r["mutation_class"] == "read")
    write = next(r for r in _RECORDS if r["mutation_class"] != "read")
    assert dry_run_output_schema(read) is None
    report = dry_run_output_schema(write)
    assert report is not None
    jsonschema.Draft202012Validator.check_schema(report)
    assert {"dry_run", "ran", "would_call"} <= set(report["required"])


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
