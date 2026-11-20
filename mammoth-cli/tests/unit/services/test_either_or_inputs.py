"""Fields another input stands in for are listed as optional, so help and the
input contract never ask for both (``automation update`` told callers ``patch*``
beside ``add_datasets``, which the handler then refuses)."""

from __future__ import annotations

import pytest

from mammoth_cli.services.command_contract import resolve_command_contract


@pytest.mark.parametrize(
    ("command_id", "replaced", "alternative"),
    [
        ("automation.update", "patch", "add_datasets"),
        ("view.export.update", "patches", "save_as_mode"),
    ],
)
def test_a_replaced_field_is_optional(command_id: str, replaced: str, alternative: str) -> None:
    contract = resolve_command_contract(command_id)
    assert contract is not None
    fields = {field.name: field for field in contract.fields}
    assert alternative in fields
    assert fields[replaced].required is False


def test_folder_create_takes_the_parent_as_folder_list_shows_it() -> None:
    contract = resolve_command_contract("folder.create")
    assert contract is not None
    names = {field.name for field in contract.fields}
    assert "parent_resource_id" in names
    assert "parent_folder_id" not in names
