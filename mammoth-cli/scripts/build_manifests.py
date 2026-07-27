#!/usr/bin/env python3
"""Generate the three reviewed parity manifests from pinned inputs.

Inputs (all offline):
- ``spec/openapi/openapi.json``          pinned production snapshot (376 ops).
- SDK introspection                      242 public methods.
- ``scripts/_command_map.py``            primary-reviewed op dispositions.
- ``scripts/_sdk_catalog.py``            primary-reviewed SDK command mapping.

Outputs:
- ``spec/manifests/openapi-operations.yaml``  376 operation records.
- ``spec/manifests/sdk-methods.yaml``         242 SDK method records.
- ``spec/manifests/commands/<group>.yaml``    one command record per command.

Regeneration is deterministic: re-running must produce no diff.
"""

from __future__ import annotations

import shlex
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
SPEC = SCRIPTS.parent / "spec"
MANIFESTS = SPEC / "manifests"
COMMANDS_DIR = MANIFESTS / "commands"
REPO_ROOT = SCRIPTS.parent.parent

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT))

import _command_map as cmap  # noqa: E402
from _openapi_extract import iter_operations, load_snapshot  # noqa: E402
from _sdk_catalog import CLI_ONLY_COMMANDS, EXTRA_OP_HINTS, load_sdk_catalog  # noqa: E402

from mammoth_cli.services.positionals import positionals_for  # noqa: E402

REVIEWER = "primary"


def _yaml_dump(data: Any) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


# --- mutation/confirmation/wait/pagination derivation ----------------------

READ_METHODS = {"GET"}
HIGH_IMPACT_GROUPS = {"billing", "support"}

# Response component schemas that denote an async *job handle* the caller must
# wait on (the server kicked off work and returned only a reference), as opposed
# to a job *status record* returned by a job-read endpoint. A command whose
# success response is one of these -- directly or as a union member -- has not
# produced its result yet, so labelling it ``not_async`` is a lie.
_JOB_HANDLE_SCHEMAS = frozenset({"ObjectJobSchema", "JobResponse"})


def _operations_with_job_id(document: dict[str, Any]) -> set[str]:
    """Return operationIds that accept a ``job_id`` parameter (path or query).

    Such an operation reads a *specific, already-known* job, so its job-shaped
    response is a status record to return verbatim -- it must never auto-wait.
    """
    result: set[str] = set()
    for path_item in document.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        shared = path_item.get("parameters", []) or []
        for method, operation in path_item.items():
            if method not in {"get", "put", "post", "delete", "patch"}:
                continue
            if not isinstance(operation, dict):
                continue
            params = shared + (operation.get("parameters", []) or [])
            names = {p.get("name") for p in params if isinstance(p, dict)}
            if "job_id" in names and operation.get("operationId"):
                result.add(str(operation["operationId"]))
    return result


def derive_mutation(command_id: str, method: str) -> str:
    group = command_id.split(".", 1)[0]
    if group in HIGH_IMPACT_GROUPS:
        return "high_impact"
    if command_id in {"workspace.delete", "user.delete-account", "support.ownership.transfer"}:
        return "high_impact"
    if command_id.startswith("view.transform.") or command_id.startswith("view.task."):
        if method in READ_METHODS:
            return "read"
        return "reversible_pipeline"
    if command_id.startswith("view.export.") and method not in READ_METHODS:
        return "external_effect"
    if method in READ_METHODS:
        return "read"
    if method == "DELETE":
        return "destructive"
    if method == "POST" and (
        command_id.endswith(".create") or ".create" in command_id or command_id.endswith(".upload")
    ):
        return "benign_mutation"
    return "benign_mutation"


def derive_confirmation(mutation_class: str) -> str:
    return {
        "read": "none",
        "benign_mutation": "none",
        "reversible_pipeline": "none",
        "destructive": "prompt_or_yes",
        "high_impact": "confirm_target",
        "external_effect": "yes_always",
    }[mutation_class]


# Commands whose success response is a job handle (kicked-off async work) but
# whose backing SDK method does not wait internally, so the CLI handler must wait
# and the reviewed wait policy must say so. Structurally the same case the
# dashboard promotion below handles, enumerated here for the non-dashboard
# families the audit confirmed return unfinished state.
_ASYNC_JOB_COMMANDS = frozenset(
    {
        "dataset.create",
        "folder.trash",
        "trash.add",
        "trash.restore",
        "user.avatar.upload",
        "view.pipeline.edit",
    }
)


