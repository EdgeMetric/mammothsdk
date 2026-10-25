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
from collections import defaultdict
from functools import cache
from typing import Any, cast

from mammoth_cli.commands.schema.examples import _positionals, runnable_example
from mammoth_cli.manifest.loader import command_by_id, load_commands, load_operations
from mammoth_cli.output.normalize import trusted_json_schema
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.local_paths import local_path_fields
from mammoth_cli.services.command_contract import LOCAL_COMMANDS, resolve_command_contract
from mammoth_cli.services.field_enums import field_enum, with_enum
from mammoth_cli.services.input_fields import (
    excluded_input_fields,
)
from mammoth_cli.services.openapi_types import (
    openapi_body_schema_for,
    openapi_response_schema_for,
)
from mammoth_cli.services.positionals import LOCAL_PATH, resolve_positionals
from mammoth_cli.services.type_system import is_opaque_mapping, json_schema

_OPAQUE_EXPERT_COMMANDS = frozenset({"view.task.add", "view.task.preview", "view.task.update"})
_TYPED_TRANSFORM_ALTERNATIVES = [
    "view.transform.filter",
    "view.transform.join",
    "view.transform.math",
]


# A compact string scope is retained for existing discovery consumers.  These
# reviewed exceptions add the exact binding facts an agent needs for the
# sensitive operations repaired in this release; do not infer a project parent
# merely from a command-family name.
_SCOPE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "project.user.update": {
        "kind": "project",
        "required_context": ["project_id"],
        "target_fields": ["user_id", "invite_id"],
        "target_rule": "exactly one target field is required by the backend contract",
    },
    "view.exportable-config.apply": {
        "kind": "project",
        "required_context": ["project_id"],
        "target_fields": ["view_id", "dataset_id"],
        "target_rule": "view_id is required; dataset_id may be supplied or resolved from the view",
    },
}
# View transform/task commands add a step to the GIVEN view. An agent asked for
# a NEW dataset must know that before calling, so the statement is carried by
# every such command's contract (schema get ``preconditions``, find, --help).
_IN_PLACE_PREFIXES = ("view.transform.", "view.task.")
IN_PLACE_RECIPE = (
    "EDITS THE GIVEN VIEW IN PLACE: this adds a step to the view and changes that view "
    "and its dataset's output. To make a NEW dataset and leave the source untouched: "
    "`mammoth view create SOURCE_DATASET_ID` (working view), do the steps on that working "
    "view, then `mammoth view export dataset WORKING_VIEW_ID` "
    "(add dataset_name only if the user named it)."
)
_IN_PLACE_KEYWORDS = (
    "new dataset create make in place edits given view working view source untouched"
)


def edits_view_in_place(record: dict[str, Any]) -> bool:
    """True for a view transform/task command that changes an existing view."""
    return bool(record.get("edits_target")) and str(record.get("command_id", "")).startswith(
        _IN_PLACE_PREFIXES
    )


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
    contract = resolve_command_contract(str(record["command_id"]))
    if contract is None or contract.sdk_symbol is None:
        return None
    if contract.accepts_extra:
        return None
    excluded = _externally_supplied_fields(record["command_id"])
    body_schema = openapi_body_schema_for(
        tuple(str(item) for item in record.get("operation_ids", []))
    )
    path_fields = local_path_fields(record["command_id"], record.get("positionals", []))
    # A field an optional positional fills (``view summary VIEW_ID [DATASET_ID]``) is
    # resolved by the command when both are omitted, as the input schema says.
    fallbacks = {
        item.falls_back_to_field for item in contract.positionals if item.falls_back_to_field
    }
    return [
        {
            "name": field.name,
            "type": field.type_name,
            "required": field.required and field.name not in fallbacks,
            "enum": field.enum_values,
            "default": field.default_value if field.has_default else None,
            "schema": (
                body_schema
                if field.name == "body"
                and is_opaque_mapping(field.annotation)
                and body_schema is not None
                else json_schema(field.annotation, field.name)
            ),
            # Only where it applies: a host that cannot read the path refuses the command.
            **({"kind": LOCAL_PATH} if field.name in path_fields else {}),
        }
        for field in contract.accepted_fields
        if field.name not in excluded
    ]


