"""Handlers for the ``dataset`` command family (project-scoped).

Every dataset operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and dataset ids come from a
positional argument or the strict ``--input`` document. Handlers dispatch
through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the public SDK method named by the command's reviewed manifest
``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.dataset._common import (
    _DATA_SYMBOL,
    _DATASET_GET_SYMBOL,
    _forward_optional,
    _meta,
    _require_field,
    _require_int_positional,
    _require_int_positional_at,
    _symbol,
)
from mammoth_cli.commands.dataset.find import (
    _find_by_name,
    _visible_projects,
    search_cut_note,
    search_hits,
)
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_API_ERROR,
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_RESOURCE_NOT_FOUND,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_API,
    EXIT_NOT_FOUND,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.new_data import with_file_upload_path
from mammoth_cli.runtime.session import open_service, require_project, resolved_project
from mammoth_cli.services.delete_check import ensure_deleted, ensure_unlisted, find_dependents
from mammoth_cli.services.listing import (
    DATASET_ROW_FIELDS,
    NAMES_DATA_BUDGET,
    NAMES_MAX_ROWS,
    dataset_summary,
    fit_budget,
    search_page,
)
from mammoth_cli.services.schema_diff import column_samples, schema_diff
from mammoth_cli.services.update_method import describe as describe_update_method
from mammoth_cli.services.update_method import parse_mode

#: The server's limits on a dataset definition (``DefinitionSpec`` in mvc-service).
_DEFINITION_LIMITS = {"term": 60, "definition": 300}


def _definitions_result(data: Any, dataset_id: int) -> dict[str, Any]:
    """``{dataset_id, definitions: [{id, term, definition}]}`` from the server's answer."""
    body = data if isinstance(data, dict) else {}
    definitions = [
        {"id": d.get("id"), "term": d.get("term"), "definition": d.get("definition")}
        for d in body.get("definitions") or []
        if isinstance(d, dict)
    ]
    return {"dataset_id": body.get("dataset_id", dataset_id), "definitions": definitions}


def _definition_text(document: dict[str, Any] | None, field: str) -> str:
    """A required ``--input`` string, stripped, within the server's length limit."""
    value = _require_field(document, field)
    text = value.strip() if isinstance(value, str) else ""
    limit = _DEFINITION_LIMITS[field]
    if not text or len(text) > limit:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The '{field}' input field must be text of 1 to {limit} characters.",
            exit_status=EXIT_USAGE,
        )
    return text


def dataset_definition_list(invocation: Invocation) -> HandlerResult:
    """List what terms mean for one dataset, as its users saved them."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return _definitions_result(data, dataset_id), _meta(invocation, auth.workspace_id, project_id)


def dataset_definition_add(invocation: Invocation) -> HandlerResult:
    """Save what a term means for a dataset (``term`` and ``definition`` from ``--input``).

    Shared by every chat on the dataset, so it always asks: ``--yes --confirm DATASET_ID``.
    A definition for the same term (any case) is replaced.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    term = _definition_text(document, "term")
    definition = _definition_text(document, "definition")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"save what '{term}' means for everyone using dataset {dataset_id}",
        target=str(dataset_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            term=term,
            definition=definition,
            project_id=project_id,
        )
    return _definitions_result(data, dataset_id), _meta(invocation, auth.workspace_id, project_id)


