"""Basic ``view export`` handlers (create, csv, list, runs, publish-db, update ...)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _DATASET_ID_FIELD,
    _forward_optional,
    _int_positional_at,
    _meta,
    _page_offset,
    _profile_name,
    _require_exact_parent,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
)
from mammoth_cli.commands.view.export_specialized import (
    _reject_unacknowledged_table_replace,
    _with_recurrence_note,
)
from mammoth_cli.commands.view.pipeline import (
    _with_list_paging,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime import embedded, parents
from mammoth_cli.runtime.confirm import (
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    DEFAULT_MUTATION_JOB_TIMEOUT,
    open_service,
    require_project,
)
from mammoth_cli.services.local_files import refuse_existing_file


def view_export_create(invocation: Invocation) -> HandlerResult:
    """Create an export for a dataview. ``export_spec`` required. Always ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    export_spec = _require_field(document, "export_spec")
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"create an export on view {dataview_id}"
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_spec": export_spec,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_csv(invocation: Invocation) -> HandlerResult:
    """Export a dataview to a local CSV file.

    With no --input the file is written to the current directory under an
    auto-generated name; the dataset is resolved from the view. Override with
    ``--input '{"output_path": "path.csv"}'``. An existing file is not replaced
    (``file_exists``) unless ``--overwrite`` is given.

    Embedded (see ``mammoth_cli.runtime.embedded``), no file is written: the
    signed download URL is returned instead so the host can hand it to its
    user. ``output_path`` is refused in that case.
    """
    return _download_dataview(
        invocation, "mammoth.api.exports.ExportsAPI.to_csv_url", ("output_path", "timeout")
    )


def view_export_download(invocation: Invocation) -> HandlerResult:
    """Download a dataview to a local file as csv, xlsx, json, ndjson, xml, yaml or parquet.

    Same as ``view export csv`` otherwise: ``--input '{"file_type": "xlsx", "output_path":
    "out.xlsx"}'``; the default name carries the format's extension; an existing file is not
    replaced unless ``--overwrite``; embedded, the signed download URL is returned instead.
    """
    return _download_dataview(
        invocation,
        "mammoth.api.exports.ExportsAPI.to_file_url",
        ("output_path", "file_type", "timeout"),
    )


def _download_dataview(
    invocation: Invocation, embedded_symbol: str, fields: tuple[str, ...]
) -> HandlerResult:
    """Shared body of ``view export csv`` and ``view export download``."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    if embedded.active():
        return _view_export_csv_embedded(invocation, dataview_id, document, embedded_symbol)
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, (*fields, "dataset_id"))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        # The SDK's own default name needs the parent dataset, which is known here.
        target = kwargs.get("output_path")
        if target is None and kwargs.get(_DATASET_ID_FIELD) is not None:
            extension = str(kwargs.get("file_type") or "csv").strip().lower().lstrip(".")
            target = f"dataview_{kwargs[_DATASET_ID_FIELD]}_{dataview_id}_export.{extension}"
        if target is not None:
            refuse_existing_file(invocation, target)
        data = service.call(_symbol(invocation), **kwargs)
    # The SDK returns a Path; render it as a string so the written location is
    # visible in every output mode and serializes cleanly to JSON.
    return {"output_path": str(data)}, _meta(invocation, auth.workspace_id, None)


def _view_export_csv_embedded(
    invocation: Invocation, dataview_id: int, document: dict[str, Any], symbol: str
) -> HandlerResult:
    """A download for an embedded call: never writes a local file."""
    if "output_path" in document:
        raise CliError(
            code=CODE_UNSUPPORTED_CONTRACT,
            message="output_path is not supported here; files are not written in embedded mode.",
            exit_status=EXIT_USAGE,
            hint="Drop output_path -- an embedded call returns a download_url instead.",
        )
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("file_type", "timeout", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(symbol, **kwargs)
    return {"download_url": data["url"]}, _meta(invocation, auth.workspace_id, None)


def view_export_delete(invocation: Invocation) -> HandlerResult:
    """Delete one export by id. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"delete export {export_id} of view {dataview_id}",
    )
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("skip_validation", "dataset_id"))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_get(invocation: Invocation) -> HandlerResult:
    """Get one export by id."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_list(invocation: Invocation) -> HandlerResult:
    """List exports for a dataview, with optional filters from ``--input``."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    dataset_id = _int_positional_at(invocation, 1, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(
        document,
        kwargs,
        (
            "fields",
            "limit",
            "offset",
            "sort",
            "sequence",
            "status",
            "reordered",
            "handler_type",
            "end_of_pipeline",
            "runnable",
            "dataset_id",
        ),
    )
    if "offset" in kwargs:
        kwargs["offset"] = _page_offset(kwargs["offset"])
    if dataset_id is not None:
        kwargs["dataset_id"] = dataset_id
    with open_service(invocation) as (service, auth):
        if kwargs.get("dataset_id") is None:
            # A remembered parent spares the SDK its scan of every dataset.
            remembered = parents.lookup(_profile_name(invocation), auth.workspace_id, dataview_id)
            if remembered is not None:
                kwargs["dataset_id"] = remembered
        data = service.call(_symbol(invocation), **kwargs)
    data = _with_list_paging(
        data, invocation, f"mammoth view export list {dataview_id}", kwargs, "exports", 50
    )
    return data, _meta(invocation, auth.workspace_id, None)