_INLINE_SCHEMA_MAX_CHARS = 3000
#: A restrictions note (where a nested input shape often lives) is inlined up to this long.
_INLINE_NOTES_MAX_CHARS = 700


def _compact_accepted_fields(record: dict[str, Any]) -> list[dict[str, Any]] | None:
    """``_accepted_fields`` with a nested JSON Schema only where the type name is not enough.

    A find result inlines this for its top matches: enough to compose a call
    (name, type, required, enum) without a follow-up ``schema get``. A
    non-scalar field (e.g. convert-type's ``conversions``) also carries its
    JSON Schema, unless that would be larger than ``_INLINE_SCHEMA_MAX_CHARS``.
    """
    fields = _accepted_fields(record)
    if fields is None:
        return None
    compact: list[dict[str, Any]] = []
    for field in fields:
        item: dict[str, Any] = {
            key: field[key] for key in ("name", "type", "required", "enum", "kind") if key in field
        }
        schema = field.get("schema")
        if (
            schema is not None
            and not _is_scalar_field_schema(schema)
            and len(json.dumps(schema, default=str)) <= _INLINE_SCHEMA_MAX_CHARS
        ):
            item["schema"] = schema
        compact.append(item)
    return compact


def input_contract(command_id: str) -> dict[str, Any] | None:
    """The input shape a rejected call should have used: fields (with nested shapes) and an example.

    Attached to input-validation errors so the caller can correct the call
    without a ``schema get`` round trip. ``None`` for a command with no
    manifest record or no accepted fields.
    """
    record = command_by_id(command_id)
    if record is None:
        return None
    fields = _compact_accepted_fields(record)
    if fields is None:
        return None
    contract: dict[str, Any] = {"command_id": command_id, "accepted_fields": fields}
    if record.get("agent_example"):
        contract["agent_example"] = record["agent_example"]
    return contract


def _externally_supplied_fields(command_id: str) -> frozenset[str]:
    """Fields supplied by positionals or authenticated CLI context."""
    if command_id in LOCAL_COMMANDS:
        return frozenset(
            {
                item.name
                for item in resolve_positionals(command_id)
                if item.falls_back_to_field is None
            }
        )
    excluded = excluded_input_fields(command_id)
    if command_id == "activity.list":
        # ``excluded_input_fields`` treats "project_id" as the active-project
        # context on every command, but here it is an ActivityFiltersSchema
        # request-body filter (any workspace project, not the active one) --
        # the command's own contract already admits and forwards it (see
        # ``_S7_ADDITIONAL_INPUT_FIELDS["activity.list"]``). Only
        # "workspace_id" is the legacy-admitted, never-forwarded field here.
        excluded -= {"project_id"}
    return excluded


def command_scope(record: dict[str, Any]) -> str:
    """The one scope classifier; ``capability list`` and ``schema list`` both use it."""
    command_id = str(record["command_id"])
    family = str(record.get("command_path", "")).split()[0]
    operation_hints = _operation_hints_by_command().get(command_id, "")
    search_text = f"{command_id} {family} {operation_hints}".casefold()
    if family == "dashboard" and command_id.startswith("dashboard.tags."):
        scope = "workspace"
    elif (
        command_id == "ai.retention.condition"
        or "{project_id}" in search_text
        or family
        in {
            "project",
            "dataset",
            "file",
            "folder",
            "view",
            "batch",
            "annotation",
            "dashboard",
            "automation",
            "schedule",
            "snippet",
            "template",
            "workflow",
        }
    ):
        scope = "project"
    elif "{workspace_id}" in search_text or family in {
        "workspace",
        "user",
        "support",
        "billing",
        "connector",
        "client-app",
        "external-key",
    }:
        scope = "workspace"
    elif family in {
        "auth",
        "config",
        "context",
        "completion",
        "doctor",
        "schema",
        "capability",
        "skill",
        "version",
    }:
        scope = "local"
    else:
        scope = "profile"
    return scope


