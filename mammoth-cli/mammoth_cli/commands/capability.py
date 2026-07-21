"""Capability discovery generated from the reviewed manifests.

An agent uses these to discover which operations exist, their support state,
canonical command, SDK symbol, mutation class, and confirmation/wait/pagination
policies — without reading source.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.manifest.loader import command_by_id, load_operations


def capability_entries() -> list[dict[str, Any]]:
    """One capability record per OpenAPI operation."""
    entries: list[dict[str, Any]] = []
    for op in load_operations():
        command_id = op.get("canonical_command")
        command = command_by_id(command_id) if command_id else None
        entries.append(
            {
                "operation_id": op["operation_id"],
                "identity": op["identity"],
                "disposition": op["disposition"],
                "canonical_command": command_id,
                "command_path": command["command_path"] if command else None,
                "sdk_symbol": op.get("sdk_symbol"),
                "mutation_class": command["mutation_class"] if command else None,
                "confirmation": command["confirmation"] if command else None,
                "wait_policy": command["wait_policy"] if command else None,
                "pagination_policy": command["pagination_policy"] if command else None,
                "acceptance_evidence": command["acceptance_evidence"] if command else None,
            }
        )
    return sorted(entries, key=lambda entry: entry["operation_id"])


def get_capability(operation_id: str) -> dict[str, Any] | None:
    for entry in capability_entries():
        if entry["operation_id"] == operation_id:
            return entry
    return None
