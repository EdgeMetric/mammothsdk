"""Handler output matches each command's declared ``output_schema`` (#315).

Every command with a declared schema is run through the real CLI, the real SDK and the real
handler on its manifest ``agent_example``. Only the HTTP layer is replaced: each request
gets a sample built from the OpenAPI ``200`` schema of the operation it hits (the stand-in
for a recorded response; the repository holds none). The envelope's ``data`` must then
validate against the declared schema.

A command that stops with an error on its example (it needs an input the example cannot
supply from a sampled response) is counted as unexercised, not as passing. Every write must
run: one that cannot is named in ``_EXEMPT`` with the reason, and its schema is checked
against a hand-built result instead. ``FLOOR_READS`` keeps the unexercised reads from
growing unnoticed. A ``--dry-run`` of each write is checked against the dry-run report schema.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from mammoth.api.exports import ExportsAPI
from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError

from mammoth_cli.commands.schema import dry_run_output_schema, output_schema
from mammoth_cli.context import resolver
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.runtime import verify
from mammoth_cli.services import openapi_types
from mammoth_cli.services.explore_cards import card_for_column
from mammoth_cli.services.openapi_types import openapi_response_schema_for
from mammoth_cli.testing import login_default_profile, make_runner

#: Declared reads whose example must run to a result and validate.
FLOOR_READS = 318
#: Writes whose ``--dry-run`` must come back as a ``DryRunReport`` (a local command and a
#: handler with no gated call return their real result instead).
FLOOR_DRY_RUNS = 450

#: What the SDK returns for an artifact route (PNG, PDF, MP4, HTML): a description of the body.
_BINARY_BODY = {
    "content_type": "image/png",
    "size_bytes": 3,
    "sha256": "0" * 64,
    "content_base64": "AAAA",
}

#: Commands whose response is polymorphic in a way the sampler cannot build: the SDK's model
#: rewrites the sampled branch's discriminating values, so the sample matches no branch.
_UNSAMPLABLE = frozenset({"connector.ds-config.get"})

#: Commands whose example cannot run to a result against sampled responses, each with the
#: reason. Their declared schema is checked against a hand-built result instead
#: (``test_an_unexercisable_command_result_matches_its_schema``).
_EXEMPT: dict[str, str] = {
    "dataset.update": "always refuses with unsupported_contract until the backend takes it",
    "schedule.create": "the backend answers NOT_IMPLEMENTED (feature_unavailable)",
    "view.export.dataset": "creates a dataset and waits 300 s on a job the sample never ends",
    "view.draft.auto-run": "the sampled pipeline stays in a reference error after the toggle",
    "history.undo": "needs a journaled write to undo; test_history.py runs it",
    "history.resume": "needs a journaled run to resume; test_history.py runs it",
}

#: Commands left out of the dry-run check: they wait on a background job the sample never ends.
_DRY_RUN_SKIPPED = frozenset({"view.export.dataset"})

_AGENT_SCOPE = '{"scope": {"type": "workspace", "workspace_id": 4}}'

#: Replacement examples for commands whose own example cannot run against a sampled response.
_EXAMPLES: dict[str, str] = {
    "agent.access.grant.update": (
        'mammoth agent access grant update 123 --input \'{"level": "ask"}\''
    ),
    "folder.bulk-delete": "mammoth folder bulk-delete --input '{\"folder_ids\": [1]}' --yes",
    "batch.create": 'mammoth batch create 123 456 --input \'{"mapping": {"example": "example"}}\'',
    "view.explore-panel.edit": (
        "mammoth view explore-panel edit 123 456 --input"
        ' \'{"edits": [{"op": "metric", "card": "Region", "agg": "SUM",'
        ' "of": "Revenue"}]}\''
    ),
    "folder.delete": "mammoth folder delete 1 --yes",
    "folder.trash": "mammoth folder trash 1",
    "folder.update": 'mammoth folder update 1 --input \'{"name": "Revenue report"}\'',
    "view.transform.rename-columns": (
        "mammoth view transform rename-columns 123 --input"
        ' \'{"renames": {"cust_id": "Customer reference"}, "dataset_id": 456}\''
    ),
    "view.transform.extract-date": (
        "mammoth view transform extract-date 123 --input"
        ' \'{"column": "Order Date", "component": "year", "dataset_id": 456}\''
    ),
    "view.transform.increment-date": (
        "mammoth view transform increment-date 123 --input"
        ' \'{"column": "Order Date", "delta": {"days": 1}, "dataset_id": 456}\''
    ),
    "view.variants.create": (
        "mammoth view variants create 456 --input"
        ' \'{"from_view": 123, "column": "Region", "values": ["East", "West"]}\''
    ),
    "batch.update": (
        "mammoth batch update 123 --input"
        ' \'{"patch": [{"op": "replace", "path": "/name", "value": "Status"}]}\''
    ),
    "view.ai.generate-data": (
        "mammoth view ai generate-data 123 --input"
        ' \'{"prompt": "Summarize revenue by region", "dataset_id": 456}\''
    ),
    "view.task.preview-cancel": (
        "mammoth view task preview-cancel 123 456 --input '{\"dataset_id\": 456}'"
    ),
    "view.draft.submit": "mammoth view draft submit 123 --input '{\"dataset_id\": 456}'",
    "view.export.create": (
        'mammoth view export create 123 --input \'{"dataset_id": 456, "export_spec":'
        ' {"DATAVIEW_ID": 1, "handler_type": "postgres", "trigger_type": "none",'
        ' "run_immediately": true}}\' --yes'
    ),
    "view.export.csv": "mammoth view export csv 123 --input '{\"dataset_id\": 456}'",
    "view.export.download": (
        'mammoth view export download 123 --input \'{"file_type": "xml", "dataset_id": 456}\''
    ),
    "view.export.bigquery": (
        'mammoth view export bigquery 123 456 --input \'{"selected_profile": {},'
        ' "selected_identity": {}, "table": "exports", "replace_table": true}\' --yes'
    ),
    "view.export.publish-db": (
        'mammoth view export publish-db 123 --input \'{"odbc_type": "postgres",'
        ' "replace_table": true, "target_properties": {"table": "exports"}}\' --yes'
    ),
    "agent.action.delete": "mammoth agent action delete act-1 --session sess-1 --yes",
    "agent.message.set-request-kind": (
        "mammoth agent message set-request-kind msg-1 --session sess-1"
        ' --input \'{"request_kind": "ask"}\''
    ),
    "agent.plan.approve": f"mammoth agent plan approve sess-1 --input '{_AGENT_SCOPE}' --yes",
    "agent.plan.discard": f"mammoth agent plan discard sess-1 --input '{_AGENT_SCOPE}' --yes",
    "agent.plan.skip": f"mammoth agent plan skip sess-1 1 --input '{_AGENT_SCOPE}'",
    "agent.plan.edit-proposal": (
        "mammoth agent plan edit-proposal --session sess-1 --input"
        ' \'{"plan_id": "plan-1", "action": "rename", "key": "Status"}\''
    ),
    "agent.run.extend": "mammoth agent run extend run-1 --session sess-1",
    "agent.run.pause": "mammoth agent run pause run-1 --session sess-1",
    "agent.run.resume": "mammoth agent run resume run-1 --session sess-1",
    "agent.run.retry": "mammoth agent run retry run-1 --session sess-1 --yes",
    "agent.run.stop": "mammoth agent run stop run-1 --session sess-1",
    "agent.run.units.set": (
        "mammoth agent run units set run-1 --session sess-1 --input"
        ' \'{"step": 1, "kind": "dataset", "units": [{"id": 12, "name": "Sales",'
        ' "project_id": 3}]}\''
    ),
    "agent.turn.cancel": "mammoth agent turn cancel turn-1 --session sess-1",
    "auth.login": f"mammoth auth login --input '{{\"api_token\": \"mm_{'t' * 43}\"}}'",
    "config.set": "mammoth config set output json",
    "connector.ds-config.create": (
        "mammoth connector ds-config create postgres prod-warehouse --input"
        ' \'{"query": "select 1"}\' --yes'
    ),
    "dashboard.filter.remove": (
        'mammoth dashboard filter remove 123 --input \'{"field": "example"}\''
    ),
    "dataset.create-from-pdf": (
        "mammoth dataset create-from-pdf 123 --input"
        ' \'{"file_name": "./sales.csv", "table_list": [0]}\''
    ),
    "dataset.interpretation.confirm": (
        "mammoth dataset interpretation confirm 123 --input"
        ' \'{"user_instruction": "first row is the header"}\''
    ),
    "dataset.interpretation.preview": (
        "mammoth dataset interpretation preview 123 --input"
        ' \'{"user_instruction": "first row is the header"}\''
    ),
    "dataset.update": (
        "mammoth dataset update --input"
        ' \'{"patch_data": [{"op": "replace", "path": "/name", "value": "Sales"}]}\' --yes'
    ),
    "file.upload-folder": "mammoth file upload-folder ./sales",
    "notification.update": (
        "mammoth notification update 123 --input"
        ' \'{"patch": [{"op": "replace", "path": "isRead", "value": true}]}\''
    ),
    "notification.update-batch": (
        "mammoth notification update-batch --input"
        ' \'{"patch": [{"op": "replace", "path": "isRead", "value": true}]}\''
    ),
    "parameter.group.update": 'mammoth parameter group update 123 --input \'{"name": "Prices"}\'',
    "parameter.update": 'mammoth parameter update 123 --input \'{"name": "Tax rate"}\'',
    "snippet.update": 'mammoth snippet update 123 --input \'{"name": "Total"}\'',
    "support.plan.storage-option.update": (
        "mammoth support plan storage-option update 123 456 --input '{\"storage_gb\": 5}'"
        " --yes --confirm 456"
    ),
    "support.subscription.create": (
        "mammoth support subscription create 123 resource-123 --input"
        ' \'{"customer_id": "cust-1"}\' --yes --confirm 123'
    ),
    "trash.add": 'mammoth trash add --input \'{"items": [{"id": 1, "type": "dataset"}]}\'',
    "trash.restore": 'mammoth trash restore --input \'{"items": [{"id": 1, "type": "dataset"}]}\'',
    "view.transform.combine-columns": (
        "mammoth view transform combine-columns 123 --input"
        ' \'{"sources": ["Status", "Region"], "new_column": "Label", "dataset_id": 456}\''
    ),
    "view.transform.date-diff": (
        "mammoth view transform date-diff 123 --input"
        ' \'{"component": "YEAR", "start": "Order Date", "end": "Admitted",'
        ' "new_column": "Age", "dataset_id": 456}\''
    ),
    "view.transform.math": (
        "mammoth view transform math 123 --input"
        ' \'{"expression": "price * quantity", "new_column": "Total", "dataset_id": 456}\''
    ),
    "view.transform.small-large": (
        "mammoth view transform small-large 123 --input"
        ' \'{"function": "SMALL", "columns": ["Q1", "Q2"], "new_column": "Low",'
        ' "dataset_id": 456}\''
    ),
    "view.transform.window": (
        "mammoth view transform window 123 --input"
        ' \'{"function": "ROW_NUMBER", "new_column": "Row", "dataset_id": 456}\''
    ),
    "webhook.update": "mammoth webhook update 123 --input '{\"is_secure\": true}'",
    "workflow.update": 'mammoth workflow update 123 --input \'{"name": "Nightly load"}\'',
    "workspace.user.remove-batch": (
        'mammoth workspace user remove-batch --input \'{"ids": "7,8"}\' --yes'
    ),
}

#: The request document of a command whose example reads one from a path (default ``{}``).
_DATABASE_EXPORT = (
    '{"host": "db.example", "port": 5432, "database": "sales", "table": "exports",'
    ' "username": "agent", "password": "secret", "replace_table": true}'
)
_REQUEST_DOCUMENTS: dict[str, str] = {
    "view.export.azure-blob": (
        '{"storage_account_name": "acct", "tenant_id": "t", "client_id": "c",'
        ' "client_secret": "s", "container_name": "box"}'
    ),
    "view.export.elasticsearch": (
        '{"host": "es.example", "username": "agent", "password": "secret", "index": "sales"}'
    ),
    "view.export.ftp": (
        '{"domain": "ftp.example", "directory": "/out", "file": "sales.csv",'
        ' "username": "agent", "password": "secret"}'
    ),
    "view.export.mssql": _DATABASE_EXPORT,
    "view.export.mysql": _DATABASE_EXPORT,
    "view.export.postgres": _DATABASE_EXPORT,
    "view.export.redshift": _DATABASE_EXPORT,
    "view.export.onedrive": (
        '{"tenant_id": "t", "client_id": "c", "client_secret": "s", "user_id": "u"}'
    ),
    "view.export.powerbi": (
        '{"username": "agent", "password": "secret", "client_id": "c", "dataset": "Sales",'
        ' "table": "exports"}'
    ),
    "view.export.sharepoint": (
        '{"tenant_id": "t", "client_id": "c", "client_secret": "s",'
        ' "site_url": "https://example.sharepoint.com/sites/x"}'
    ),
    "view.export.tableau": (
        '{"server_url": "https://tableau.example", "token_name": "t", "token_secret": "s"}'
    ),
    "connector.connection.create": '{"config": {"host": "db.example", "port": 5432}}',
    "connector.connection.update": '{"credentials": {"password": "secret"}}',
    "external-key.create": (
        '{"key_type": "open_ai", "key_name": "Team key", "secure_key": "sk-example"}'
    ),
    "file.set-password": '{"password": "secret"}',
    "workspace.accept-invite": '{"token": "invite-token"}',
}

_FILE_NAME = re.compile(r"\./[\w.-]+\.(?:csv|pdf|png|zip)")
_FILE_ARGUMENT = re.compile(r"^[\w./-]+\.(csv|pdf|png|zip|twbx|pbix|xlsx)$")
_CONFIRM_HINT = re.compile(r"Pass --confirm (\S+?)\.?$")

_PROJECT = "1"
_WORKSPACE = 4

#: Paths a DELETE removed during the command being run; the sampled server then 404s them.
_DELETED: set[str] = set()

#: Export lists a POST added an export to, and the export it added (it has run and succeeded).
_EXPORTS = "/pipeline/exports"
_ADDED_EXPORTS: dict[str, dict[str, Any]] = {}
_NEW_EXPORT = {
    "id": 5,
    "status": "executed",
    "error_info": None,
    "execution_end_time": "2026-01-01T00:00:00Z",
}

#: Column renames a PATCH applied to a dataview ({internal name: new display name}).
_RENAMED: dict[str, str] = {}

#: The columns of every sampled dataview, so the examples' column names resolve.
_VIEW_COLUMNS = {
    "Status": "TEXT",
    "Region": "TEXT",
    "Product": "TEXT",
    "Name": "TEXT",
    "cust_id": "TEXT",
    "Revenue": "NUMERIC",
    "Cost": "NUMERIC",
    "price": "NUMERIC",
    "quantity": "NUMERIC",
    "Customer ID": "NUMERIC",
    "Q1": "NUMERIC",
    "Q2": "NUMERIC",
    "Q3": "NUMERIC",
    "Order Date": "DATE",
    "Admitted": "DATE",
    "Ship Date": "DATE",
}


#: A background job that has finished, and what an export's job reports when it has.
_FINISHED_JOB = {
    "id": 11,
    "status": "success",
    "response": {"url": "https://example.com/export.csv", "trigger_id": 5},
    "last_updated_at": "2026-01-01T00:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "path": "/jobs/11",
    "operation": "export",
}


def _resource_with_dataset(sample: dict[str, Any]) -> dict[str, Any]:
    """Give a sampled resource row the parent dataset reference a dataview row carries."""
    return {**sample, "resource": {**sample["resource"], "dataset": {"id": 456, "name": "Sales"}}}


def _folders_with_integer_parents(sample: dict[str, Any]) -> dict[str, Any]:
    """Give every sampled folder an integer parent, as the folders route does."""
    folders = [{**folder, "parent_id": 1} for folder in sample["folders"]]
    return {**sample, "folders": folders}


#: What replaces fields of a sampled response, by operation id: the fields to set, or a
#: function from the OpenAPI sample to the response. Used where the spec leaves a field
#: out (an empty ``200``), or the SDK's model needs a value the sampler cannot know.
_SAMPLE_OVERRIDES: dict[str, dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any]]] = {
    "GetDataviewInformationIndividual": {
        "id": 123,
        "ds_id": 456,
        "user_display_properties": {
            "EXPLORE_PANEL": {
                "height": 300,
                "cards": [card_for_column("column_0000000001", "TEXT")],
            }
        },
        "pipeline_status": "ready",
        "is_pipeline_running": False,
        "metadata": [
            {
                "name": f"column_{index:010d}",
                "internal_name": f"column_{index:010d}",
                "display_name": name,
                "type": kind,
            }
            for index, (name, kind) in enumerate(_VIEW_COLUMNS.items())
        ],
    },
    "AddDataview": {"id": 124},
    "GetResource": _resource_with_dataset,
    "ListFolders": _folders_with_integer_parents,
    "GetCurrentWorkspace": {"id": _WORKSPACE},
    "AgentChat": {"session_id": "sess-1", "turn_id": "turn-1"},
    "DuplicateDashboard": {"id": 2},
    "AddPages": {"sequence": 2, "bake_job_id": 9},
    "Suggest": {"id": 7},
    "AddExport": {"trigger_id": 5, "future_id": 11, "job": _FINISHED_JOB},
    "GetJob": {"job": _FINISHED_JOB},
    "TrashFolder": {"job": _FINISHED_JOB},
    "CreateBlankDashboard": {"id": 2},
    "UpdateFolderDetails": lambda sample: {"folder": {**sample["folder"], "parent_id": 1}},
    "GetCanvasDraft": lambda sample: {
        **sample,
        "canvas": {**sample["canvas"], "filters": [{"field": "example", "control": "multi"}]},
    },
}


def _operation_templates() -> list[tuple[str, re.Pattern[str], str]]:
    """List every OpenAPI operation as (method, path pattern, operation id).

    Returns:
        The operations, those with the fewest path parameters first so that a literal
        path such as ``/dashboards/email-updates`` wins over ``/dashboards/{id}``.
    """
    found = []
    for path, item in openapi_types._document().get("paths", {}).items():
        pattern = re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", path) + "$")
        for method, operation in item.items():
            if isinstance(operation, dict) and operation.get("operationId"):
                found.append((method.upper(), pattern, operation["operationId"]))
    found.sort(key=lambda entry: entry[1].pattern.count("[^/]+"))
    return found


_OPERATIONS = _operation_templates()


_STRING_FORMATS = {
    "date": "2026-01-01",
    "date-time": "2026-01-01T00:00:00Z",
    "email": "agent@example.com",
    "uuid": "00000000-0000-4000-8000-000000000001",
    "uri": "https://example.com",
}


def _full_sample(
    node: dict[str, Any], defs: dict[str, Any], seen: frozenset[str] = frozenset()
) -> Any:
    """Build a value for a schema with every property filled in.

    A sample with only the required keys would leave the SDK's typed models to dump their
    optional fields as ``null``, which a real server's response does not.

    Args:
        node: The schema node.
        defs: The schema's shared ``$defs``.
        seen: The ``$ref`` names being expanded, to stop a recursive schema.

    Returns:
        A JSON value the node accepts.
    """
    if "const" in node:
        return node["const"]
    if node.get("enum"):
        return node["enum"][0]
    ref = node.get("$ref")
    if isinstance(ref, str):
        name = ref.rsplit("/", 1)[-1]
        if name in seen:
            return {}
        return _full_sample(defs.get(name, {}), defs, seen | {name})
    if node.get("allOf"):
        merged: dict[str, Any] = {}
        for member in node["allOf"]:
            value = _full_sample(member, defs, seen)
            if isinstance(value, dict):
                merged.update(value)
        return merged
    for key in ("oneOf", "anyOf"):
        if node.get(key):
            return _full_sample(node[key][0], defs, seen)
    kind = node.get("type")
    if isinstance(kind, list):
        kind = next((item for item in kind if item != "null"), "null")
    if kind == "object" or "properties" in node:
        return {
            name: _full_sample(child, defs, seen)
            for name, child in node.get("properties", {}).items()
        }
    if kind == "array":
        return [_full_sample(node.get("items", {}), defs, seen)]
    scalars: dict[str | None, Any] = {"integer": 1, "number": 1.5, "boolean": True, "null": None}
    if kind in scalars:
        return scalars[kind]
    return _STRING_FORMATS.get(node.get("format"), "example")


def _spec_sample(method: str, endpoint: str) -> Any:
    """Build the response a spec-conforming server would give for one request.

    Args:
        method: HTTP method.
        endpoint: Request path, with or without a query string.

    Returns:
        A sample of the operation's ``200`` schema, or ``{}`` when the path is unknown.
    """
    path = "/" + endpoint.lstrip("/").split("?")[0]
    for verb, pattern, operation_id in _OPERATIONS:
        if verb == method.upper() and pattern.match(path):
            schema = openapi_response_schema_for((operation_id,))
            sample = _full_sample(schema, schema.get("$defs", {})) if schema else {}
            override = _SAMPLE_OVERRIDES.get(operation_id)
            if callable(override):
                return override(sample)
            if isinstance(sample, dict) and override:
                sample.update(override)
            return sample
    return {}


def _any_of(node: Any) -> Any:
    """Read every ``oneOf`` of a schema as ``anyOf``.

    The OpenAPI document uses ``oneOf`` over branches that overlap (a string and a
    date-time string, an IPv4 and an IPv6 address); a value that fits one of them is what
    it means, and ``oneOf`` would reject it for fitting two.

    Args:
        node: A schema, or part of one.

    Returns:
        A copy with ``oneOf`` renamed.
    """
    if isinstance(node, dict):
        return {("anyOf" if key == "oneOf" else key): _any_of(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_any_of(item) for item in node]
    return node


def _declared() -> list[dict[str, Any]]:
    return sorted(
        (record for record in load_commands() if record.get("output_schema")),
        key=lambda record: record["command_id"],
    )


def _invoke(argv: list[str]) -> dict[str, Any]:
    """Run one CLI call and parse its JSON envelope.

    Args:
        argv: The arguments after ``mammoth``.

    Returns:
        The parsed envelope, or ``{"error": ...}`` when the output was not an envelope.
    """
    text = make_runner().invoke(argv).output.strip()
    decoder = json.JSONDecoder()
    envelope: dict[str, Any] = {"error": {"code": "not_json"}}
    position = text.find("{")
    # A command that streams (``run``, ``recipe run``) prints one envelope per step, then its own.
    while 0 <= position < len(text):
        try:
            envelope, end = decoder.raw_decode(text, position)
        except ValueError:
            return {"error": {"code": "not_json"}}
        position = text.find("{", end)
    return envelope


def _prepare_files(argv: list[str], command_id: str, workdir: Path) -> list[str]:
    """Create the local files an example names, so the handler finds them.

    Args:
        argv: The example's arguments.
        command_id: The command being run.
        workdir: The directory the command runs in.

    Returns:
        ``argv`` with an ``--input`` path that does not exist pointed at a request document
        (``_REQUEST_DOCUMENTS``) written to ``workdir``.
    """
    prepared = list(argv)
    for named in _FILE_NAME.findall(" ".join(prepared)):
        (workdir / named).parent.mkdir(parents=True, exist_ok=True)
        (workdir / named).write_bytes(b"a,b\n1,2\n")
    for index, token in enumerate(prepared):
        if token == "./sales":
            (workdir / "sales").mkdir(exist_ok=True)
            (workdir / "sales" / "a.csv").write_bytes(b"a,b\n1,2\n")
        if _FILE_ARGUMENT.match(token):
            (workdir / token).parent.mkdir(parents=True, exist_ok=True)
            (workdir / token).write_bytes(b"a,b\n1,2\n")
        if token == "--input" and index + 1 < len(prepared):
            value = prepared[index + 1]
            if not value.lstrip().startswith(("{", "[", "-", "@")) and not Path(value).exists():
                document = workdir / "request.json"
                document.write_text(_REQUEST_DOCUMENTS.get(command_id, "{}"), encoding="utf-8")
                prepared[index + 1] = str(document)
    return prepared


def _run(record: dict[str, Any], workdir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Run a command's manifest example and return its JSON envelope.

    The run is a real one, signed in with a fresh profile. A write is confirmed with
    ``--yes``, and with ``--confirm`` of the target the CLI names when it asks for one; a
    command that takes neither (a local one) is run without.

    Args:
        record: The command's manifest record.
        workdir: The directory the command runs in.
        dry_run: Run it with ``--dry-run``, which reports the request instead of making it.

    Returns:
        The parsed envelope, or ``{"error": ...}`` when the output was not an envelope.
    """
    login_default_profile()
    _DELETED.clear()
    _ADDED_EXPORTS.clear()
    _RENAMED.clear()
    command_id = record["command_id"]
    argv = shlex.split(_EXAMPLES.get(command_id, record["agent_example"]))[1:]
    argv = _prepare_files(argv, command_id, workdir)
    argv += ["--output", "json", "--no-input", "--project", _PROJECT]
    if dry_run:
        argv.append("--dry-run")
    if record["mutation_class"] != "read":
        argv.append("--yes")
    envelope = _invoke(argv)
    error = envelope.get("error") or {}
    if error.get("code") == "unknown_option" and "--yes" in argv:
        argv.remove("--yes")
        return _invoke(argv)
    hint = _CONFIRM_HINT.search(error.get("hint") or "")
    if error.get("code") == "confirmation_target_mismatch" and hint:
        if "--confirm" in argv:
            at = argv.index("--confirm")
            del argv[at : at + 2]
        return _invoke([*argv, "--confirm", hint.group(1)])
    return envelope