def _compact_contract(record: dict[str, Any]) -> dict[str, Any]:
    """Return the bounded, honest contract used by discovery clients.

    The manifest is authoritative for these values.  ``None`` is retained for
    fields the manifest does not prove; discovery must not turn a missing proof
    into a promise about backend behavior.
    """
    command_id = str(record["command_id"])
    resolved = resolve_command_contract(command_id)
    scope = command_scope(record)

    # Policy values exposed by discovery come from the same resolved contract
    # consumed by admission/binding.  The manifest fallback only applies to
    # genuinely local/bespoke commands without a resolvable SDK contract.
    mutation_class = resolved.effects if resolved is not None else record.get("mutation_class")
    result_model = resolved.result_contract if resolved is not None else record.get("result_model")
    wait_policy = resolved.wait_behavior if resolved is not None else record.get("wait_policy")
    if mutation_class in {None, "read"}:
        recovery = "Rerun only after checking the exit code and stable error code."
    else:
        recovery = (
            "Reconcile target/job state before retry; retain returned IDs and verify "
            "the intended postcondition."
        )
    restrictions = record.get("known_restrictions")
    if edits_view_in_place(record):
        restrictions = f"{IN_PLACE_RECIPE} {restrictions or ''}".strip()
    elif restrictions is None:
        required_positionals = [
            str(item.get("metavar") or item.get("name"))
            for item in record.get("positionals", [])
            if item.get("required")
        ]
        if required_positionals:
            restrictions = "Required inputs: " + ", ".join(required_positionals) + "."
    return {
        "scope": scope,
        "effects": mutation_class,
        "preconditions": restrictions,
        "result": result_model,
        "async": wait_policy,
        "verification": record.get("acceptance_evidence"),
        "recovery": recovery,
        "limits": {
            "pagination": record.get("pagination_policy"),
            "continuation": (
                "not_proven" if record.get("pagination_policy") not in {None, "none"} else None
            ),
        },
    }


def _scope_requirements(command_id: str, scope: str) -> dict[str, Any]:
    """Return detailed binding facts without expanding compact discovery."""
    return _SCOPE_REQUIREMENTS.get(
        command_id,
        {
            "kind": scope,
            "required_context": [],
            "target_fields": [],
            "target_rule": (
                "Inspect positionals and accepted_fields for operation-specific bindings."
            ),
        },
    )


# Public name for callers that want contract semantics without rebuilding a
# full request schema.  The underscore implementation keeps the helper's
# origin obvious next to the manifest-derived schema code.
compact_contract = _compact_contract