def dataset_definition_remove(invocation: Invocation) -> HandlerResult:
    """Remove one definition from a dataset by its id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    if len(invocation.extra_args) < 2 or not str(invocation.extra_args[1]).strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a definition id argument.",
            exit_status=EXIT_USAGE,
            hint="Pass the id from 'dataset definition list DATASET_ID' after the dataset id.",
        )
    definition_id = str(invocation.extra_args[1]).strip()
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"remove definition {definition_id} from dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            definition_id=definition_id,
            project_id=project_id,
        )
    return _definitions_result(data, dataset_id), _meta(invocation, auth.workspace_id, project_id)


def dataset_list(invocation: Invocation) -> HandlerResult:
    """List datasets in the active project, newest first, each with what tells them apart.

    Every item carries its created/updated time and how its data arrived (from the
    list route's ``sources``), cut to fit the agent tool output cap. The list asks
    only the cheap fields, so it holds no row counts or column names: ``view list
    DATASET_ID`` shows a dataset's columns, and ``dataset find --input '{"columns":
    [...]}'`` finds the dataset that has given columns.
    The result carries ``total``, the project's whole dataset count, so "how many
    datasets" never needs paging: read ``total`` with the first page's newest names.
    For a list of names (e.g. "which files can I see?") pass ``names: true``: ONE call
    returns up to 500 bare ``{id, name}`` rows, newest first, with ``total`` and ``more``.
    With no project set it returns ``{project_id, project_name, id, name}`` rows from every
    project the caller can open, from one workspace search (the newest 500 at most).
    ``full: true`` returns the raw ``{id, name}`` list instead. ``name`` keeps only datasets
    whose name contains it (case-insensitive) across every page, as short rows without
    column lists; ``limit``/``offset`` then page over the matches.
    """
    document = invocation.load_input() or {}
    name = document.get("name")
    wants_names = document.get("names") and not (isinstance(name, str) and name.strip())
    if wants_names and resolved_project(invocation) is None:
        return _dataset_names_everywhere(invocation)
    project_id = require_project(invocation)
    _validate_paging(document)
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "offset", "sort"))
    if wants_names:
        return _dataset_names(invocation, project_id, document)
    if isinstance(name, str) and name.strip():
        return _dataset_name_search(invocation, project_id, name.strip(), document)
    compact = not document.get("full")
    if compact:
        kwargs["fields"] = DATASET_ROW_FIELDS
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        if compact:
            data = _compact_dataset_list(
                data, kwargs.get("offset", 0), kwargs.get("sort"), kwargs.get("limit", 100)
            )
            if isinstance(data, dict) and "shown" in data:
                data["total"] = _dataset_total(service, project_id, data, kwargs.get("offset", 0))
    return data, _meta(invocation, auth.workspace_id, project_id)


def _dataset_names(
    invocation: Invocation, project_id: int, document: dict[str, Any]
) -> HandlerResult:
    """``dataset list`` with ``names``: every ``{id, name}`` of the project in one result.

    Capped at ``NAMES_MAX_ROWS`` rows and ``NAMES_DATA_BUDGET`` bytes; ``total`` is the whole
    count and ``more`` says the cap cut the list (``name`` then narrows it).
    """
    with open_service(invocation) as (service, auth):
        data = service.call(
            "mammoth.api.datasets.DatasetsAPI.list_all",
            project_id=project_id,
            sort=document.get("sort", "(created_at:desc)"),
            fields="id,name",
        )
    records = data.get("datasets", []) if isinstance(data, dict) else []
    rows = [{"id": r["id"], "name": r.get("name")} for r in records if isinstance(r, dict)]
    kept, _cut = fit_budget(rows[:NAMES_MAX_ROWS], budget=NAMES_DATA_BUDGET)
    result: dict[str, Any] = {"datasets": kept, "shown": len(kept), "total": len(rows)}
    if len(kept) < len(rows):
        result["more"] = True
        result["note"] = (
            f"Only the newest {len(kept)} of {len(rows)} names fit one call; narrow with "
            '--input \'{"name": "<text>"}\' to find the rest.'
        )
    return result, _meta(invocation, auth.workspace_id, project_id)


def _dataset_names_everywhere(invocation: Invocation) -> HandlerResult:
    """``dataset list`` with ``names`` and no project: the names of every reachable project.

    One workspace search (100 hits a page, the route's cap) lists the datasets of the
    projects the caller can open, under the same access rules as ``project list``; one
    ``project list`` read supplies the project names. Capped at ``_SEARCH_PAGES`` pages.
    """
    with open_service(invocation) as (service, auth):
        hits, cut = search_hits(service, "datasource", "", fields="minimal")
        names = {p.get("id"): p.get("name") for p in _visible_projects(service)}
    rows = [
        {
            "project_id": hit["project_id"],
            "project_name": names[hit["project_id"]],
            "id": hit["object_id"],
            "name": hit.get("name"),
        }
        for hit in hits
        if hit.get("project_id") in names
    ]
    kept, _cut = fit_budget(rows[:NAMES_MAX_ROWS], budget=NAMES_DATA_BUDGET)
    result: dict[str, Any] = {
        "datasets": kept,
        "shown": len(kept),
        "total": len(rows),
        "projects": len({row["project_id"] for row in rows}),
    }
    if cut or len(kept) < len(rows):
        result["more"] = True
        result["note"] = (
            f"Only the newest {len(kept)} names were read; pass --project to list one "
            "project's names, or name to find one."
        )
    return result, _meta(invocation, auth.workspace_id, None)


def _dataset_total(service: Any, project_id: int, page: dict[str, Any], offset: int) -> int:
    """The project's whole dataset count. The list route sends none, so a page that
    is the last one counts itself; otherwise the ids are read once, here, in one call."""
    if not page.get("more"):
        return int(offset) + int(page["shown"])
    everything = service.call(
        "mammoth.api.datasets.DatasetsAPI.list_all", project_id=project_id, fields="id"
    )
    return len(everything.get("datasets", []))


def _dataset_name_search(
    invocation: Invocation, project_id: int, name: str, document: dict[str, Any]
) -> HandlerResult:
    """``dataset list`` with ``name``: every page is read here, then filtered by substring.

    The list route only filters by exact name, so the substring match is local; the
    reads are bounded by the SDK's ``max_pages``.
    """
    with open_service(invocation) as (service, auth):
        data = service.call(
            "mammoth.api.datasets.DatasetsAPI.list_all",
            project_id=project_id,
            sort=document.get("sort", "(created_at:desc)"),
            fields=DATASET_ROW_FIELDS,
        )
        records = data.get("datasets", []) if isinstance(data, dict) else []
        page = search_page(records, name, int(document.get("offset", 0)), document.get("limit"))
        if page["matched"] == 0:
            found, cut = _find_by_name(service, name.lower(), _visible_projects(service))
            elsewhere = [m for m in found if m["project_id"] != project_id]
            if elsewhere:
                page["in_other_projects"] = elsewhere
                page["note"] = (
                    f"No dataset in project {project_id} matches; the ones listed in "
                    "in_other_projects do. Run the next call with --project <its project_id>."
                )
            if cut:
                page["truncated"] = True
                page["note"] = " ".join(
                    filter(None, (page.get("note"), search_cut_note("datasets")))
                )
    page["name"] = name
    return page, _meta(invocation, auth.workspace_id, project_id)


def _compact_dataset_list(data: Any, offset: int, sort: str | None, limit: int) -> Any:
    """Summarise a dataset-list page and fit it to the tool output cap."""
    datasets = data.get("datasets") if isinstance(data, dict) else None
    if not isinstance(datasets, list):
        return data
    summaries = [dataset_summary(item) for item in datasets if isinstance(item, dict)]
    kept, omitted = fit_budget(summaries)
    result: dict[str, Any] = {
        "datasets": kept,
        "shown": len(kept),
        "order": sort or "newest first (created_at desc)",
        "note": (
            "A dataset record holds no sample values; 'view list DATASET_ID' shows "
            "a sample of the stored profile per view as sample_values "
            "(all_columns: true lists every column)."
        ),
    }
    # The list route sends no ``next``: a page of ``limit`` rows may have a successor.
    if omitted or data.get("next") or len(datasets) >= limit:
        result["more"] = True
        result["next_offset"] = int(offset) + len(kept)
        result["note"] += (
            " For just the names of every dataset, one call: --input '{\"names\": true}'"
            " (up to 500 names, no paging)."
        )
    return result


def _export_write_hint(data: dict[str, Any]) -> str | None:
    """Name the recurring export that writes into this dataset, if any.

    A dataset produced by ``view export dataset`` carries its source view and
    export ids in ``additional_info`` (``DATAVIEW_ID``/``TRIGGER_ID`` — an
    export is a ``DataviewActionTrigger`` row, so ``TRIGGER_ID`` is exactly the
    ``export_id`` argument ``view export delete`` takes). Deleting the dataset
    does not stop that export from writing into it again; name the export and
    the command that stops it (T1-O-10: an agent deleted the dataset instead).
    """
    additional_info = data.get("additional_info")
    if not isinstance(additional_info, dict):
        return None
    dataview_id = additional_info.get("DATAVIEW_ID")
    export_id = additional_info.get("TRIGGER_ID")
    if not isinstance(dataview_id, int) or not isinstance(export_id, int):
        return None
    return (
        f"This dataset is written by a recurring export from view {dataview_id} "
        f"(export {export_id}); deleting the dataset does not stop the export. "
        f"Run 'mammoth view export delete {dataview_id} {export_id}' to stop it."
    )


def _zero_view_hint(dataset_id: int, status: Any = None) -> str:
    """Name the fix for a dataset with no queryable views yet (T1-I-13).

    Nothing is queryable until a view exists (transforms, joins, exports and
    previews all take a view id, not a dataset id) — an agent that only reads
    dataset-level metadata and never sees a zero view count can conclude "no
    correction needed" while nothing it changed is visible anywhere.
    """
    if status in ("need_action", "has_unstructured_data"):
        return (
            "This dataset has no views yet because it is waiting for a decision "
            f"(status {status}). Run 'mammoth dataset file-settings get {dataset_id}', then "
            f"'mammoth dataset file-settings update {dataset_id}' with the settings; a view "
            "appears once it is ready."
        )
    return (
        f"This dataset has no views yet; nothing is queryable until one exists. "
        f"Run 'mammoth view create {dataset_id}' to create one."
    )


def dataset_get(invocation: Invocation) -> HandlerResult:
    """Get one dataset by id in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
        views = service.call(
            "mammoth.api.dataviews.DataviewsAPI.list",
            dataset_id=dataset_id,
            project_id=project_id,
        )
    _strip_file_ingestion_automation_possible(data)
    hint = _export_write_hint(data) if isinstance(data, dict) else None
    if isinstance(data, dict) and isinstance(views, dict):
        view_count = len(views.get("dataviews") or [])
        data = {**data, "view_count": view_count}
        if view_count == 0:
            zero_hint = _zero_view_hint(dataset_id, data.get("status"))
            hint = f"{hint} {zero_hint}" if hint else zero_hint
    if hint is not None:
        data = {**data, "hint": hint}
    return data, _meta(invocation, auth.workspace_id, project_id)


def _strip_file_ingestion_automation_possible(data: Any) -> None:
    """Drop ``automation_possible`` (T1-R-01/T1-R-07): CSV-ingestion metadata
    about whether the header-parsing pipeline can auto-process this upload
    (``api/api/file/unprocessed.py``), unrelated to whether the dataset has a
    connector to put on a scheduled refresh. Left in, an agent checking a
    dataset's automation options reads it as contradicting a correct "no
    refreshable source" claim."""
    if not isinstance(data, dict):
        return
    params = data.get("additional_info", {}).get("all_data_backup", {}).get("PARAMS", {})
    if isinstance(params, dict):
        params.pop("automation_possible", None)


def _sample_read(service: Any, dataset_id: int, project_id: int) -> Any:
    return service.call(_DATA_SYMBOL, dataset_id=dataset_id, project_id=project_id)


def dataset_schema_diff(invocation: Invocation) -> HandlerResult:
    """Compare two datasets' columns and propose the ``batch create`` mapping.

    ``DESTINATION_ID SOURCE_ID`` are in the order ``batch create`` takes them.
    """
    from mammoth_cli.commands.batch import _dataset_columns

    project_id = require_project(invocation)
    destination_id = _require_int_positional_at(invocation, 0, "destination dataset id")
    source_id = _require_int_positional_at(invocation, 1, "source dataset id")
    with open_service(invocation) as (service, auth):
        destination = _dataset_columns(service, destination_id, "destination")
        source = _dataset_columns(service, source_id, "source")
        diff = schema_diff(
            destination,
            source,
            column_samples(_sample_read(service, destination_id, project_id), destination),
            column_samples(_sample_read(service, source_id, project_id), source),
        )
    result = {"destination_dataset_id": destination_id, "source_dataset_id": source_id, **diff}
    result["next"] = (
        f"mammoth batch create {destination_id} {source_id} --input "
        "'{\"mapping\": <mapping>}'; batch create refuses a source column with no destination, "
        "so map or drop each added column first."
    )
    return result, _meta(invocation, auth.workspace_id, project_id)


def dataset_data(invocation: Invocation) -> HandlerResult:
    """Fetch a dataset's data, waiting for the backing job to complete."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _validate_paging(document: dict[str, Any]) -> None:
    """Refuse a ``limit`` outside 0..100 or a negative ``offset`` before any call is made."""
    for field, minimum, maximum in (("limit", 0, 100), ("offset", 0, None)):
        value = document.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < minimum
            or (maximum is not None and value > maximum)
        ):
            bound = "between 0 and 100" if maximum is not None else "non-negative"
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"'{field}' must be {bound}.",
                exit_status=EXIT_USAGE,
            )


def _batch_column_ids(
    service: Any, dataset_id: int, project_id: int, columns: str | list[str]
) -> str:
    """The comma-separated column ids the batch-data route wants, from names or ids."""
    response = service.call(_DATASET_GET_SYMBOL, dataset_id=dataset_id, project_id=project_id)
    dataset = response.get("dataset", response) if isinstance(response, dict) else {}
    schema = dataset.get("data_schema") if isinstance(dataset, dict) else None
    return resolve_batch_columns(schema, dataset_id, columns)


def resolve_batch_columns(schema: Any, dataset_id: int, columns: str | list[str]) -> str:
    """Column ids, comma-separated, for names or ids in ``columns`` (a list or one string).

    The batch-data route refuses display names with a bare "invalid columns"; the dataset
    schema maps each ``c_name`` to its ``c_id``. An id passes through; a name the schema
    lacks is refused with the names it has.
    """
    if not isinstance(schema, list):
        raise CliError(
            code=CODE_API_ERROR,
            message=f"Could not read dataset {dataset_id}'s columns to resolve 'columns'.",
            exit_status=EXIT_API,
        )
    wanted = [n.strip() for n in columns.split(",")] if isinstance(columns, str) else columns
    ids = {c["c_id"] for c in schema if isinstance(c, dict) and "c_id" in c}
    by_name = {c["c_name"]: c["c_id"] for c in schema if isinstance(c, dict) and "c_name" in c}
    resolved = [name if name in ids else by_name.get(name) for name in wanted]
    missing = [name for name, found in zip(wanted, resolved, strict=True) if found is None]
    if missing:
        raise CliError(
            code="unknown_column",
            message=f"Column(s) not in dataset {dataset_id}: {', '.join(missing)}.",
            exit_status=EXIT_USAGE,
            hint="Use column names or ids from `mammoth dataset get`.",
            details={"columns": missing, "available": sorted(by_name)},
        )
    return ",".join(str(found) for found in resolved)


def dataset_batch_data(invocation: Invocation) -> HandlerResult:
    """Fetch data for a specific dataset batch."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    batch_id = _require_int_positional_at(invocation, 1, "batch id")
    document = invocation.load_input() or {}
    _validate_paging(document)
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "batch_id": batch_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("columns", "limit", "offset", "timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        if kwargs.get("columns"):
            columns = kwargs["columns"]
            kwargs["columns"] = _batch_column_ids(service, dataset_id, project_id, columns)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings(invocation: Invocation) -> HandlerResult:
    """Get file settings (delimiter, header, dates, ...) for a dataset."""
    data, meta = _read_dataset(invocation)
    return with_file_upload_path(data, _require_int_positional(invocation, "dataset id")), meta


def dataset_broken_rows(invocation: Invocation) -> HandlerResult:
    """List the lines of a dataset's uploaded file that could not be parsed."""
    return _read_dataset(invocation)


def dataset_broken_rows_resolve(invocation: Invocation) -> HandlerResult:
    """Add corrected set-aside lines to a dataset, or discard them. Prompt or ``--yes``.

    ``--input`` carries ``op`` (``add`` or ``remove``), ``batch_id`` and ``rows``
    (``{"line_num", "line"}`` each, from ``dataset broken-rows list``). Returns a
    job to wait on.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "op": _require_field(document, "op"),
        "batch_id": _require_field(document, "batch_id"),
        "rows": _require_field(document, "rows"),
        "project_id": project_id,
    }
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"{kwargs['op']} set-aside lines of dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _read_dataset(invocation: Invocation) -> HandlerResult:
    """Call this command's SDK read with the DATASET_ID positional."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    if dataset_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dataset id must be positive.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings_update(invocation: Invocation) -> HandlerResult:
    """Update a dataset's file settings from ``--input``.

    Each field is optional: the SDK keeps the stored value of any reading setting
    (``delimiter``, ``has_header``, ``initial_skip_count``, ``quotechar``) left out.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(
        document,
        kwargs,
        (
            "delimiter",
            "has_header",
            "initial_skip_count",
            "quotechar",
            "date_format",
            "preview_mode",
            "skip_auto_process_check",
            "date_formats",
            "set_project_level_date_format",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        # The route answers with a reprocess job handle. Block on it (honoring
        # ``--job-timeout``) so the command returns when the dataset has been re-read
        # with the new settings; a response that is not a job passes through.
        settled = service.wait_if_job(data)
        if isinstance(settled, dict) and isinstance(data, dict) and settled is not data:
            settled = {**data, **settled}
        if isinstance(settled, dict) and not settled.get("name"):
            settled = _with_dataset_name(service, settled, dataset_id, project_id)
    return settled, _meta(invocation, auth.workspace_id, project_id)


def dataset_update_method_get(invocation: Invocation) -> HandlerResult:
    """Say whether a new file replaces this dataset's rows or adds to them."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return describe_update_method(data, dataset_id), _meta(
        invocation, auth.workspace_id, project_id
    )


def dataset_update_method_set(invocation: Invocation) -> HandlerResult:
    """Set whether a new file replaces this dataset's rows (``replace``) or adds to them.

    The setting stays on the dataset: every later upload into it and every folder
    automation feeding it follows it. ``schema_mapping`` optionally says which file
    column feeds which dataset column.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    mode = parse_mode(_require_field(document, "mode"))
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "mode": mode, "project_id": project_id}
    assert document is not None
    _forward_optional(document, kwargs, ("schema_mapping",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return describe_update_method(data, dataset_id), _meta(
        invocation, auth.workspace_id, project_id
    )


def _with_dataset_name(
    service: Any, result: dict[str, Any], dataset_id: int, project_id: int
) -> dict[str, Any]:
    """Add ``dataset_name`` to a result that names its dataset by id only (best effort)."""
    try:
        record = service.call(_DATASET_GET_SYMBOL, dataset_id=dataset_id, project_id=project_id)
    except CliError:
        return result
    name = record.get("name") if isinstance(record, dict) else None
    return {**result, "dataset_name": name} if isinstance(name, str) and name else result


def dataset_file_settings_undo(invocation: Invocation) -> HandlerResult:
    """Undo the last file settings change for a dataset. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"undo file settings for dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


_INTERPRETATION_FIELDS = ("user_instruction", "structure_map", "destination_dataset_id")


def dataset_interpretation(invocation: Invocation) -> HandlerResult:
    """Preview or confirm how a file that can be read several ways is interpreted.

    ``--input`` carries ``user_instruction`` (plain English, e.g. one of the
    suggestions ``dataset get`` shows), a ``structure_map`` from an earlier
    preview, or a ``destination_dataset_id``; at least one is required. ``confirm``
    alone also takes ``mode``: ``"original"`` keeps the file in its uploaded layout
    (no other field then), ``"interpreted"`` is the default.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    confirming = invocation.command_id == "dataset.interpretation.confirm"
    _forward_optional(
        document,
        kwargs,
        (*_INTERPRETATION_FIELDS, "mode") if confirming else _INTERPRETATION_FIELDS,
    )
    if not any(field in kwargs for field in (*_INTERPRETATION_FIELDS, "mode")):
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="Say how to read the file: pass one of " + ", ".join(_INTERPRETATION_FIELDS),
            exit_status=EXIT_USAGE,
            hint="Use a suggestion from 'mammoth dataset get DATASET_ID' "
            "(additional_info.interpretation.instruction_suggestions) as user_instruction.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        if confirming and isinstance(data, dict):
            data = {**data, **_confirmed_shape(service, dataset_id, project_id)}
    return data, _meta(invocation, auth.workspace_id, project_id)


def _confirmed_shape(service: Any, dataset_id: int, project_id: int) -> dict[str, Any]:
    """The dataset's ``columns`` (display name and type) and ``row_count`` after a confirm.

    Best effort: the confirm already ran, so an unreadable dataset adds nothing and never fails
    the command.

    Args:
        service: The open service.
        dataset_id: The confirmed dataset.
        project_id: Its project.

    Returns:
        ``{"columns": [{"name", "type"}], "row_count": N}`` with the parts that could be read.
    """
    try:
        response = service.call(
            "mammoth.api.datasets.DatasetsAPI.get", dataset_id=dataset_id, project_id=project_id
        )
    except CliError:
        return {}
    dataset = response.get("dataset", response) if isinstance(response, dict) else None
    if not isinstance(dataset, dict):
        return {}
    shape: dict[str, Any] = {}
    schema = dataset.get("data_schema") or dataset.get("columns")
    if isinstance(schema, list):
        shape["columns"] = [
            {"name": col.get("c_name", col.get("name")), "type": col.get("c_type", col.get("type"))}
            for col in schema
            if isinstance(col, dict)
        ]
    if isinstance(dataset.get("row_count"), int):
        shape["row_count"] = dataset["row_count"]
    return shape


def dataset_rename(invocation: Invocation) -> HandlerResult:
    """Rename a dataset. Dataset id is positional; new name comes from ``--input``.

    A name another dataset of the project already has gets a number added (``name 2``)
    instead of failing; ``{"unique": false}`` asks for the exact name or an error. The
    result's ``name`` is the name applied.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    name = _require_field(document, "name")
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "name": name, "project_id": project_id}
    if document is None or document.get("unique") is not False:
        kwargs["unique"] = True
    with open_service(invocation) as (service, auth):
        try:
            data = service.call(_symbol(invocation), **kwargs)
        except CliError as error:
            if "4DSET008" not in error.message:
                raise
            # The backend refuses a rename to the current name; that is the state asked for.
            current = service.call(
                "mammoth.api.datasets.DatasetsAPI.get", dataset_id=dataset_id, project_id=project_id
            )
            record = current.get("dataset", current) if isinstance(current, dict) else {}
            if not isinstance(record, dict) or record.get("name") != name:
                raise
            data = {
                "dataset_id": dataset_id,
                "name": name,
                "changed": False,
                "note": "The dataset already has this name; nothing was changed.",
            }
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_refresh(invocation: Invocation) -> HandlerResult:
    """Fetch a URL dataset's link again into the same dataset. Prompt or ``--yes`` required.

    The server refuses a dataset not made from a URL and a URL that serves JSON; its
    reason reaches the caller. Waits for the job (honoring ``--job-timeout``).
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"fetch the link of dataset {dataset_id} again and update its data",
    )
    with open_service(invocation) as (service, auth):
        handle = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
        service.wait_if_job(handle)
    return {"dataset_id": dataset_id, "refreshed": True}, _meta(
        invocation, auth.workspace_id, project_id
    )


def dataset_trash(invocation: Invocation) -> HandlerResult:
    """Move one dataset to the project trash (reversible)."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_restore(invocation: Invocation) -> HandlerResult:
    """Restore a trashed dataset."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one dataset by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    action = f"delete dataset {dataset_id}"
    with open_service(invocation) as (service, auth):
        # A read, not a mutation: the dry-run gate lets it through so the
        # confirmation message below can name the export writing into this
        # dataset (T1-O-10), the same as a real run would see.
        preview = service.call(
            "mammoth.api.datasets.DatasetsAPI.get", dataset_id=dataset_id, project_id=project_id
        )
        hint = _export_write_hint(preview) if isinstance(preview, dict) else None
        if hint is not None:
            action = f"{action}. {hint}"
        enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=action)
        ack = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
        # The server acknowledges a delete with a job handle. Settle it here so
        # the handle's id is kept as ``job.id`` (the shape ``view delete`` has).
        settled = service.wait_if_job(ack)
        data = _with_job(ack, settled)
        # A delete the server accepts but does not carry out (a view's join still reads
        # the dataset) is a failure, not a verified success.
        ensure_deleted(
            service,
            noun="dataset",
            resource_id=dataset_id,
            read_symbol="mammoth.api.datasets.DatasetsAPI.get",
            read_kwargs={"dataset_id": dataset_id, "project_id": project_id},
            responses=(ack, settled),
            recovery_commands=_dependent_view_recovery(ack, settled, dataset_id),
        )
        # The get can say gone while ``dataset list`` still shows the dataset: verified only
        # when the list the caller reads next agrees.
        ensure_unlisted(
            service,
            noun="dataset",
            resource_id=dataset_id,
            list_symbol="mammoth.api.datasets.DatasetsAPI.list_all",
            list_kwargs={"project_id": project_id, "fields": "id,name"},
            collection="datasets",
        )
    if isinstance(data, dict):
        # ``ensure_deleted`` read the dataset and found it gone; say so rather than
        # listing the project's remaining datasets to show the same thing.
        data = {**data, "deleted": [dataset_id]}
        if hint is not None:
            data["hint"] = hint
    return data, _meta(invocation, auth.workspace_id, project_id)


def _dependent_view_recovery(ack: Any, settled: Any, dataset_id: int) -> list[str]:
    """``view task list`` for each view the server named as depending on the dataset."""
    for response in (ack, settled):
        found = find_dependents(response, dataset_id)
        if isinstance(found, dict):
            return [f"mammoth view task list {view_id}" for view_id in sorted(found)]
    return []


def _with_job(handle: Any, settled: Any) -> Any:
    """Return the settled result with the acknowledged job's id as ``job.id``."""
    job_id = handle.get("job_id") if isinstance(handle, dict) else None
    if job_id is None or not isinstance(settled, dict):
        return settled
    return {**settled, "job": {"id": job_id}}


def dataset_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete the listed datasets. ``dataset_ids`` from ``--input``; ``--yes`` required.

    The route has no delete-all form: it takes an explicit ``ids`` list and
    rejects an empty one, so the CLI never confirms an implicit whole-project
    delete.
    """
    project_id = require_project(invocation)
    document = invocation.load_input()
    dataset_ids = _require_field(document, "dataset_ids")
    if (
        not isinstance(dataset_ids, list)
        or not dataset_ids
        or any(
            isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in dataset_ids
        )
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'dataset_ids' input field must be a non-empty list of positive integers.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=(
            f"delete datasets {', '.join(str(item) for item in dataset_ids)} "
            f"in project {project_id}"
        ),
    )
    with open_service(invocation) as (service, auth):
        # Look before deleting: an id the backend never had must read as not_found,
        # not as a deleted dataset with a null payload.
        present = _datasets_still_present(service, dataset_ids, project_id)
        existing = [item for item in dataset_ids if item in present]
        data: Any = None
        remaining: list[int] = []
        if existing:
            data = service.call(_symbol(invocation), dataset_ids=existing, project_id=project_id)
            remaining = _datasets_still_present(service, existing, project_id)
    results = [
        _bulk_delete_result(item, item in present, item in remaining) for item in dataset_ids
    ]
    deleted = [r["dataset_id"] for r in results if r["status"] == "deleted"]
    meta = _meta(invocation, auth.workspace_id, project_id)
    if not deleted:
        missing_only = not existing
        raise CliError(
            code=CODE_RESOURCE_NOT_FOUND if missing_only else CODE_API_ERROR,
            message=(
                f"No dataset with id {', '.join(str(i) for i in dataset_ids)} in project "
                f"{project_id}."
                if missing_only
                else f"None of the {len(dataset_ids)} datasets was deleted; "
                f"still present: {', '.join(str(i) for i in remaining)}."
            ),
            exit_status=EXIT_NOT_FOUND if missing_only else EXIT_API,
            hint=(
                "Use dataset ids as 'mammoth dataset list' shows them."
                if missing_only
                else "A dataset that another view uses as a lookup or join source is kept. "
                "Delete the view that uses it first, then run the delete again."
            ),
            details={"results": results},
        )
    out: dict[str, Any] = {
        "results": results,
        "deleted": deleted,
        "requested": len(dataset_ids),
    }
    if isinstance(data, dict):
        out["response"] = data
    if len(deleted) < len(dataset_ids):
        out["partial"] = True
        out["warnings"] = [
            f"Dataset {r['dataset_id']}: {r['status']}"
            + (f" ({r['detail']})" if r.get("detail") else "")
            for r in results
            if r["status"] != "deleted"
        ]
    return out, meta


def _bulk_delete_result(dataset_id: int, existed: bool, survived: bool) -> dict[str, Any]:
    if not existed:
        return {"dataset_id": dataset_id, "status": "not_found"}
    if survived:
        return {
            "dataset_id": dataset_id,
            "status": "failed",
            "detail": (
                "still present, probably used by a view's join or lookup; "
                f"mammoth dataset get {dataset_id} shows it and mammoth dataset delete "
                f"{dataset_id} names the dependent views"
            ),
        }
    return {"dataset_id": dataset_id, "status": "deleted"}


#: Backend code for a dataset id that does not exist (the get route answers 400, not 404).
_INVALID_DATASET_ID = "4DSET001"


def _datasets_still_present(service: Any, dataset_ids: list[int], project_id: int) -> list[int]:
    """The ids of ``dataset_ids`` the server still returns after a bulk delete."""
    present: list[int] = []
    for dataset_id in dataset_ids:
        try:
            service.call(
                "mammoth.api.datasets.DatasetsAPI.get", dataset_id=dataset_id, project_id=project_id
            )
        except CliError as error:
            if (
                error.code != CODE_RESOURCE_NOT_FOUND
                and error.details.get("backend_code") != _INVALID_DATASET_ID
            ):
                raise
            continue
        present.append(dataset_id)
    return present


def dataset_bulk_update(invocation: Invocation) -> HandlerResult:
    """Apply a bulk patch across the active project's datasets. High-impact."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    patch_data = _require_field(document, "patch_data")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"bulk-update datasets in project {project_id}",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patch_data=patch_data, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_update(invocation: Invocation) -> HandlerResult:
    """Reject untyped dataset patches; use a typed dataset command instead."""
    raise CliError(
        code=CODE_UNSUPPORTED_CONTRACT,
        message="Raw dataset patch operations are not available through the CLI.",
        exit_status=EXIT_USAGE,
        hint=(
            "Use 'dataset rename DATASET_ID' for a name change, 'dataset update-method set "
            "DATASET_ID' for whether a new file replaces or adds rows, or 'dataset "
            "file-settings update DATASET_ID' for how the file is read; other update variants "
            "need a typed contract."
        ),
        details={
            "command_id": invocation.command_id,
            "blocker": "B07 DATASET_PATCH_UNTYPED",
            "typed_alternatives": [
                "dataset.rename",
                "dataset.update-method.set",
                "dataset.file-settings.update",
            ],
        },
        recovery_commands=[
            "mammoth schema get dataset.rename",
            "mammoth schema get dataset.update-method.set",
            "mammoth schema get dataset.file-settings.update",
        ],
    )