def view_export_runs(invocation: Invocation) -> HandlerResult:
    """Get the run history of one export, newest first: when, rows, destination, errors."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    dataset_id = _int_positional_at(invocation, 2, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("limit", "dataset_id"))
    if dataset_id is not None:
        kwargs["dataset_id"] = dataset_id
    with open_service(invocation) as (service, auth):
        if kwargs.get("dataset_id") is None:
            # A remembered parent spares the SDK its scan of every dataset.
            remembered = parents.lookup(_profile_name(invocation), auth.workspace_id, dataview_id)
            if remembered is not None:
                kwargs["dataset_id"] = remembered
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_rest_fill(invocation: Invocation) -> HandlerResult:
    """Propose REST API export settings from an API docs page. Always requires ``--yes``.

    Mammoth's server fetches ``docs_url`` and reads it to propose the form values (never
    credentials). Nothing is configured or sent: the result is a suggestion to review.
    It always waits for the job, for at most ``--job-timeout`` seconds.
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    docs_url = _require_field(document, "docs_url")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"have Mammoth read {docs_url} to propose REST settings for view {dataview_id}",
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "docs_url": docs_url,
        "project_id": project_id,
        "wait": True,
        "timeout": invocation.job_timeout or DEFAULT_MUTATION_JOB_TIMEOUT,
    }
    _forward_optional(document or {}, kwargs, ("notes", "dataset_id"))
    explicit_dataset = _int_positional_at(invocation, 1, "dataset id")
    if explicit_dataset is not None:
        kwargs["dataset_id"] = explicit_dataset
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        job = service.call(_symbol(invocation), **kwargs)
    data = dict(job) if isinstance(job, dict) else {"job": job}
    response = data.get("response")
    if isinstance(response, dict) and response.get("suggestion") is not None:
        data["suggestion"] = response["suggestion"]
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_summary(invocation: Invocation) -> HandlerResult:
    """What a view has had done to it and where it goes: steps, actions, exports, dashboards."""
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    if view_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT, message="view id must be positive.", exit_status=EXIT_USAGE
        )
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=view_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_publish_db(invocation: Invocation) -> HandlerResult:
    """Publish a dataview to a database endpoint. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    odbc_type = _require_field(document, "odbc_type")
    target_properties = _require_field(document, "target_properties")
    assert document is not None
    table = target_properties.get("table") if isinstance(target_properties, dict) else None
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"publish-db on view {dataview_id}"
    )
    table_note = _reject_unacknowledged_table_replace(invocation.command_id, document, table)
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "odbc_type": odbc_type,
        "target_properties": target_properties,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    if table_note is not None:
        data = _with_recurrence_note(data, table_note)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_publish_db_update(invocation: Invocation) -> HandlerResult:
    """Patch a dataview's published database endpoint. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    patch = _require_field(document, "patch")
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"publish-db-update on view {dataview_id}"
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "patch": patch,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_update(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to an export. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    export_id = _require_int_positional_at(invocation, 1, "export id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update export {export_id} of view {dataview_id}",
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "export_id": export_id,
        "patches": patches,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("skip_validation", "dataset_id"))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# Typed ViewExport convenience routes
# ---------------------------------------------------------------------------