def _schema_common(record: dict[str, Any]) -> dict[str, Any]:
    """Shared enrichment fields for both the listing and single-command views."""
    symbol = record.get("sdk_symbol")
    accepted = _accepted_fields(record)
    if accepted is not None and record["command_id"] in {
        "view.exportable-config.get",
        "view.exportable-config.apply",
    }:
        # The SDK requires a parent dataset, but the CLI resolves it from the
        # view or accepts it as an optional trailing positional/input field.
        accepted = [
            {**field, "required": False} if field["name"] == "dataset_id" else field
            for field in accepted
        ]
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

            registered = field_enum(record["command_id"], field["name"])
            if registered is not None:
                field_schema = with_enum(field_schema, registered)
            if record["command_id"] == "parameter.create" and field["name"] == "name":
                field_schema = {**field_schema, "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"}
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
        if record["command_id"] == "batch.create-spec":
            input_schema["oneOf"] = [
                {
                    "required": ["source_id", "mapping"],
                    "not": {"required": ["file_id"]},
                },
                {
                    "required": ["file_id"],
                    "not": {"anyOf": [{"required": ["source_id"]}, {"required": ["mapping"]}]},
                },
            ]
        if record["command_id"] == "view.exportable-config.apply":
            # Release schema: exactly one of clipboard items or full config.
            # Nested task/action/etc objects intentionally remain open because
            # their release schemas are polymorphic and operation-specific.
            input_schema = {
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "integer", "minimum": 1},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "params": {"type": "object", "additionalProperties": True},
                                "transform_params": {
                                    "type": "object",
                                    "additionalProperties": True,
                                },
                            },
                            "additionalProperties": True,
                        },
                    },
                    "config": {
                        "type": "object",
                        "properties": {
                            "tasks": {"type": ["array", "null"], "items": {"type": "object"}},
                            "actions": {"type": ["array", "null"], "items": {"type": "object"}},
                            "checkpoints": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "data_checks": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "derivatives": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "display_properties": {"type": ["object", "null"]},
                            "metadata": {
                                "type": ["array", "null"],
                                "items": {"type": "object"},
                            },
                            "dependencies": {"type": ["object", "null"]},
                            "user_preferences": {"type": ["object", "null"]},
                            "name": {"type": ["string", "null"]},
                            "taskwise_info": {"type": ["object", "null"]},
                        },
                        "additionalProperties": True,
                    },
                    "insert_after_sequence": {"type": ["integer", "null"]},
                    "is_paste_mode": {"type": "boolean", "default": False},
                },
                "oneOf": [
                    {"required": ["items"], "not": {"required": ["config"]}},
                    {"required": ["config"], "not": {"required": ["items"]}},
                ],
                "additionalProperties": False,
            }
        if record["command_id"] == "dataset.batch-data":
            batch_properties = cast(dict[str, Any], input_schema["properties"])
            batch_properties["limit"].update({"minimum": 0, "maximum": 100})
            batch_properties["offset"].update({"minimum": 0})
            for field in accepted:
                if field["name"] == "limit":
                    field["schema"].update({"minimum": 0, "maximum": 100})
                elif field["name"] == "offset":
                    field["schema"].update({"minimum": 0})
        if definitions:
            input_schema["$defs"] = definitions
        # This mapping is produced locally from reviewed command contracts,
        # not returned by an API. Preserve JSON-Schema declaration names (for
        # example ``properties.api_secret``) through Result/render's second
        # normalization pass without trusting arbitrary result dictionary keys.
        input_schema = cast(dict[str, Any], trusted_json_schema(input_schema))
    contract = _compact_contract(record)
    opaque_fields = [
        str(field["name"])
        for field in accepted or []
        if str(field["name"]) in {"task_spec", "body"}
    ]
    contract_level = (
        "opaque_expert"
        if record["command_id"] in _OPAQUE_EXPERT_COMMANDS
        else "partially_typed" if opaque_fields else "typed"
    )
    return {
        "server_status": record.get("server_status", "served"),
        "positionals": _positionals(record["command_id"]),
        "accepted_fields": accepted,
        "input_schema": input_schema,
        "runnable_example": runnable_example(record, str(symbol) if symbol else None),
        # Keep the contract alongside the detailed schema so callers can stop
        # after one bounded request when they only need execution semantics.
        "contract": contract,
        "contract_level": contract_level,
        "unresolved_nested_fields": opaque_fields,
        "safe_typed_alternatives": (
            list(_TYPED_TRANSFORM_ALTERNATIVES)
            if record["command_id"] in _OPAQUE_EXPERT_COMMANDS
            else []
        ),
        # Top-level aliases keep the compact contract easy to consume while
        # ``contract`` gives clients one stable namespace for future fields.
        **contract,
    }


def _hidden_pending(record: dict[str, Any]) -> bool:
    """Whether an embedded call that opted out of pending commands must not see ``record``."""
    return embedded.hides_pending() and record.get("server_status") == "pending"


def schema_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in load_commands():
        if record.get("disposition") == "alias" or _hidden_pending(record):
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


#: ``schema get`` fields an agent needs to compose one call. The rest of the
#: record (JSON Schema, exit-code table, recovery boilerplate) is static or
#: duplicated and comes back only with ``full``.
_BRIEF_SCHEMA_KEYS = (
    "command_id",
    "command_path",
    "server_status",
    "positionals",
    "accepted_fields",
    "agent_example",
    "mutation_class",
    "confirmation",
    "wait_policy",
    "scope",
    "scope_requirements",
    "preconditions",
    "secret_fields",
    "safe_typed_alternatives",
)


def schema_index(family: str | None = None) -> dict[str, Any]:
    """Return the command index: families with counts, or one family's commands.

    The complete per-command records (``schema_entries``) run to megabytes;
    an agent choosing a command needs names and mutation classes, then one
    ``schema get`` for the command it picked.
    """
    entries = schema_entries()
    words = (family or "").strip().split(".")[0].split()
    if words:
        wanted = words[0]
        commands = [
            {
                "command_id": entry["command_id"],
                "command_path": entry["command_path"],
                "mutation_class": entry["mutation_class"],
                "confirmation": entry["confirmation"],
                "server_status": entry["server_status"],
            }
            for entry in entries
            if entry["command_path"].split()[0] == wanted
        ]
        return {"family": wanted, "total": len(commands), "commands": commands}
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["command_path"].split()[0]] = (
            counts.get(entry["command_path"].split()[0], 0) + 1
        )
    return {
        "total": len(entries),
        "families": [{"family": name, "commands": count} for name, count in sorted(counts.items())],
        "next": "mammoth schema list FAMILY, then mammoth schema get COMMAND_ID",
    }