def _deleted_paths(path: str, request: dict[str, Any]) -> set[str]:
    """The item paths a DELETE removes: the path itself, or ``path/ID`` per id it lists.

    Args:
        path: Request path.
        request: The request's keyword arguments (``params``, ``json``).

    Returns:
        The paths of the removed items.
    """
    listed: set[str] = set()
    for source in (request.get("params"), request.get("json")):
        for key, value in (source or {}).items():
            if key.endswith("ids"):
                items = value.split(",") if isinstance(value, str) else value
                listed |= {f"{path}/{item}" for item in items}
    return listed or {path}


def _without_deleted(path: str, sample: Any, deleted: set[str]) -> Any:
    """Leave out of a sampled list the items an earlier DELETE removed.

    Args:
        path: Request path of the list.
        sample: The sampled response.
        deleted: Paths of the removed items.

    Returns:
        ``sample``, its lists without the removed items.
    """
    if not isinstance(sample, dict):
        return sample
    return {
        key: (
            [item for item in value if f"{path}/{item.get('id')}" not in deleted]
            if isinstance(value, list) and all(isinstance(item, dict) for item in value)
            else value
        )
        for key, value in sample.items()
    }


def _with_added_export(method: str, path: str, sample: Any) -> Any:
    """Show the export a POST added: in the view's export list, and as its own route.

    Args:
        method: HTTP method.
        path: Request path.
        sample: The sampled response.

    Returns:
        ``sample`` with the added export in the list, or as the item, once one was added.
    """
    if method.upper() != "GET" or not isinstance(sample, dict):
        return sample
    if path in _ADDED_EXPORTS:
        added = {**_NEW_EXPORT, **_ADDED_EXPORTS[path]}
        return {**sample, "exports": [*sample["exports"], {**sample["exports"][0], **added}]}
    parent, _, export_id = path.rpartition("/")
    if parent in _ADDED_EXPORTS and export_id == str(_NEW_EXPORT["id"]):
        return {**sample, **_NEW_EXPORT, **_ADDED_EXPORTS[parent]}
    return sample


