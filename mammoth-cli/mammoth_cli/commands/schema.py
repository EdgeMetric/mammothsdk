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
import re
import shlex
from collections import defaultdict
from functools import cache
from typing import Any, cast

from mammoth_cli.manifest.loader import command_by_id, load_commands, load_operations
from mammoth_cli.output.normalize import trusted_json_schema
from mammoth_cli.services.argspec import FieldSpec
from mammoth_cli.services.command_contract import LOCAL_COMMANDS, resolve_command_contract
from mammoth_cli.services.input_fields import (
    example_input_hints,
    excluded_input_fields,
    handler_owned_fields,
)
from mammoth_cli.services.openapi_types import openapi_body_schema_for, sample_from_schema
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals
from mammoth_cli.services.type_system import is_opaque_mapping, json_schema, sample_value

_OUTPUT_JSON_NO_INPUT = ("--output", "json", "--no-input")
# A command whose request carries a secret never gets an inline JSON example:
# the published example points at a protected owner-only file instead, so no
# generated or copied command line ever puts a credential in argv.
_PROTECTED_INPUT_PATH = "/private/path/request.json"
_OPAQUE_EXPERT_COMMANDS = frozenset({"view.task.add", "view.task.preview", "view.task.update"})
_TYPED_TRANSFORM_ALTERNATIVES = [
    "view.transform.filter",
    "view.transform.join",
    "view.transform.math",
]

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
    "view.export.csv": "export download local CSV file artifact",
    "view.transform.discard-duplicates": (
        "duplicate duplicates dedup deduplicate remove repeated rows"
    ),
    "view.transform.convert-type": "convert type cast numeric text date column",
    "view.transform.fill-missing": "fill missing null empty impute carry forward values",
    "view.transform.join": "join blend lookup merge matching keys rows",
}

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
    "data-app.share": {
        "kind": "workspace",
        "required_context": ["workspace_id"],
        "target_fields": ["data_app_id"],
        "target_rule": "data_app_id is a required positional",
    },
    "view.exportable-config.apply": {
        "kind": "project",
        "required_context": ["project_id"],
        "target_fields": ["view_id", "dataset_id"],
        "target_rule": "view_id is required; dataset_id may be supplied or resolved from the view",
    },
}

_MAX_FIND_RESULTS = 20
_MAX_FIND_LIMIT = 100

# Search is intentionally a small, deterministic intent matcher rather than a
# fuzzy/remote search service.  The aliases describe language users commonly
# use for a command; they do not add capabilities to the catalog.  Keeping the
# map here also makes a cold process produce the same ordering as a warm one.
_DISCOVERY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "show": ("list", "get", "browse", "display", "view"),
    "display": ("show", "list", "get", "view"),
    "visualize": ("dashboard", "chart", "analytics"),
    "spreadsheet": ("csv", "xlsx", "excel", "file", "upload"),
    "excel": ("spreadsheet", "xlsx", "file"),
    "csv": ("spreadsheet", "file", "upload"),
    "local": ("file", "download", "csv", "artifact"),
    "download": ("export", "file", "csv", "artifact", "local"),
    "column": ("columns", "field", "fields", "schema"),
    "columns": ("column", "field", "fields", "schema"),
    "display-name": ("name", "column", "columns", "field", "fields", "schema"),
    "language": ("name", "column", "columns", "field", "fields", "schema", "text"),
    "field": ("column", "columns", "fields"),
    "fields": ("column", "columns", "field"),
    "clean": ("transform", "replace", "remove", "edit"),
    "edit": ("transform", "update", "replace", "change"),
    "remove": ("delete", "trash", "bulk-delete"),
    "import": ("upload", "create", "file"),
    "ingest": ("upload", "import", "file"),
    "asynchronous": ("async", "job", "wait"),
    "async": ("job", "wait", "poll"),
    "poll": ("job", "wait", "status"),
}
_DISCOVERY_STOPWORDS = frozenset(
    {"a", "an", "the", "me", "please", "for", "to", "of", "by", "with", "can", "i"}
)
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


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
        for field in contract.accepted_fields
        if field.name not in excluded
    ]


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


def _tokens(value: str) -> frozenset[str]:
    """Tokenize search text consistently across platforms and Python runs."""
    return frozenset(_TOKEN_RE.findall(value.casefold()))


def _query_tokens(query: str) -> tuple[str, ...]:
    return tuple(token for token in _tokens(query) if token not in _DISCOVERY_STOPWORDS)


