"""``view variants create`` is a registered, reviewed command with a closed input contract."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.command_contract import bind_command_inputs, resolve_command_contract

_ID = "view.variants.create"


def test_it_has_a_handler_and_a_reviewed_manifest_entry() -> None:
    record = command_by_id(_ID)

    assert _ID in HANDLERS
    assert record is not None
    assert record["command_path"] == "view variants create"
    assert record["mutation_class"] == "benign_mutation"
    assert record["agent_example"].startswith("mammoth view variants create 123 --input")


def test_the_document_requires_from_view_column_and_values() -> None:
    contract = resolve_command_contract(_ID)

    assert contract is not None
    assert {f.name for f in contract.fields if f.required} == {"from_view", "column", "values"}
    assert {f.name for f in contract.fields} == {"from_view", "column", "values", "name_template"}


def test_an_omitted_name_template_stays_omitted() -> None:
    bound = bind_command_inputs(_ID, {"from_view": 1, "column": "Region", "values": ["a"]})

    assert "name_template" not in bound


def test_an_input_field_outside_the_contract_is_refused_at_admission() -> None:
    document = {"from_view": 1, "column": "Region", "values": ["a"], "operator": "NE"}

    with pytest.raises(CliError) as refused:
        validate_input_fields(_ID, document)

    assert refused.value.code == "unknown_input_field"
    assert refused.value.exit_status == EXIT_USAGE