def derive_wait(command_id: str, method: str, catalog_value: str | None) -> str:
    # A hand-reviewed async-job command is authoritative: its handler blocks on
    # the kicked-off job and returns the finished result, so the manifest must
    # advertise a waiting policy even when a stale catalog entry says otherwise.
    if command_id in _ASYNC_JOB_COMMANDS:
        return "always_wait"
    if catalog_value:
        return catalog_value
    if command_id.startswith("view.transform.") and method != "GET":
        return "always_wait"
    if command_id.startswith("view.task.") and method == "POST":
        return "always_wait"
    if command_id in {"job.wait", "job.wait-many", "view.pipeline.wait"}:
        return "always_wait"
    return "not_async"


def derive_pagination(command_id: str, method: str, catalog_value: str | None) -> str:
    if catalog_value:
        return catalog_value
    if method == "GET" and (command_id.endswith(".list") or command_id.endswith("-list")):
        return "single_page"
    return "none"


def derive_acceptance(command_id: str, mutation_class: str) -> tuple[str, str | None]:
    group = command_id.split(".", 1)[0]
    if mutation_class in {"high_impact", "external_effect"} or group in {"billing", "support"}:
        return "contract_only_high_impact", (
            "High-impact or external-effect operation without a disposable fixture."
        )
    if group in {"workspace", "user"} and mutation_class != "read":
        return "contract_only_high_impact", (
            "Account or workspace mutation without a disposable fixture."
        )
    if mutation_class == "read":
        return "live_read_only", None
    if group == "dashboard":
        return "contract_only_no_disposable_fixture", (
            "Dashboard mutation has contract coverage but no automated disposable-dashboard "
            "fixture in tests/live."
        )
    # Project-scoped safe operations run against a disposable project.
    return "live_disposable_project", None


def _model_base(command_id: str) -> str:
    parts = [p for chunk in command_id.split(".") for p in chunk.split("-")]
    return "".join(word.capitalize() for word in parts)


def build_command_record(
    command_id: str,
    *,
    operation_ids: list[str],
    method: str,
    sdk_symbol: str,
    catalog: dict[str, Any] | None,
    disposition: str = "command",
    alias_of: str | None = None,
) -> dict[str, Any]:
    command_path = command_id.replace(".", " ")
    op_token = command_id.upper().replace(".", "-").replace(" ", "-")
    mutation = (catalog or {}).get("mutation_class") or derive_mutation(command_id, method)
    wait = derive_wait(command_id, method, (catalog or {}).get("wait_policy"))
    pagination = derive_pagination(command_id, method, (catalog or {}).get("pagination_policy"))
    # A reviewed catalog entry may pin an explicit confirmation policy when the
    # derived default for its mutation class does not fit (e.g. a local
    # external-effect command that should prompt at a TTY rather than always
    # require --yes). Otherwise derive it from the mutation class.
    confirmation = (catalog or {}).get("confirmation") or derive_confirmation(mutation)
    evidence, exemption = derive_acceptance(command_id, mutation)
    base = _model_base(command_id)
    positionals = positionals_for(command_id, sdk_symbol)
    required_metavars = "".join(f" {p.metavar}" for p in positionals if p.required)

    # Honor an explicit ``example_value`` (a concrete, resolvable id for the
    # discovery commands) so this fallback example -- used when a command has no
    # resolvable SDK signature for ``runnable_example`` -- still runs to exit
    # zero, matching ``schema._sample_positional_value``.
    def _sample(spec: Any) -> str:
        if spec.example_value is not None:
            return str(spec.example_value)
        return "123" if spec.type is int else "example"

    positional_samples = "".join(f" {shlex.quote(_sample(p))}" for p in positionals)

    record: dict[str, Any] = {
        "command_id": command_id,
        "command_path": command_path,
        "disposition": disposition,
        "alias_of": alias_of,
        "operation_ids": operation_ids,
        "positionals": [p.as_manifest() for p in positionals],
        "options": [],
        "sdk_symbol": sdk_symbol,
        "sdk_conversion": (catalog or {}).get("sdk_conversion")
        or f"Call {sdk_symbol} with validated request fields.",
        "request_model": f"{base}Request",
        "result_model": f"{base}Result",
        "mutation_class": mutation,
        "confirmation": confirmation,
        "wait_policy": wait,
        "pagination_policy": pagination,
        "acceptance_evidence": evidence,
        "live_test": f"LT-{op_token}" if exemption is None else None,
        "live_exemption_reason": exemption,
        "contract_fixture": None,
        "required_fixture_guard": None,
        "secret_fields": list((catalog or {}).get("secret_fields") or []),
        "human_example": (catalog or {}).get("human_example")
        or f"mammoth {command_path}{required_metavars} --help",
        "agent_example": (catalog or {}).get("agent_example")
        or f"mammoth {command_path}{positional_samples} --output json --no-input",
        "unit_tests": [f"UT-{op_token}"],
        "contract_tests": [f"CT-{op_token}-HUMAN", f"CT-{op_token}-JSON", f"CT-{op_token}-ERROR"],
        "draft_test": None,
        "undo_test": None,
        "known_restrictions": (catalog or {}).get("notes"),
        "reviewed_by": REVIEWER,
    }
    # This is the same recursive, shell-safe example used by schema discovery;
    # keeping it here prevents manifests and generated docs from carrying a
    # syntactically valid but semantically incomplete invocation.
    from mammoth_cli.commands.schema import runnable_example

    if not (catalog or {}).get("agent_example"):
        record["agent_example"] = (
            runnable_example(record, sdk_symbol, positionals) or record["agent_example"]
        )
    if command_id.startswith("view.transform.") or command_id.startswith("view.draft."):
        record["draft_test"] = f"LT-{op_token}-DRAFT"
    if mutation == "reversible_pipeline":
        record["undo_test"] = f"LT-{op_token}-UNDO"
    return record


