"""Schema discovery generated from the reviewed command manifests.

Returns each command's request/result models, examples, policies, and test ids
so an agent can construct a valid invocation without reading source. The
accepted request fields are derived from the command's backing SDK signature
(see :mod:`mammoth_cli.services.argspec`) so discovery reports the real,
always-current field set rather than an empty list.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.services.argspec import arg_spec


def _accepted_fields(record: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Return the backing method's accepted fields for a command record.

    Args:
        record: A reviewed command manifest record.

    Returns:
        A list of ``{"name", "required"}`` field descriptors in signature
        order, or None when the command has no resolvable backing signature
        (bespoke commands) or accepts arbitrary keyword arguments.
    """
    symbol = record.get("sdk_symbol")
    if not symbol:
        return None
    spec = arg_spec(str(symbol))
    if spec is None or spec.accepts_extra:
        return None
    return [{"name": field.name, "required": field.required} for field in spec.fields]


def schema_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        entries.append(
            {
                "command_id": record["command_id"],
                "command_path": record["command_path"],
                "request_model": record["request_model"],
                "result_model": record["result_model"],
                "positionals": record.get("positionals", []),
                "options": record.get("options", []),
                "accepted_fields": _accepted_fields(record),
                "mutation_class": record["mutation_class"],
                "confirmation": record["confirmation"],
                "wait_policy": record["wait_policy"],
                "pagination_policy": record["pagination_policy"],
                "human_example": record["human_example"],
                "agent_example": record["agent_example"],
            }
        )
    return sorted(entries, key=lambda entry: entry["command_id"])


def get_schema(command_id: str) -> dict[str, Any] | None:
    record = command_by_id(command_id)
    if record is None or record.get("disposition") == "alias":
        return None
    return {
        "command_id": record["command_id"],
        "command_path": record["command_path"],
        "request_model": record["request_model"],
        "result_model": record["result_model"],
        "positionals": record.get("positionals", []),
        "options": record.get("options", []),
        "accepted_fields": _accepted_fields(record),
        "human_example": record["human_example"],
        "agent_example": record["agent_example"],
        "exit_codes": {
            "0": "success",
            "1": "API or operation failure",
            "2": "usage, input, or confirmation failure",
            "4": "authentication or authorization failure",
            "5": "resource not found",
            "6": "conflict or failed precondition",
            "7": "retryable network, timeout, or rate-limit failure",
            "130": "interruption",
        },
    }
