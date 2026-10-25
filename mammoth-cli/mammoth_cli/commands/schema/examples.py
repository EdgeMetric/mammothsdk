"""Runnable examples: a copy-pasteable command line, with sample ids and input, per command."""

from __future__ import annotations

import json
import shlex
from typing import Any

from mammoth_cli.services.argspec import FieldSpec
from mammoth_cli.services.command_contract import LOCAL_COMMANDS, resolve_command_contract
from mammoth_cli.services.input_fields import (
    example_input_hints,
    handler_owned_fields,
)
from mammoth_cli.services.openapi_types import (
    openapi_body_schema_for,
    sample_from_schema,
)
from mammoth_cli.services.positionals import PositionalSpec, resolve_positionals
from mammoth_cli.services.type_system import is_opaque_mapping, sample_value

# Agent examples carry no ``--output json --no-input``: a piped run already
# gets machine JSON and never prompts, and ``MAMMOTH_OUTPUT``/``MAMMOTH_NO_INPUT``
# cover a session that is not piped.
_OUTPUT_JSON_NO_INPUT: tuple[str, ...] = ()


# A command whose request carries a secret never gets an inline JSON example:
# the published example points at a protected owner-only file instead, so no
# generated or copied command line ever puts a credential in argv.
_PROTECTED_INPUT_PATH = "/private/path/request.json"


# Commands whose useful example the SDK signature cannot express: a distinct
# second id, an optional-but-central input field, or two views to compare.
_FIXED_EXAMPLES: dict[str, tuple[tuple[str, ...], dict[str, Any]]] = {
    "view.optimize": (("123",), {}),
    "view.transform.batch": (
        ("123",),
        {
            "steps": [
                {
                    "op": "filter",
                    "input": {"condition": {"column": "Cost", "operator": "GTE", "value": 20}},
                },
                {"op": "sort", "input": {"order_by": [["Cost", "DESC"]]}},
                {"op": "limit-rows", "input": {"n": 2}},
            ],
            "dataset_id": 456,
        },
    ),
    "view.transform.first-name": (
        ("123",),
        {"column": "Name", "new_column": "First name", "dataset_id": 456},
    ),
    "view.transform.update-column": (
        ("123",),
        {"column": "Cost", "expression": "Cost + 5", "dataset_id": 456},
    ),
    "view.explore-panel.get": (("123",), {}),
    "view.explore-panel.set": (
        ("123",),
        {"panel": {"columns": "all"}},
    ),
    "view.explore-panel.edit": (
        ("123",),
        {"edits": [{"op": "metric", "card": "Region", "agg": "SUM", "of": "Amount"}]},
    ),
    "view.explore-panel.add-to-dashboard": (
        ("123",),
        {"card": "Region", "new_dashboard_title": "Regions"},
    ),
    "view.explore-panel.export-image": (
        ("123",),
        {"card": "Region", "output_path": "card.svg", "style_id": None},
    ),
    "project.check": (("123", "456"), {}),
    "agent.chat": (
        (),
        {
            "message": "Summarize revenue by region",
            "scope": {"type": "workspace", "workspace_id": 123},
            "client_context": {"project_id": 456},
        },
    ),
    "view.data.profile": (("123",), {"target": "Churn"}),
    "dataset.definition.add": (
        ("123",),
        {"term": "late", "definition": "delivered more than 5 days after shipped_date"},
    ),
    "dataset.definition.remove": (("123", "a1b2c3d4"), {}),
    "dataset.refresh": (("123",), {}),
    "view.data.drivers": (
        ("123",),
        {
            "measure": {"column": "revenue", "function": "SUM"},
            "date_column": "sale_date",
            "compare": ["2026-07", "2026-08"],
            "by": ["store", "category"],
        },
    ),
    "view.data.forecast": (
        ("123",),
        {
            "measure": {"column": "revenue", "function": "SUM"},
            "date_column": "sale_date",
            "unit": "month",
            "periods": 2,
        },
    ),
    "view.variants.create": (
        ("123",),
        {"from_view": 456, "column": "Region", "values": ["East", "West"]},
    ),
    "workflow.canvas": (
        ("12",),
        {
            "canvas_state": {
                "proposed_changes": [
                    {
                        "op": "add_view",
                        "dataset_id": 415,
                        "name": "Urgent tickets",
                        "ref": "urgent",
                    },
                    {
                        "op": "add_step",
                        "view_ref": "urgent",
                        "transform": "filter",
                        "params": {
                            "condition": {
                                "column": "Priority",
                                "operator": "EQ",
                                "value": "Urgent",
                            }
                        },
                        "label": "Keep urgent tickets",
                    },
                    {
                        "op": "send_to_new_dataset",
                        "dataset_id": 415,
                        "view_ref": "urgent",
                        "name": "Urgent tickets by team",
                    },
                ]
            }
        },
    ),
    "view.data.compare": (
        ("111", "222"),
        {
            "group_by": ["Campaign"],
            "aggregations": [{"column": "Spend", "function": "SUM", "as_name": "Spend"}],
        },
    ),
}


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
    # Exact names whose value has one obvious, valid shape.
    exact = {
        "slug": "revenue-overview",
        "object_type": "change_plan",
        "agent_key": "revenue-assistant",
        "connector_key": "postgres",
        "connection_key": "prod-warehouse",
        "client_key": "web-client",
        "ds_config_key": "orders-config",
        "sheet": "Sheet1",
        "delimiter": ",",
        "quotechar": '"',
        "quote_char": '"',
        "find": "N/A",
        "search": "N/A",
        "replace": "Unknown",
        "sheets": "Sheet1",
        "version": "1",
        "as": "Total revenue",
        "timezone": "UTC",
    }
    if name in exact:
        return exact[name]
    if any(part in name for part in ("password", "secret", "token", "credential")):
        return "replace-with-secret"
    if "email" in name:
        return "analyst@example.com"
    if "origin" in name:
        return "https://example.com"
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
    if "column" in name or name in {
        "source",
        "key",
        "field",
        "group_by",
        "rows",
        "left",
        "right",
        "select",
        "on",
    }:
        return "Status"
    if name in {"start", "end"}:
        return "Order Date" if name == "start" else "Ship Date"
    if name in {
        "description",
        "body",
        "content",
        "text",
        "note",
        "comment",
        "expected",
        "code",
    }:
        return "Quarterly revenue summary"
    if name.endswith("_id") or name in {"id", "identifier"}:
        return "resource-123"
    # No safe guess: a visible placeholder, never a literal that looks like data.
    return f"<{field_name}>"


