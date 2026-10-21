"""Find results and input-validation errors carry the command's input shape (PRD-3119)."""

from __future__ import annotations

from mammoth_cli.commands.schema import _compact_accepted_fields, input_contract
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.executor import _attach_input_contract


def test_find_fields_inline_the_nested_shape_of_conversions() -> None:
    record = command_by_id("view.transform.convert-type")
    assert record is not None
    fields = {f["name"]: f for f in _compact_accepted_fields(record) or []}
    nested = str(fields["conversions"]["schema"])
    assert "input_formats" in nested and "output_format" in nested
    assert "input_format_preference" in nested


def test_find_fields_keep_scalars_schema_free() -> None:
    record = command_by_id("view.transform.convert-type")
    assert record is not None
    fields = {f["name"]: f for f in _compact_accepted_fields(record) or []}
    assert [name for name, f in fields.items() if "schema" in f] == ["conversions"]


def test_input_contract_names_fields_and_example() -> None:
    contract = input_contract("view.column.format.set")
    assert contract is not None
    assert "formats" in {f["name"] for f in contract["accepted_fields"]}
    assert contract["agent_example"]


def test_input_contract_is_none_for_an_unknown_command() -> None:
    assert input_contract("no.such.command") is None


def test_validation_error_gets_the_contract() -> None:
    error = CliError(code="unknown_input_field", message="nope", exit_status=2)
    _attach_input_contract(error, "view.transform.convert-type")
    assert "conversions" in str(error.details["input_contract"])


def test_other_errors_are_left_alone() -> None:
    error = CliError(code="api_error", message="boom")
    _attach_input_contract(error, "view.transform.convert-type")
    assert "input_contract" not in error.details