def _token_aliases(token: str) -> frozenset[str]:
    """Return the finite synonym neighborhood for one intent token."""
    return frozenset((token, *_DISCOVERY_SYNONYMS.get(token, ())))


def _compact_contract(record: dict[str, Any]) -> dict[str, Any]:
    """Return the bounded, honest contract used by discovery clients.

    The manifest is authoritative for these values.  ``None`` is retained for
    fields the manifest does not prove; discovery must not turn a missing proof
    into a promise about backend behavior.
    """
    command_id = str(record["command_id"])
    resolved = resolve_command_contract(command_id)
    family = str(record.get("command_path", "")).split()[0]
    operation_hints = _operation_hints_by_command().get(command_id, "")
    search_text = f"{command_id} {family} {operation_hints}".casefold()
    if family == "dashboard" and command_id.startswith("dashboard.tags."):
        scope = "workspace"
    elif command_id == "ai.retention.condition" or "{project_id}" in search_text or family in {
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
    }:
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
    if restrictions is None:
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
            "continuation": "not_proven"
            if record.get("pagination_policy") not in {None, "none"}
            else None,
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
    # Credential documents must never be synthesized into a JSON command
    # example.  The local auth adapter validates a protected file reference;
    # the manifest carries the safe ``creds.json`` invocation instead.
    if record["command_id"] == "auth.login":
        return None
    if record["command_id"] == "ai.retention.condition":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                "--input",
                json.dumps({"mode": "generate", "intent": "completed payments older than 90 days"}),
                *_OUTPUT_JSON_NO_INPUT,
                "--project", "456",
            ]
        )
    if record["command_id"] == "dashboard.import-workbook":
        # This high-impact multipart command needs explicit scope and target
        # confirmation in its unattended example. The numeric project is
        # syntactically runnable; the sample workbook remains nonexistent.
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "sample.twbx",
                "--project",
                "456",
                "--yes",
                "--confirm",
                "456",
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    # The backend's generic task_spec envelope is intentionally opaque in the
    # SDK signature. Keep the generated example structurally valid, while
    # agent-facing docs direct users to typed view.transform.* commands.
    task_examples = {
        "view.task.add": ["mammoth", "view", "task", "add", "123"],
        "view.task.preview": ["mammoth", "view", "task", "preview", "123"],
        "view.task.update": ["mammoth", "view", "task", "update", "123", "123"],
    }
    if record["command_id"] in task_examples:
        task_input: dict[str, Any] = {
            "task_spec": {"DATAVIEW_ID": 123, "SEQUENCE_NUMBER": 1, "COPY": {}}
        }
        if record["command_id"] == "view.task.update":
            task_input["dataset_id"] = 456
        return shlex.join(
            [
                *task_examples[record["command_id"]],
                "--input",
                json.dumps(task_input),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "batch.create-spec":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                "--input", json.dumps({"file_id": 94}), *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "view.exportable-config.get":
        return shlex.join(
            ["mammoth", *record["command_path"].split(), "123", *_OUTPUT_JSON_NO_INPUT]
        )
    if record["command_id"] == "view.exportable-config.apply":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input-format",
                "json",
                "--input",
                json.dumps({"config": {"tasks": []}}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.rename":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                "--input", json.dumps({"name": "Revenue"}),
                *_OUTPUT_JSON_NO_INPUT, "--yes", "--confirm", "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.set":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                "--input", json.dumps({"tags": ["Revenue"]}),
                *_OUTPUT_JSON_NO_INPUT, "--yes", "--confirm", "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.delete":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                *_OUTPUT_JSON_NO_INPUT, "--yes", "--confirm", "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.merge":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                "--input", json.dumps({"target_id": 456}),
                *_OUTPUT_JSON_NO_INPUT, "--yes", "--confirm", "123",
            ]
        )
    if record["command_id"] == "dashboard.archive":
        return shlex.join(
            [
                "mammoth", *record["command_path"].split(), "123",
                "--input", json.dumps({"archived": True}),
                *_OUTPUT_JSON_NO_INPUT, "--yes", "--confirm", "123",
            ]
        )
    contract = resolve_command_contract(str(record["command_id"]))
    if contract is None or contract.sdk_symbol is None or contract.accepts_extra:
        return None
    fields = contract.accepted_fields
    if positionals is None:
        positionals = resolve_positionals(record["command_id"])
    tokens: list[str] = ["mammoth", *record["command_path"].split()]
    tokens.extend(str(_sample_positional_value(p)) for p in positionals)
    excluded = frozenset(
        (set() if record["command_id"] in LOCAL_COMMANDS else {"project_id", "workspace_id"})
        | {item.name for item in positionals}
        # A positional may fill a differently-named SDK parameter (e.g. the
        # ``folder_id`` positional fills ``folder_ids``). That parameter is
        # positional-sourced, so it must be excluded from the generated
        # ``--input`` example too -- mirroring ``excluded_input_fields`` so the
        # example never advertises a field the validator rejects.
        | {item.fills_sdk_param for item in positionals if item.fills_sdk_param}
    ) | handler_owned_fields(record["command_id"])
    required = [field for field in fields if field.required and field.name not in excluded]
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
        if set(record.get("secret_fields") or ()).intersection(document):
            tokens.extend(["--input", _PROTECTED_INPUT_PATH])
        else:
            tokens.extend(["--input", json.dumps(document)])
    tokens.extend(_OUTPUT_JSON_NO_INPUT)
    if record["command_id"] in {"project.user.update", "data-app.share"}:
        # These published high-impact examples must satisfy the same policy
        # their manifests advertise; otherwise discovery emits a command that
        # deterministically fails before dispatch.
        tokens.append("--yes")
    if record["command_id"] == "project.resource-dependencies.update":
        # This command has a confirm_target policy.  Keep its generated
        # example executable in non-interactive mode instead of advertising a
        # request that the safety guard will reject.
        tokens.extend(["--yes", "--confirm", str(_sample_positional_value(positionals[0]))])
    elif record["command_id"] == "dashboard.create-blank":
        tokens.append("--yes")
    return shlex.join(tokens)


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
        else "partially_typed"
        if opaque_fields
        else "typed"
    )
    return {
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


def find_schemas(
    query: str,
    *,
    limit: int = _MAX_FIND_RESULTS,
    cursor: int = 0,
) -> dict[str, Any]:
    """Return compact command matches for interactive and agent discovery.

    ``schema list`` deliberately remains the complete, machine-readable
    inventory.  This search avoids returning a large nested schema for every
    command when callers only need to locate the right command id first; use
    the included ``full_schema_command`` to fetch the authoritative detail.
    Every whitespace-separated term must occur in a command name, its examples,
    or its stable operation-purpose text, making the result deterministic and
    easy to compose in scripts.
    """
    terms = _query_tokens(query)
    # Clamp caller-provided bounds instead of allowing an accidental unbounded
    # discovery response.  A negative cursor is a usage mistake, not a request
    # to wrap around the catalog.
    bounded_limit = max(1, min(int(limit), _MAX_FIND_LIMIT))
    offset = max(0, int(cursor))
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
        searchable = " ".join(source for _, source in sources).casefold()
        searchable_tokens = _tokens(f"{primary_text} {searchable}")
        score = 0
        matched = True
        for term in terms:
            aliases = _token_aliases(term)
            if not (aliases & searchable_tokens):
                matched = False
                break
            if term in _tokens(primary_text):
                score += 100
            elif term in _tokens(searchable):
                score += 40
            else:
                score += 20
            # Exact phrase/path matches outrank a synonym match, then stable
            # command-id ordering breaks all remaining ties.
            if term in searchable_tokens:
                score += 10
        if matched:
            # Purpose and command-specific hints are stronger than generic
            # family words such as ``data`` or ``show``.
            score += 5 * sum(
                1 for term in terms if any(term in source.casefold() for _, source in sources[:2])
            )
            command_purpose = _COMMAND_DISCOVERY_PURPOSES.get(command_id, "").casefold()
            score += 100 * sum(1 for term in terms if term in _tokens(command_purpose))
            action = command_path.split()[1] if len(command_path.split()) > 1 else ""
            if "show" in terms and action in {"list", "get", "browse"}:
                score += 80
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
    page = [match for _, match in ranked_matches[offset : offset + bounded_limit]]
    has_more = offset + len(page) < total_matches
    continuation = (
        {
            "next_cursor": str(offset + len(page)),
            "has_more": True,
            "limit": bounded_limit,
            "query": query,
        }
        if has_more
        else None
    )
    return {
        "query": query,
        "matches": page,
        "total_matches": total_matches,
        "truncated": has_more,
        "continuation": continuation,
    }


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
        "wait_policy": record["wait_policy"],
        "pagination_policy": record["pagination_policy"],
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
