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
import shlex
from collections import defaultdict
from functools import cache
from typing import Any

from mammoth_cli.manifest.loader import command_by_id, load_commands, load_operations
from mammoth_cli.services.argspec import FieldSpec, arg_spec
from mammoth_cli.services.input_fields import (
    example_input_hints,
    excluded_input_fields,
    handler_owned_fields,
)
from mammoth_cli.services.openapi_types import openapi_body_schema_for, sample_from_schema
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals
from mammoth_cli.services.type_system import is_opaque_mapping, json_schema, sample_value

_OUTPUT_JSON_NO_INPUT = ("--output", "json", "--no-input")

# Human intent often uses the resource's familiar format or outcome rather
# than a literal command token.  These small, stable hints supplement (never
# replace) manifest and OpenAPI text during compact discovery.
_GROUP_DISCOVERY_PURPOSES = {
    "dataset": "data import tables CSV spreadsheet",
    "file": "source file storage",
    "view": "transform query clean analyze data pipeline",
    "dashboard": "build visualize share charts analytics",
    "workflow": "automate pipeline orchestration",
}

_COMMAND_DISCOVERY_PURPOSES = {
    "file.upload": "upload import CSV spreadsheet XLSX source data",
    "file.upload-folder": "upload source-data directory folder",
}

_MAX_FIND_RESULTS = 20


@cache
def _operation_hints_by_command() -> dict[str, str]:
    """Return searchable OpenAPI summaries and tags keyed by command id."""
    hints: defaultdict[str, list[str]] = defaultdict(list)
    for operation in load_operations():
        command_id = operation.get("canonical_command")
        if not command_id:
            continue
        hints[str(command_id)].extend(
            [str(operation.get("summary", "")), *map(str, operation.get("tags", []))]
        )
    return {command_id: " ".join(parts) for command_id, parts in hints.items()}


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
    excluded = _externally_supplied_fields(record["command_id"])
    body_schema = openapi_body_schema_for(
        tuple(str(item) for item in record.get("operation_ids", []))
    )
    return [
        {
            "name": field.name,
            "type": field.type_name,
            "required": field.required,
            "enum": field.enum_values,
            "default": field.default_value if field.has_default else None,
            "schema": (
                body_schema
                if field.name == "body"
                and is_opaque_mapping(field.annotation)
                and body_schema is not None
                else json_schema(field.annotation, field.name)
            ),
        }
        for field in spec.fields
        if field.name not in excluded
    ]


def _externally_supplied_fields(command_id: str) -> frozenset[str]:
    """Fields supplied by positionals or authenticated CLI context."""
    return excluded_input_fields(command_id)


def _positionals(command_id: str) -> list[dict[str, Any]]:
    """Return a command's positional arguments in the schema JSON shape."""
    return [spec.as_manifest() for spec in resolve_positionals(command_id)]


def _sample_positional_value(spec: PositionalSpec) -> Any:
    """A representative value for one positional, for the runnable example.

    Prefers the spec's ``example_value`` when set (a concrete, resolvable id for
    the discovery commands whose example is executed offline), falling back to a
    generic ``123``/``example`` placeholder that is never validated at build time.
    """
    if spec.example_value is not None:
        return spec.example_value
    return 123 if spec.type is int else _representative_string(spec.name)


def _sample_field_value(field: FieldSpec) -> Any:
    """A representative JSON value for one accepted field's type."""
    return _humanize_sample(sample_value(field.annotation), field.name)


def _representative_string(field_name: str) -> str:
    """Return a realistic, non-secret sample for a named string field."""
    name = field_name.casefold().replace("-", "_")
    if any(part in name for part in ("password", "secret", "token", "credential")):
        return "replace-with-secret"
    if "email" in name:
        return "analyst@example.com"
    if any(part in name for part in ("url", "uri", "webhook")):
        return "https://example.com/data.csv"
    if any(part in name for part in ("file", "path")):
        return "./sales.csv"
    if any(part in name for part in ("expression", "formula")):
        return "price * quantity"
    if any(part in name for part in ("query", "sql")):
        return "SELECT region, SUM(revenue) FROM data GROUP BY region"
    if any(part in name for part in ("prompt", "intent", "question", "message")):
        return "Summarize revenue by region"
    if any(part in name for part in ("new_column", "as_name", "name", "title", "label")):
        return "Revenue report"
    if "column" in name or name in {"source", "key"}:
        return "Status"
    if name.endswith("_id") or name in {"id", "identifier"}:
        return "resource-123"
    return "sample"


def _humanize_sample(value: Any, field_name: str) -> Any:
    """Replace generator placeholders with domain-shaped representative data."""
    if value == "example":
        return _representative_string(field_name)
    if isinstance(value, list):
        singular = field_name[:-1] if field_name.endswith("s") else field_name
        return [_humanize_sample(item, singular) for item in value]
    if isinstance(value, dict):
        return {
            ("sample_key" if key == "example" else key): _humanize_sample(
                item, "key" if key == "example" else key
            )
            for key, item in value.items()
        }
    return value


