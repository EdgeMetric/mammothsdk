"""``dashboard filter add|list|remove`` are registered, reviewed commands."""

from __future__ import annotations

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.command_contract import resolve_command_contract

_IDS = ("dashboard.filter.add", "dashboard.filter.list", "dashboard.filter.remove")


def test_each_filter_command_has_a_handler_and_a_reviewed_manifest_entry() -> None:
    for command_id in _IDS:
        assert command_id in HANDLERS
        record = command_by_id(command_id)
        assert record is not None
        assert record["command_path"] == command_id.replace(".", " ")


def test_add_and_remove_take_the_field_and_list_takes_nothing() -> None:
    add = resolve_command_contract("dashboard.filter.add")
    remove = resolve_command_contract("dashboard.filter.remove")
    listing = resolve_command_contract("dashboard.filter.list")

    assert add is not None and remove is not None and listing is not None
    assert [f.name for f in add.fields if f.required] == ["field"]
    assert {f.name for f in add.fields} >= {"field", "control", "label", "default"}
    assert [f.name for f in remove.fields if f.required] == ["field"]
    assert not listing.fields


def test_add_and_remove_are_reversible_writes_that_read_the_canvas_back() -> None:
    for command_id in ("dashboard.filter.add", "dashboard.filter.remove"):
        record = command_by_id(command_id)
        assert record is not None
        assert record["mutation_class"] == "benign_mutation"
        assert record["readback"]["command"] == "dashboard.canvas.get"