def _renames(body: Any) -> dict[str, str]:
    """The column renames a dataview PATCH body asks for ({internal name: new name})."""
    renames: dict[str, str] = {}
    patch = body.get("patch") if isinstance(body, dict) else None
    for operation in patch if isinstance(patch, list) else []:
        if (
            isinstance(operation, dict)
            and operation.get("path") == "display_properties/COLUMN_NAMES"
        ):
            renames.update(operation.get("value") or {})
    return renames


def _with_renames(method: str, path: str, sample: Any) -> Any:
    """Show the renames a PATCH applied in the view's display properties on the next read."""
    if method.upper() != "GET" or not _RENAMED or not isinstance(sample, dict):
        return sample
    if "metadata" not in sample:
        return sample
    properties = {**(sample.get("display_properties") or {}), "COLUMN_NAMES": dict(_RENAMED)}
    return {**sample, "display_properties": properties}


def sampled_server(monkeypatch: pytest.MonkeyPatch, workdir: Path) -> None:
    """Replace the HTTP layer with spec-built responses, in a signed-in, isolated CLI.

    Args:
        monkeypatch: The test's monkeypatch.
        workdir: The directory the commands run in.
    """
    login_default_profile()
    monkeypatch.chdir(workdir)

    async def fake_request(self: Any, method: str, endpoint: str, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("expected_response_shape") == "binary":
            return _BINARY_BODY
        path = "/" + endpoint.lstrip("/").split("?")[0]
        if method.upper() == "DELETE":
            _DELETED.update(_deleted_paths(path, kwargs))
        elif path in _DELETED:
            raise MammothAPIError("Not found", status_code=404)
        elif method.upper() == "POST" and path.endswith(_EXPORTS):
            target = (kwargs.get("json") or {}).get("target_properties")
            extra = {"target_properties": {**target, "TARGET_DS_ID": 456}} if target else {}
            _ADDED_EXPORTS[path] = extra
        elif method.upper() == "PATCH":
            _RENAMED.update(_renames(kwargs.get("json")))
        sample = _without_deleted(path, _spec_sample(method, endpoint), _DELETED)
        return _with_renames(method, path, _with_added_export(method, path, sample))

    async def fake_download(self: Any, url: str, output_path: Path, **_kwargs: Any) -> Path:
        output_path.write_bytes(b"a,b\n1,2\n")
        return output_path

    monkeypatch.setattr(MammothClient, "_request", fake_request)
    monkeypatch.setattr(ExportsAPI, "_download_file", fake_download)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_args, **_kwargs: _WORKSPACE)
    # The sampled exports list is never "settled": do not wait for the backend's re-check.
    monkeypatch.setattr(verify, "_EXPORT_SETTLE_S", 0.0)