def runnable_example(
    record: dict[str, Any],
    symbol: str | None,
    positionals: tuple[PositionalSpec, ...] | None = None,
) -> str | None:
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
    if positionals is None:
        positionals = resolve_positionals(record["command_id"])
    tokens: list[str] = ["mammoth", *record["command_path"].split()]
    tokens.extend(str(_sample_positional_value(p)) for p in positionals)
    excluded = frozenset(
        {"project_id", "workspace_id"}
        | {item.name for item in positionals}
        # A positional may fill a differently-named SDK parameter (e.g. the
        # ``folder_id`` positional fills ``folder_ids``). That parameter is
        # positional-sourced, so it must be excluded from the generated
        # ``--input`` example too -- mirroring ``excluded_input_fields`` so the
        # example never advertises a field the validator rejects.
        | {item.fills_sdk_param for item in positionals if item.fills_sdk_param}
    ) | handler_owned_fields(record["command_id"])
    required = [field for field in spec.fields if field.required and field.name not in excluded]
    hints = example_input_hints(record["command_id"])
    if required or hints:
        body_schema = openapi_body_schema_for(
            tuple(str(item) for item in record.get("operation_ids", []))
        )
        document = {
            field.name: (
                _humanize_sample(sample_from_schema(body_schema), field.name)
                if field.name == "body"
                and is_opaque_mapping(field.annotation)
                and body_schema is not None
                else _sample_field_value(field)
            )
            for field in required
        }
        # A command with a runtime "one of" / identifier requirement the signature
        # cannot express supplies the missing accepted field here, so the
        # documented example is actually runnable rather than just well-formed.
        document.update(hints)
        tokens.extend(["--input", json.dumps(document)])
    tokens.extend(_OUTPUT_JSON_NO_INPUT)
    return shlex.join(tokens)


def _schema_common(record: dict[str, Any]) -> dict[str, Any]:
    """Shared enrichment fields for both the listing and single-command views."""
    symbol = record.get("sdk_symbol")
    accepted = _accepted_fields(record)
    input_schema = None
    if accepted is not None:
        definitions: dict[str, Any] = {}
        properties: dict[str, Any] = {}
        for field in accepted:
            field_schema = dict(field["schema"])
            prefix = f"{field['name']}__"

            def namespace_refs(value: Any, namespace: str = prefix) -> Any:
                if isinstance(value, dict):
                    return {
                        key: (
                            item.replace("#/$defs/", f"#/$defs/{namespace}")
                            if key == "$ref" and isinstance(item, str)
                            else namespace_refs(item)
                        )
                        for key, item in value.items()
                    }
                if isinstance(value, list):
                    return [namespace_refs(item) for item in value]
                return value

            def hoist_definitions(value: Any, namespace: str = prefix) -> Any:
                if isinstance(value, dict):
                    result = dict(value)
                    nested = result.pop("$defs", {})
                    for name, definition in nested.items():
                        definitions[f"{namespace}{name}"] = hoist_definitions(definition)
                    return {key: hoist_definitions(item) for key, item in result.items()}
                if isinstance(value, list):
                    return [hoist_definitions(item) for item in value]
                return value

            properties[field["name"]] = hoist_definitions(namespace_refs(field_schema))
        # A field a positional falls back to (the dual-sourced "positional OR
        # --input field" pattern) is satisfiable from the command line, so it is
        # NOT required *in the --input document*: the runnable example supplies
        # it positionally and omits it from --input, so requiring it here would
        # make the generated example fail its own input schema. It stays an
        # accepted (optional) field so passing it via --input still works.
        fallback_fields = {
            spec.falls_back_to_field
            for spec in resolve_positionals(record["command_id"])
            if spec.falls_back_to_field
        }
        input_schema = {
            "type": "object",
            "properties": properties,
            "required": [
                field["name"]
                for field in accepted
                if field["required"] and field["name"] not in fallback_fields
            ],
            "additionalProperties": False,
        }
        if definitions:
            input_schema["$defs"] = definitions
    return {
        "positionals": _positionals(record["command_id"]),
        "accepted_fields": accepted,
        "input_schema": input_schema,
        "runnable_example": runnable_example(record, str(symbol) if symbol else None),
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


def find_schemas(query: str) -> dict[str, Any]:
    """Return compact command matches for interactive and agent discovery.

    ``schema list`` deliberately remains the complete, machine-readable
    inventory.  This search avoids returning a large nested schema for every
    command when callers only need to locate the right command id first; use
    the included ``full_schema_command`` to fetch the authoritative detail.
    Every whitespace-separated term must occur in a command name, its examples,
    or its stable operation-purpose text, making the result deterministic and
    easy to compose in scripts.
    """
    terms = tuple(term for term in query.casefold().split() if term)
    ranked_matches: list[tuple[int, dict[str, Any]]] = []
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        command_id = str(record["command_id"])
        command_path = str(record["command_path"])
        positional_help = " ".join(
            str(positional.get("help", "")) for positional in record.get("positionals", [])
        )
        primary_text = f"{command_id} {command_path}".casefold()
        sources = (
            (30, f"{record.get('human_example', '')} {record.get('agent_example', '')}"),
            (20, positional_help),
            (15, _operation_hints_by_command().get(command_id, "")),
            (60, _COMMAND_DISCOVERY_PURPOSES.get(command_id, "")),
            (3, _GROUP_DISCOVERY_PURPOSES.get(command_path.split()[0], "")),
        )
        score = 0
        for term in terms:
            if term in primary_text:
                score += 100
                continue
            source_score = max(
                (weight for weight, source in sources if term in source.casefold()), default=0
            )
            if source_score == 0:
                break
            score += source_score
        else:
            ranked_matches.append(
                (
                    score,
                    {
                        "command_id": command_id,
                        "command_path": command_path,
                        "mutation_class": record["mutation_class"],
                        "confirmation": record["confirmation"],
                        "full_schema_command": (
                            f"mammoth schema get {command_id} --output json --no-input"
                        ),
                    },
                )
            )
    ranked_matches.sort(key=lambda item: (-item[0], item[1]["command_id"]))
    total_matches = len(ranked_matches)
    return {
        "query": query,
        "matches": [match for _, match in ranked_matches[:_MAX_FIND_RESULTS]],
        "total_matches": total_matches,
        "truncated": total_matches > _MAX_FIND_RESULTS,
    }


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
