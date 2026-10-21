"""Specialized ``view export`` handler and its safety guards."""

from __future__ import annotations

import inspect
from typing import Any

from mammoth_cli.commands.view._common import (
    _DATASET_ID_FIELD,
    HandlerResult,
    _int_positional_at,
    _meta,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id,
)
from mammoth_cli.commands.view.export_dataset import (
    _hidden_column_names,
    _new_dataset_facts,
    _pending_dataset_export,
    _reject_append_schema_mismatch,
    reject_dataset_export_conflicts,
)
from mammoth_cli.commands.view.settle import (
    _dataset_view_info,
    _view_info_after_settling,
)
from mammoth_cli.errors.envelope import (
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.runtime.verify import export_wait_budget, read_export_ids, wait_export_run
from mammoth_cli.services.append_blank_columns import (
    BLANK_COLUMNS_FIELD,
    acknowledged_blank_columns,
)

# The SDK exposes these destinations as typed helpers on ``View.export``.  A
# generic ``view export create`` cannot stand in for them: the helpers have
# destination-specific required fields, secret handling, and safety policy.
# Keep the allow-list here deliberately closed so a misspelled input field can
# never silently become an arbitrary ``**kwargs`` export option.
_SPECIAL_EXPORTS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "view.export.dataset": (
        "to_dataset",
        (),
        (),
    ),
    "view.export.managed-s3": ("to_s3", (), ()),
    "view.export.live-link": ("to_live_link", (), ()),
    "view.export.azure-blob": (
        "to_azure_blob",
        ("storage_account_name", "tenant_id", "client_id", "client_secret", "container_name"),
        ("client_secret",),
    ),
    "view.export.bigquery": (
        "to_bigquery",
        ("selected_profile", "selected_identity", "table"),
        (),
    ),
    "view.export.elasticsearch": (
        "to_elasticsearch",
        ("host", "username", "password", "index"),
        ("password",),
    ),
    "view.export.email": ("to_email", ("emails",), ()),
    "view.export.ftp": (
        "to_ftp",
        ("domain", "directory", "file", "username", "password"),
        ("password",),
    ),
    "view.export.mssql": (
        "to_mssql",
        ("host", "port", "database", "table", "username", "password"),
        ("password",),
    ),
    "view.export.mysql": (
        "to_mysql",
        ("host", "port", "database", "table", "username", "password"),
        ("password",),
    ),
    "view.export.onedrive": (
        "to_onedrive",
        ("tenant_id", "client_id", "client_secret", "user_id"),
        ("client_secret",),
    ),
    "view.export.postgres": (
        "to_postgres",
        ("host", "port", "database", "table", "username", "password"),
        ("password",),
    ),
    "view.export.powerbi": (
        "to_powerbi",
        ("username", "password", "client_id", "dataset", "table"),
        ("password",),
    ),
    "view.export.redshift": (
        "to_redshift",
        ("host", "port", "database", "table", "username", "password"),
        ("password",),
    ),
    "view.export.rest": ("to_rest_api", ("base_url", "endpoint_path"), ("auth",)),
    "view.export.sftp": (
        "to_sftp",
        ("host", "username"),
        ("password", "private_key", "passphrase"),
    ),
    "view.export.sharepoint": (
        "to_sharepoint",
        ("tenant_id", "client_id", "client_secret", "site_url"),
        ("client_secret",),
    ),
    "view.export.tableau": (
        "to_tableau",
        ("server_url", "token_name", "token_secret"),
        ("token_secret",),
    ),
}

# The SDK helpers all expose ``**kwargs`` for the common export trigger
# controls.  These are the reviewed common controls accepted by every typed
# route. Destination-specific fields are added from ``_SPECIAL_EXPORTS``.
_SPECIAL_EXPORT_COMMON_FIELDS = frozenset(
    {
        "trigger_type",
        "run_immediately",
        "validate_only",
        "end_of_pipeline",
        "additional_properties",
        "condition",
    }
)


# Database exports rebuild their destination table: the distributary drops it
# and recreates it from the view on the first write and on every later pipeline
# run (BigQuery only for export_type REPLACE, its WRITE_TRUNCATE mode). Postgres
# and MySQL also cut a table name to 60 characters, silently writing elsewhere.
_REPLACE_TABLE_FIELD = "replace_table"
_DB_REPLACE_ROUTES = frozenset(
    {
        "view.export.postgres",
        "view.export.mysql",
        "view.export.mssql",
        "view.export.redshift",
        "view.export.bigquery",
    }
)
_DB_TABLE_NAME_LIMIT_ROUTES = frozenset({"view.export.postgres", "view.export.mysql"})
_DB_TABLE_NAME_LIMIT = 60