def _humanize_sample(value: Any, field_name: str) -> Any:
    """Replace generator placeholders with domain-shaped representative data."""
    if value == "example":
        return _representative_string(field_name)
    if isinstance(value, int) and not isinstance(value, bool) and "skip" in field_name:
        # Rows to skip: an example that skips one would drop a real first row.
        return 0
    if isinstance(value, list):
        singular = field_name[:-1] if field_name.endswith("s") else field_name
        return [_humanize_sample(item, singular) for item in value]
    if isinstance(value, dict):
        return {
            ("name" if key == "example" else key): _humanize_sample(
                item, "key" if key == "example" else key
            )
            for key, item in value.items()
        }
    return value


_DISTINCT_IDS = ("123", "456", "789", "1011")


#: Commands whose ``--confirm`` is a positional other than the first: the change lands on the
#: second id (the workspace of a partner, the storage option of a plan), not on its parent.
_CONFIRM_POSITIONAL: dict[str, str] = {
    "support.partner.client.delete": "workspace_id",
    "support.partner.client.detach": "workspace_id",
    "support.partner.client.cancel-detach": "workspace_id",
    "support.plan.storage-option.update": "option_id",
    "support.plan.storage-option.archive": "option_id",
}


def _confirm_index(command_id: str, specs: tuple[PositionalSpec, ...], given: int) -> int:
    """Index, among the example's positionals, of the one ``--confirm`` must repeat."""
    name = _CONFIRM_POSITIONAL.get(command_id)
    for index, spec in enumerate(specs):
        if spec.name == name and index < given:
            return index
    return 0


#: ``confirm_target`` commands that confirm the signed-in workspace, not a positional: the
#: example carries ``--confirm`` with a sample workspace id distinct from its other ids.
_WORKSPACE_CONFIRM_EXAMPLES = frozenset(
    {
        "agent.access.settings.update",
        "billing.hosted-page",
        "billing.stripe.create",
        "billing.stripe.held-change.cancel",
    }
)