def build() -> dict[str, int]:
    document = load_snapshot()
    ops = iter_operations(document)
    sdk_catalog = load_sdk_catalog()  # sdk_symbol -> record
    cmd_to_sym: dict[str, str] = {}
    cmd_to_cat: dict[str, dict[str, Any]] = {}
    for record in sdk_catalog.values():
        command = record.get("canonical_command")
        if command and command not in cmd_to_sym:
            cmd_to_sym[command] = record["sdk_symbol"]
            cmd_to_cat[command] = record

    # 1. openapi-operations.yaml
    op_records: list[dict[str, Any]] = []
    command_ops: dict[str, list[str]] = defaultdict(list)
    command_method: dict[str, str] = {}
    for meta in ops:
        oid = meta["operation_id"]
        disposition, command, alias_of, reason = cmap.disposition_for(oid)
        sdk_symbol: str | None = None
        if disposition == "command":
            sdk_symbol = cmd_to_sym.get(command) or cmap.planned_symbol(command)
            command_ops[command].append(oid)
            command_method.setdefault(command, meta["method"])
        op_records.append(
            {
                "identity": meta["identity"],
                "method": meta["method"],
                "path": meta["path"],
                "operation_id": oid,
                "tags": meta["tags"],
                "summary": meta["summary"],
                "security": meta["security"],
                "request_schema": meta["request_schema"],
                "response_schemas": meta["response_schemas"],
                "deprecated": meta["deprecated"],
                "disposition": disposition,
                "disposition_reason": reason,
                "canonical_command": command,
                "alias_of": alias_of,
                "sdk_symbol": sdk_symbol,
                "reviewed_by": REVIEWER,
            }
        )
    op_records.sort(key=lambda record: (record["path"], record["method"]))
    (MANIFESTS / "openapi-operations.yaml").write_text(
        _yaml_dump(
            {
                "manifest_schema_version": 1,
                "operation_count": len(op_records),
                "operations": op_records,
            }
        ),
        encoding="utf-8",
    )

    # 2. sdk-methods.yaml
    from inventory_sdk import build_document as build_sdk_introspection

    introspection = build_sdk_introspection()
    sdk_records: list[dict[str, Any]] = []
    for method in introspection["methods"]:
        symbol = method["sdk_symbol"]
        cat = sdk_catalog.get(symbol, {})
        no_command_reason = None
        if not cat.get("canonical_command") and not cat.get("alias_of"):
            no_command_reason = cat.get("notes") or "SDK-only helper; no reviewed CLI command."
        sdk_records.append(
            {
                "sdk_symbol": symbol,
                "implementation_origin": symbol,
                "signature": method["signature"],
                "openapi_operation_ids": cat.get("openapi_operation_ids", []),
                "canonical_command": cat.get("canonical_command"),
                "alias_of": cat.get("alias_of"),
                "no_command_reason": no_command_reason,
                "mutation_class": cat.get("mutation_class"),
                "wait_policy": cat.get("wait_policy"),
                "pagination_policy": cat.get("pagination_policy"),
                "secret_fields": cat.get("secret_fields", []),
                "reviewed_by": REVIEWER,
            }
        )
    sdk_records.sort(key=lambda record: record["sdk_symbol"])
    (MANIFESTS / "sdk-methods.yaml").write_text(
        _yaml_dump(
            {
                "manifest_schema_version": 1,
                "method_count": len(sdk_records),
                "generator_version": introspection["generator_version"],
                "methods": sdk_records,
            }
        ),
        encoding="utf-8",
    )

    # 3. commands/<group>.yaml
    commands: dict[str, dict[str, Any]] = {}
    # op-backed commands
    for command, oids in command_ops.items():
        sym = cmd_to_sym.get(command) or cmap.planned_symbol(command)
        commands[command] = build_command_record(
            command,
            operation_ids=sorted(set(oids)),
            method=command_method.get(command, "POST"),
            sdk_symbol=sym,
            catalog=cmd_to_cat.get(command),
        )
    # extra SDK-convenience commands: every catalog canonical command that is
    # not already produced from an operation (transforms, draft verbs, export
    # variants, waits, and other SDK conveniences over shared operations).
    for command in sorted(cmd_to_sym):
        if command in commands:
            continue
        hint = EXTRA_OP_HINTS.get(command, {})
        commands[command] = build_command_record(
            command,
            operation_ids=hint.get("operation_ids", []),
            method=hint.get("method", "POST"),
            sdk_symbol=cmd_to_sym[command],
            catalog=cmd_to_cat.get(command),
        )
    # CLI-only commands (auth, config, context, doctor, capability, schema, skill)
    for command, spec in CLI_ONLY_COMMANDS.items():
        commands[command] = build_command_record(
            command,
            operation_ids=[],
            method=spec.get("method", "GET"),
            sdk_symbol=spec["sdk_symbol"],
            catalog={
                "mutation_class": spec["mutation_class"],
                "wait_policy": "not_async",
                "pagination_policy": spec.get("pagination_policy", "none"),
                "confirmation": spec.get("confirmation"),
            },
        )
        commands[command]["acceptance_evidence"] = "live_read_only"
        commands[command]["live_test"] = None
        commands[command]["live_exemption_reason"] = spec.get(
            "live_exemption_reason", "Local CLI operation; no server call."
        )

    # Correct async classification structurally: a dashboard command whose
    # success response is a job *handle* (kicked-off work) but which is labelled
    # not_async returns a raw job and silently ignores --job-timeout. The
    # generated and handwritten dashboard SDK methods never wait internally, so
    # the CLI must. Promote such commands to always_wait; exempt job-status
    # reads (a job_id parameter) whose job-shaped body is the intended payload.
    op_response_schemas = {meta["operation_id"]: set(meta["response_schemas"]) for meta in ops}
    job_status_ops = _operations_with_job_id(document)
    for command, record in commands.items():
        if not command.startswith("dashboard."):
            continue
        if record.get("wait_policy") != "not_async":
            continue
        oids = record.get("operation_ids") or []
        returns_handle = any(
            op_response_schemas.get(oid, set()) & _JOB_HANDLE_SCHEMAS for oid in oids
        )
        is_status_read = any(oid in job_status_ops for oid in oids)
        if returns_handle and not is_status_read:
            record["wait_policy"] = "always_wait"

    # write grouped by top-level group
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for command_id, record in commands.items():
        grouped[command_id.split(".", 1)[0]].append(record)
    # clear stale files
    if COMMANDS_DIR.exists():
        for stale in COMMANDS_DIR.glob("*.yaml"):
            stale.unlink()
    COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
    for group in sorted(grouped):
        records = sorted(grouped[group], key=lambda record: record["command_id"])
        (COMMANDS_DIR / f"{group}.yaml").write_text(
            _yaml_dump({"manifest_schema_version": 1, "commands": records}),
            encoding="utf-8",
        )

    return {
        "operations": len(op_records),
        "sdk_methods": len(sdk_records),
        "commands": len(commands),
        "command_groups": len(grouped),
    }


if __name__ == "__main__":
    result = build()
    import json

    print(json.dumps(result, indent=2))
