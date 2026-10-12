"""`capability list` and `schema list` must report the same scope per command."""

from __future__ import annotations

from mammoth_cli.commands.capability import capability_entries
from mammoth_cli.commands.schema import schema_entries


def test_capability_scope_equals_schema_scope_for_every_command() -> None:
    schema_scope = {entry["command_id"]: entry["scope"] for entry in schema_entries()}
    checked = 0
    disagreements: dict[str, tuple[str, str]] = {}
    for entry in capability_entries():
        command_id = entry["canonical_command"]
        if command_id not in schema_scope:
            continue
        checked += 1
        if entry["scope"] != schema_scope[command_id]:
            disagreements[command_id] = (entry["scope"], schema_scope[command_id])
    assert checked > 100
    assert not disagreements, f"(capability, schema) scope differs: {disagreements}"