def runnable_example(
    record: dict[str, Any],
    symbol: str | None,
    positionals: tuple[PositionalSpec, ...] | None = None,
) -> str | None:
    """Build one complete, copy-pasteable command line for this command.

    The line from :func:`_runnable_example` with its positional ids made distinct
    (``VIEW_ID DATASET_ID`` is ``123 456``, never ``123 123``) and a dataset id
    added when the SDK requires one but the command only takes it as an optional
    trailing positional, so the example names everything it needs without a lookup.
    """
    line = _runnable_example(record, symbol, positionals)
    if line is None:
        return None
    command_id = str(record["command_id"])
    if command_id == "parameter.create":
        # A parameter name is an identifier (letters, digits, underscore): no spaces.
        line = line.replace("'Revenue report'", "revenue_report", 1)
    specs = positionals if positionals is not None else resolve_positionals(command_id)
    tokens = shlex.split(line)
    start = 1 + len(str(record["command_path"]).split())
    end = start
    while end < len(tokens) and not tokens[end].startswith("-"):
        end += 1
    given = tokens[start:end]
    contract = resolve_command_contract(command_id)
    needs_dataset = contract is not None and any(
        field.name == "dataset_id" and field.required for field in contract.accepted_fields
    )
    for index, spec in enumerate(specs):
        if spec.name == "dataset_id" and len(given) == index and needs_dataset:
            given.append("456")
    seen: set[str] = set()
    for index, value in enumerate(given):
        if value.isdigit() and value in seen:
            value = next(item for item in _DISTINCT_IDS if item not in seen)
            given[index] = value
        seen.add(value)
    rest = tokens[end:]
    # Whatever a command's manifest policy asks, its example must already answer, so a copied
    # example runs unattended instead of stopping at ``confirmation_required``. A
    # ``confirm_target`` command whose target is no positional (the workspace, say) keeps
    # only ``--yes``; its refusal names the exact ``--confirm`` value.
    policy = record.get("confirmation")
    if policy in {"prompt_or_yes", "confirm_target", "yes_always"} and "--yes" not in rest:
        rest.append("--yes")
    if policy == "confirm_target" and "--confirm" not in rest:
        if command_id in _WORKSPACE_CONFIRM_EXAMPLES:
            workspace = next(item for item in _DISTINCT_IDS if item not in given)
            rest.extend(["--confirm", workspace])
        elif given:
            rest.extend(["--confirm", given[_confirm_index(command_id, specs, len(given))]])
    return shlex.join([*tokens[:start], *given, *rest])


def _runnable_example(
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
        required ``--input`` field; or None
        when the command has no resolvable backing signature.
    """
    if not symbol:
        return None
    # Credential documents must never be synthesized into a JSON command
    # example.  The local auth adapter validates a protected file reference;
    # the manifest carries the safe ``creds.json`` invocation instead.
    if record["command_id"] == "auth.login":
        return None
    if record["command_id"] == "view.data.get":
        # VIEW_ID then DATASET_ID: two different placeholders so a reader can
        # tell which is which (the generic fallback printed "123 123").
        return "mammoth view data get 123 456"
    if record["command_id"] == "ai.retention.condition":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"mode": "generate", "intent": "completed payments older than 90 days"}),
                *_OUTPUT_JSON_NO_INPUT,
                "--project",
                "456",
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
                "Sales.twbx",
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
        # COPY follows the backend param template (a list of SOURCE/AS items
        # with VERSION 2); the former ``COPY: {}`` placeholder was rejected
        # with backend code 720.
        task_input: dict[str, Any] = {
            "task_spec": {
                "DATAVIEW_ID": 123,
                "SEQUENCE_NUMBER": 1,
                "COPY": [
                    {
                        "SOURCE": "column_1",
                        "AS": {
                            "COLUMN": "Copy of column 1",
                            "TYPE": "TEXT",
                            "INTERNAL_NAME": "column_9",
                        },
                    }
                ],
                "VERSION": 2,
            }
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
    if record["command_id"] in _FIXED_EXAMPLES:
        positional_samples, sample_input = _FIXED_EXAMPLES[record["command_id"]]
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                *positional_samples,
                *(["--input", json.dumps(sample_input)] if sample_input else []),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "batch.create-spec":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"file_id": 94}),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "view.data.aggregate":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps(
                    {
                        "group_by": ["Channel"],
                        "aggregations": [
                            {"column": "Spend", "function": "SUM", "as_name": "Total Spend"}
                        ],
                    }
                ),
                *_OUTPUT_JSON_NO_INPUT,
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
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"name": "Revenue"}),
                *_OUTPUT_JSON_NO_INPUT,
            ]
        )
    if record["command_id"] == "dashboard.tags.set":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"tags": ["Revenue"]}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.delete":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.tags.merge":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"target_id": 456}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
            ]
        )
    if record["command_id"] == "dashboard.archive":
        return shlex.join(
            [
                "mammoth",
                *record["command_path"].split(),
                "123",
                "--input",
                json.dumps({"archived": True}),
                *_OUTPUT_JSON_NO_INPUT,
                "--yes",
                "--confirm",
                "123",
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
    if record["command_id"] in {"project.user.update", "workspace.user.add"}:
        # These published high-impact examples must satisfy the same policy
        # their manifests advertise; otherwise discovery emits a command that
        # deterministically fails before dispatch.
        tokens.append("--yes")
    if record["command_id"] in {
        "project.resource-dependencies.update",
        "dashboard.embed.key.rotate",
        "dashboard.embed.secret.rotate",
        "dashboard.embed.config.set",
        "dashboard.embed.origin.revoke",
        "dashboard.context.apply",
    }:
        # These commands have a confirm_target policy.  Keep their generated
        # example executable in non-interactive mode instead of advertising a
        # request that the safety guard will reject.
        tokens.extend(["--yes", "--confirm", str(_sample_positional_value(positionals[0]))])
    elif record["command_id"] == "dashboard.create-blank":
        tokens.append("--yes")
    return shlex.join(tokens)