def test_declared_outputs_match_their_schemas(
    monkeypatch: pytest.MonkeyPatch,
    isolated_cli_config: Path,
    block_real_network: None,
    tmp_path: Path,
) -> None:
    sampled_server(monkeypatch, tmp_path)

    failures: list[str] = []
    unexercised: list[str] = []
    exercised = {"read": 0, "write": 0}
    for record in _declared():
        if record["command_id"] in _UNSAMPLABLE or record["command_id"] in _EXEMPT:
            continue
        envelope = _run(record, tmp_path)
        if "error" in envelope or "data" not in envelope:
            if record["mutation_class"] != "read":
                unexercised.append(record["command_id"])
            continue
        schema = output_schema(record)
        assert schema is not None, record["command_id"]
        errors = list(
            jsonschema.Draft202012Validator(_any_of(schema)).iter_errors(envelope["data"])
        )
        if errors:
            failures.append(f"{record['command_id']}: {errors[0].message[:200]}")
        exercised["read" if record["mutation_class"] == "read" else "write"] += 1

    assert not failures, "\n".join(failures)
    assert exercised["read"] >= FLOOR_READS, exercised
    assert not unexercised, f"writes that did not run (add to _EXEMPT with a reason): {unexercised}"
    # Every declared command is either run above or named, with its reason, in ``_EXEMPT``.
    assert set(_EXEMPT) <= {record["command_id"] for record in _declared()}