def _replaces_table(command_id: str, document: dict[str, Any]) -> bool:
    """Whether this database export drops and recreates its destination table."""
    if command_id == "view.export.bigquery":
        return str(document.get("export_type") or "REPLACE").upper() == "REPLACE"
    return command_id in _DB_REPLACE_ROUTES or command_id == "view.export.publish-db"


def _reject_unacknowledged_table_replace(
    command_id: str, document: dict[str, Any], table: Any
) -> str | None:
    """Refuse a database export that is not explicitly allowed to replace its table.

    Returns the recurrence note for the result, or ``None`` when the export
    does not replace a table.
    """
    if not _replaces_table(command_id, document):
        return None
    name = str(table)
    if command_id in _DB_TABLE_NAME_LIMIT_ROUTES and len(name) > _DB_TABLE_NAME_LIMIT:
        raise CliError(
            code="table_name_too_long",
            message=(
                f"Table name {name!r} is {len(name)} characters; the database export cuts "
                f"table names to {_DB_TABLE_NAME_LIMIT} and would write a different table "
                f"({name[:_DB_TABLE_NAME_LIMIT]!r})."
            ),
            exit_status=EXIT_USAGE,
            hint=f"Use a table name of at most {_DB_TABLE_NAME_LIMIT} characters.",
            details={"table": name, "length": len(name), "limit": _DB_TABLE_NAME_LIMIT},
        )
    if document.get(_REPLACE_TABLE_FIELD) is not True:
        raise CliError(
            code="replace_table_not_acknowledged",
            message=(
                f"This export drops and recreates table {name!r} in the destination database "
                "now and on every pipeline run of the view; any existing table of that name "
                "and its rows are lost."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                f'Pick a table that may be overwritten, then add "{_REPLACE_TABLE_FIELD}": true '
                "to the input to confirm."
            ),
            details={"table": name, "field": _REPLACE_TABLE_FIELD},
        )
    return f"drops and recreates {name} now and on every pipeline run"


def _with_recurrence_note(data: Any, note: str) -> dict[str, Any]:
    """The export result as a mapping carrying ``refreshes_on_pipeline_run`` and ``note``."""
    result = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
    record = dict(result) if isinstance(result, dict) else {"result": result}
    record["refreshes_on_pipeline_run"] = True
    record["note"] = note
    return record


_PIPELINE_TRIGGER = "pipeline"
_JOB_WAIT_SYMBOL = "mammoth.api.jobs.JobsAPI.wait_for_job"
#: Exports whose add job already waits for the run: the S3 ones resolve it with the file's URL.
_EXPORT_JOB_WAITS_FOR_RUN = frozenset(
    {"view.export.dataset", "view.export.managed-s3", "view.export.live-link"}
)


def _waits_for_export_run(command_id: str, kwargs: dict[str, Any]) -> bool:
    """Whether this export saves a pipeline trigger whose run the command should wait for."""
    return (
        command_id not in _EXPORT_JOB_WAITS_FOR_RUN
        and not kwargs.get("validate_only")
        and kwargs.get("trigger_type", _PIPELINE_TRIGGER) == _PIPELINE_TRIGGER
    )


def _with_export_run(
    service: Any,
    data: Any,
    view: tuple[int, int, set[int]],
    kwargs: dict[str, Any],
    invocation: Invocation,
) -> dict[str, Any]:
    """The export result with ``export``: the saved export's run, waited for.

    The add job resolves before the backend runs a database export, so the result
    the SDK hands back says nothing of whether rows landed. The add job is waited for
    first: when it fails (the destination was refused) no export was saved, and its
    own error is the answer.
    """
    record = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
    result = dict(record) if isinstance(record, dict) else {"result": record}
    job = result.get("job")
    view_id, dataset_id, known_exports = view
    job_id = job.get("id") if isinstance(job, dict) else None
    if job_id is not None:
        service.call(_JOB_WAIT_SYMBOL, job_id=job_id)
    result["export"] = wait_export_run(
        service,
        view_id,
        dataset_id,
        known_ids=known_exports,
        budget=export_wait_budget(invocation),
        job_id=job_id,
        run_now=kwargs.get("run_immediately", True) is not False,
    )
    return result