def _is_scalar_field_schema(schema: Any) -> bool:
    """Whether a field's JSON Schema is a plain scalar with no nested shape.

    A caller composing ``--input`` for a scalar field just needs its type
    name. An object, an array of objects, or a union that includes an
    object (e.g. increment-date's ``delta``, convert-type's
    ``conversions``, a ``condition``) needs its nested shape too, or the
    bare type name (``DateDelta``) leaves it to guess.
    """
    if not isinstance(schema, dict):
        return True
    branches = schema.get("anyOf") or schema.get("oneOf")
    if branches:
        return all(_is_scalar_field_schema(branch) for branch in branches)
    schema_type = schema.get("type")
    if schema_type == "object":
        return False
    if schema_type == "array":
        return _is_scalar_field_schema(schema.get("items"))
    return True


def brief_schema(entry: dict[str, Any]) -> dict[str, Any]:
    """Reduce a full ``schema get`` record to what composing one call needs."""
    brief = {key: entry[key] for key in _BRIEF_SCHEMA_KEYS if key in entry}
    accepted = brief.get("accepted_fields")
    if isinstance(accepted, list):
        # Type and requirement are what a caller reads for a scalar; a
        # non-scalar field keeps its JSON Schema too, since a bare type name
        # does not say what shape it needs. ``full`` still has everything.
        brief["accepted_fields"] = [
            {
                key: value
                for key, value in field.items()
                if key != "schema" or not _is_scalar_field_schema(field.get("schema"))
            }
            for field in accepted
            if isinstance(field, dict)
        ]
    brief["full"] = f"mammoth schema get {entry['command_id']} --full"
    return brief


#: ``output_schema`` value of a command whose ``data`` is the API's own ``200`` body,
#: checked live against the API (``tests/live/test_output_schema.py``).
OUTPUT_SCHEMA_OPENAPI = "openapi"


def output_schema(record: dict[str, Any]) -> dict[str, Any] | None:
    """The JSON Schema (2020-12) of a command's envelope ``data``, when it declares one.

    Args:
        record: The command's manifest record.

    Returns:
        The schema with its ``$defs``, or None for a command that declares none (its
        result is reshaped by the CLI, or not yet checked against the API).
    """
    if record.get("output_schema") != OUTPUT_SCHEMA_OPENAPI:
        return None
    return openapi_response_schema_for(tuple(record.get("operation_ids") or ()))


def get_schema(command_id: str) -> dict[str, Any] | None:
    record = command_by_id(command_id)
    if record is None or record.get("disposition") == "alias":
        return None
    common = _schema_common(record)
    return {
        "command_id": record["command_id"],
        "command_path": record["command_path"],
        "request_model": record["request_model"],
        "result_model": record["result_model"],
        "options": record.get("options", []),
        **common,
        "scope_requirements": _scope_requirements(command_id, str(common["scope"])),
        # ``schema list`` already exposed these execution controls.  Keep the
        # detail endpoint self-sufficient so an agent does not need a second
        # inventory lookup before deciding whether it may dispatch.
        "mutation_class": record["mutation_class"],
        "confirmation": record["confirmation"],
        # Named so a caller knows which fields must arrive through a protected
        # ``--input FILE`` rather than an inline document or argv.
        "secret_fields": list(record.get("secret_fields") or ()),
        "wait_policy": record["wait_policy"],
        "pagination_policy": record["pagination_policy"],
        "human_example": record["human_example"],
        "agent_example": record["agent_example"],
        "output_schema": output_schema(record),
        "exit_codes": {
            "0": "success (a pending write exits 0 with status pending; see verify.next_command)",
            "1": "API or operation failure (including a write with verify.outcome failed)",
            "2": "usage, input, or confirmation failure",
            "3": "write partly applied (verify.outcome partial)",
            "4": "authentication or authorization failure",
            "5": "resource not found",
            "6": "conflict or failed precondition",
            "7": "retryable network, timeout, or rate-limit failure",
            "130": "interruption",
        },
    }
