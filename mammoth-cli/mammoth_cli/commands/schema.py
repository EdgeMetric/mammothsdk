"""Schema discovery generated from the reviewed command manifests.

Returns each command's request/result models, examples, policies, and test ids
so an agent can construct a valid invocation without reading source. The
accepted request fields (name, type, enum values, default, required) and the
positional arguments (name, type, required, metavar) are derived from the
command's backing SDK signature (see :mod:`mammoth_cli.services.argspec` and
:mod:`mammoth_cli.services.positionals`), so discovery reports the real,
always-current shape rather than the manifest's placeholder empty lists. A
synthesized, fully runnable example command line is included for every command
with a resolvable signature, so an agent never has to guess how a positional
and an ``--input`` document combine.
"""

from __future__ import annotations

import json
import typing
from typing import Any

from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.services.argspec import FieldSpec, arg_spec
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals

_OUTPUT_JSON_NO_INPUT = ("--output", "json", "--no-input")


def _accepted_fields(record: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Return the backing method's accepted fields for a command record.

    Args:
        record: A reviewed command manifest record.

    Returns:
        A list of ``{"name", "type", "required", "enum", "default"}`` field
        descriptors in signature order, or None when the command has no
        resolvable backing signature (bespoke commands) or accepts arbitrary
        keyword arguments.
    """
    symbol = record.get("sdk_symbol")
    if not symbol:
        return None
    spec = arg_spec(str(symbol))
    if spec is None or spec.accepts_extra:
        return None
    return [
        {
            "name": field.name,
            "type": field.type_name,
            "required": field.required,
            "enum": field.enum_values,
            "default": field.default_value if field.has_default else None,
        }
        for field in spec.fields
    ]


def _positionals(command_id: str) -> list[dict[str, Any]]:
    """Return a command's positional arguments in the schema JSON shape."""
    return [spec.as_manifest() for spec in resolve_positionals(command_id)]


def _sample_positional_value(spec: PositionalSpec) -> Any:
    """A representative value for one positional, for the runnable example."""
    return 123 if spec.type is int else "example"


def _sample_field_value(field: FieldSpec) -> Any:
    """A representative JSON value for one accepted field's type."""
    enum_values = field.enum_values
    if enum_values:
        return enum_values[0]
    target = field.resolved_type
    if target is bool:
        return True
    if target is int:
        return 1
    if target is float:
        return 1.0
    if target is str:
        return "example"
    origin = typing.get_origin(target) if target is not None else None
    if origin in (list, typing.List):  # noqa: UP006 - runtime origin comparison
        args = typing.get_args(target)
        inner = args[0] if args else None
        if inner is str:
            return ["example"]
        return []
    if origin in (dict, typing.Dict):  # noqa: UP006 - runtime origin comparison
        return {}
    return None


def _runnable_example(record: dict[str, Any], symbol: str | None) -> str | None:
    """Build one complete, copy-pasteable command line for this command.

    Args:
        record: A reviewed command manifest record.
        symbol: The command's ``sdk_symbol``, or None.

    Returns:
        A ``mammoth ...`` command line covering every required positional and
        required ``--input`` field, plus ``--output json --no-input``; or None
        when the command has no resolvable backing signature.
    """
    if not symbol:
        return None
    spec = arg_spec(symbol)
    if spec is None:
        return None
    positionals = resolve_positionals(record["command_id"])
    tokens: list[str] = ["mammoth", *record["command_path"].split()]
    tokens.extend(str(_sample_positional_value(p)) for p in positionals)
    required = [field for field in spec.fields if field.required]
    if required:
        document = {field.name: _sample_field_value(field) for field in required}
        tokens.extend(["--input", json.dumps(document)])
    tokens.extend(_OUTPUT_JSON_NO_INPUT)
    return " ".join(tokens)


def _schema_common(record: dict[str, Any]) -> dict[str, Any]:
    """Shared enrichment fields for both the listing and single-command views."""
    symbol = record.get("sdk_symbol")
    return {
        "positionals": _positionals(record["command_id"]),
        "accepted_fields": _accepted_fields(record),
        "runnable_example": _runnable_example(record, str(symbol) if symbol else None),
    }


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
                "options": record.get("options", []),
                **_schema_common(record),
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
        "options": record.get("options", []),
        **_schema_common(record),
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