def view_export_specialized(invocation: Invocation) -> HandlerResult:
    """Run one of the SDK's typed ``View.export`` destination helpers."""
    route = _SPECIAL_EXPORTS.get(invocation.command_id)
    if route is None:  # pragma: no cover - registry/manifest drift guard
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No typed export route is registered for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    method, required, _secrets = route
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    # The exact parent is optional for backwards compatibility; when supplied,
    # it is consumed as the trailing positional and scoped through call_view.
    dataset_id = _int_positional_at(invocation, 1, "dataset id")
    if dataset_id is None and document.get(_DATASET_ID_FIELD) is not None:
        dataset_id = int(document[_DATASET_ID_FIELD])
    # Explicit parameters come from the route's SDK signature. Only the six
    # reviewed trigger controls may flow through its **kwargs extension point;
    # using a union of every destination's fields would silently accept, for
    # example, email-only fields on a database export.
    from mammoth.view import ViewExport

    signature = inspect.signature(getattr(ViewExport, method))
    explicit_fields = {
        name
        for name, parameter in signature.parameters.items()
        if name != "self" and parameter.kind is not inspect.Parameter.VAR_KEYWORD
    }
    # The six common trigger controls only actually reach the SDK call when
    # the route's method has a **kwargs sink to carry them; ``to_dataset`` has
    # a closed signature (no **kwargs) and does not accept any of them.
    # Allowing them anyway let a field like ``end_of_pipeline`` pass this
    # check and then crash the call itself with an opaque "unexpected keyword
    # argument" TypeError instead of a clear unknown_input_field.
    accepts_var_keyword = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    common_fields = _SPECIAL_EXPORT_COMMON_FIELDS if accepts_var_keyword else frozenset()
    allowed = explicit_fields | common_fields | {_DATASET_ID_FIELD}
    if invocation.command_id in _DB_REPLACE_ROUTES:
        allowed = allowed | {_REPLACE_TABLE_FIELD}
    if invocation.command_id == "view.export.dataset":
        allowed = allowed | {BLANK_COLUMNS_FIELD}
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise CliError(
            code="unknown_input_field",
            message=(
                f"Unknown input field(s) for '{invocation.command_id.replace('.', ' ')}': "
                f"{', '.join(unknown)}. "
                f"Accepted fields: {', '.join(sorted(allowed - {_DATASET_ID_FIELD}))}."
            ),
            exit_status=EXIT_USAGE,
            hint=f"Accepted fields: {', '.join(sorted(allowed - {_DATASET_ID_FIELD}))}.",
            details={"unknown": unknown, "accepted": sorted(allowed - {_DATASET_ID_FIELD})},
        )
    for field in required:
        _require_field(document, field)
    # The manifest is the single source of truth for each destination's
    # confirmation policy (dataset export has no external effect and needs
    # none; every other destination is external_effect/yes_always). Deriving
    # it here, rather than hardcoding one policy for every route, keeps the
    # in-app agent's confirmation card (which reads the manifest) in sync
    # with what the CLI actually enforces.
    export_record = command_by_id(invocation.command_id) or {}
    enforce_confirmation(
        invocation,
        policy=str(export_record.get("confirmation") or POLICY_YES_ALWAYS),
        action=f"export view {dataview_id} via {invocation.command_id.rsplit('.', 1)[-1]}",
    )
    table_note = _reject_unacknowledged_table_replace(
        invocation.command_id, document, document.get("table")
    )
    kwargs = dict(document)
    kwargs.pop(_DATASET_ID_FIELD, None)
    kwargs.pop(_REPLACE_TABLE_FIELD, None)
    blank_columns = kwargs.pop(BLANK_COLUMNS_FIELD, None)
    is_dataset_route = invocation.command_id == "view.export.dataset"
    target_ds_id = kwargs.get("target_ds_id") if is_dataset_route else None
    save_as_mode = kwargs.get("save_as_mode") if is_dataset_route else None
    target_project = kwargs.get("target_project_id")
    result_project_id = int(target_project) if target_project is not None else project_id
    with open_service(invocation) as (service, auth):
        if dataset_id is None:
            dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        if is_dataset_route:
            reject_dataset_export_conflicts(
                service,
                dataview_id,
                dataset_id,
                int(target_ds_id) if target_ds_id is not None else None,
                save_as_mode=save_as_mode if isinstance(save_as_mode, str) else None,
            )
        target_view_before = None
        blank_warnings: list[str] = []
        target_only_columns: list[str] = []
        mapped_type_warnings: list[str] = []
        hidden_left_out = (
            _hidden_column_names(service, dataset_id, dataview_id, project_id)
            if is_dataset_route and target_ds_id is None
            else []
        )
        if target_ds_id is not None:
            # rows_before is the target's own count ahead of this write, read
            # before the call so a later re-read can never be confused with it.
            target_view_before = _dataset_view_info(service, int(target_ds_id), result_project_id)
            # REPLACE_IN_DS into an existing target runs the same backend
            # append code as APPEND_TO_DS (same mapping and schema handling),
            # so both modes get the same guards.
            target_only_columns, mapped_type_warnings = _reject_append_schema_mismatch(
                service,
                dataview_id,
                dataset_id,
                int(target_ds_id),
                kwargs.get("column_mapping"),
            )
            blank_warnings = acknowledged_blank_columns(
                int(target_ds_id), target_only_columns, blank_columns
            )
        waits_for_run = _waits_for_export_run(invocation.command_id, kwargs)
        known_exports = (
            read_export_ids(service, dataview_id, dataset_id) if waits_for_run else set()
        )
        try:
            data = service.call_view(dataview_id, method, dataset_id=dataset_id, **kwargs)
        except DryRunStop as stop:
            if is_dataset_route and target_ds_id is None:
                stop.record.update(_new_dataset_facts(kwargs.get("dataset_name"), hidden_left_out))
            raise
        except CliError as error:
            if not (is_dataset_route and error.details.get("export_pending")):
                raise
            return _pending_dataset_export(error, dataview_id, result_project_id), _meta(
                invocation, auth.workspace_id, project_id
            )
        if is_dataset_route and isinstance(data, int):
            # The SDK returns the bare id of the dataset written to; name it, and
            # say which project it landed in, so the agent's next read is obvious.
            # The written dataset's view id/name is resolved here too: an append
            # (save_as_mode=APPEND_TO_DS) never changes it, so telling the agent
            # to go re-list every time -- as a text-only 'next' hint used to --
            # cost one avoidable round trip per append to the same dataset. Best
            # effort: a failed lookup falls back to the old hint instead.
            data = {
                "dataset_id": data,
                "project_id": result_project_id,
                "source_view_id": dataview_id,
                # Every internal-dataset export is a pipeline trigger, not a
                # one-shot copy: it re-runs (and re-writes its own rows) every
                # time this view's pipeline runs.
                "refreshes_on_pipeline_run": True,
            }
            # A read immediately after the write can catch the pipeline still
            # recomputing; wait for it to settle (bounded) before trusting
            # the id/name/row_count, whether this is a brand-new dataset or
            # an existing target_ds_id -- this is the same race the old
            # "omit rather than report wrong" comment used to sidestep by
            # never reading the target's row count at all.
            view_info, pipeline_error = _view_info_after_settling(
                service,
                int(target_ds_id) if target_ds_id is not None else data["dataset_id"],
                result_project_id,
            )
            if view_info is not None:
                data["view_id"] = view_info["id"]
                data["view_name"] = view_info["name"]
            else:
                data["next"] = f"mammoth view list {data['dataset_id']}" + (
                    f" --project {result_project_id}" if target_project is not None else ""
                )
            # rows_before is None for a brand-new dataset (nothing else could
            # have written to it yet); for an existing target_ds_id it is the
            # count read above, ahead of this write.
            rows_before = (
                target_view_before["row_count"] if target_view_before is not None else None
            )
            rows_after = view_info["row_count"] if view_info is not None else None
            row_check: dict[str, Any] = {"rows_before": rows_before, "rows_after": rows_after}
            if save_as_mode == "APPEND_TO_DS":
                # An append is expected to grow the target; verify.py treats
                # a non-increase here as unverified, not just an omitted count.
                row_check["expected_row_increase"] = True
            warnings = list(mapped_type_warnings)
            if hidden_left_out:
                warnings.append(
                    "hidden column(s) of the source view are not in the new dataset: "
                    + ", ".join(hidden_left_out)
                )
            warnings[:0] = blank_warnings
            if warnings:
                row_check["warnings"] = warnings
            data["row_check"] = row_check
            if pipeline_error is not None:
                data["pipeline_error"] = pipeline_error
        if waits_for_run:
            data = _with_export_run(
                service, data, (dataview_id, dataset_id, known_exports), kwargs, invocation
            )
    if table_note is not None:
        data = _with_recurrence_note(data, table_note)
    return data, _meta(invocation, auth.workspace_id, project_id)