def test_a_dry_run_report_matches_the_dry_run_schema(
    monkeypatch: pytest.MonkeyPatch,
    isolated_cli_config: Path,
    block_real_network: None,
    tmp_path: Path,
) -> None:
    """``--dry-run`` returns ``DryRunReport`` for an API-backed write, not the real ``data``."""
    sampled_server(monkeypatch, tmp_path)

    failures: list[str] = []
    reports = 0
    for record in _declared():
        if record["mutation_class"] == "read" or record["command_id"] in _DRY_RUN_SKIPPED:
            continue
        envelope = _run(record, tmp_path, dry_run=True)
        data = envelope.get("data")
        if not isinstance(data, dict) or "would_call" not in data:
            continue
        schema = dry_run_output_schema(record)
        assert schema is not None, record["command_id"]
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(data))
        if errors:
            failures.append(f"{record['command_id']}: {errors[0].message[:200]}")
        reports += 1

    assert not failures, "\n".join(failures)
    assert reports >= FLOOR_DRY_RUNS, reports


#: What each exempt command returns, as its handler builds it (the runtime's ``verify`` block
#: added), for the commands whose example cannot run: the schema must accept it.
_VERIFY = {
    "verified": True,
    "state": "ok",
    "warnings": [],
    "reason": None,
    "needs_user": False,
    "outcome": "settled",
}
_EXEMPT_RESULTS: dict[str, dict[str, Any]] = {
    "dataset.update": {"verify": _VERIFY},
    "schedule.create": {"id": 3, "verify": _VERIFY},
    "view.export.dataset": {"dataset_id": 9, "verify": _VERIFY},
    "view.draft.auto-run": {"auto_run": True, "verify": _VERIFY},
    "history.undo": {
        "id": "g1",
        "dry_run": False,
        "undone": [{"inv": "a", "command": "dataset.trash", "steps": []}],
        "not_undoable": [{"inv": "c", "command": "dataset delete", "reason": "permanent"}],
        "outcome": "undone",
        "verify": _VERIFY,
    },
    "history.resume": {
        "resumed": "g9",
        "from_line": 2,
        "lines": 3,
        "ok": 2,
        "failed": 0,
        "skipped": 1,
        "stopped_at": None,
        "failed_lines": [],
        "continue": False,
        "dry_run": False,
        "exit": 0,
        "verify": _VERIFY,
    },
}


def test_an_exempt_command_result_matches_its_schema() -> None:
    assert set(_EXEMPT_RESULTS) == set(_EXEMPT)
    for command_id, data in _EXEMPT_RESULTS.items():
        schema = output_schema(command_by_id(command_id) or {})
        assert schema is not None, command_id
        errors = list(jsonschema.Draft202012Validator(_any_of(schema)).iter_errors(data))
        assert not errors, f"{command_id}: {errors[0].message[:200]}"
