"""Handlers for the sub-client-backed ``view`` command family.

This module covers dataview operations, checkpoints, data checks, derivatives,
versions, pipeline/task operations, exports, and AI helpers that are backed by
real SDK sub-clients (``DataviewsAPI``, ``CheckpointsAPI``, ``DataChecksAPI``,
``DerivativesAPI``, ``PipelineAPI``, ``PipelineVersionsAPI``, ``ExportsAPI``,
``AIAPI``). It intentionally excludes ``view transform *`` (pipeline
transformation builders), the interactive ``view draft *`` workflow commands,
and ``view create/get/delete`` — those are implemented elsewhere.

Most commands here are project-scoped (their SDK signature carries a
``project_id`` parameter) and take a ``dataset_id`` and/or ``dataview_id`` as
leading positionals, in the order those ids appear in the signature. A few
pipeline/task/AI commands have no ``project_id`` parameter at all — those pass
``None`` as the project id in the envelope metadata, mirroring
:mod:`mammoth_cli.commands.project`'s read handlers. Handlers dispatch through
the generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to
the public SDK method named by the command's reviewed manifest ``sdk_symbol``.
"""

from __future__ import annotations

import dataclasses
import inspect
import shlex
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from mammoth.models.exports import ExportStatus
from mammoth.view import ViewExport

from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_INVALID_ARGUMENTS,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.normalize import DataRows
from mammoth_cli.runtime import embedded, parents
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services import conditional_format as cf_rules
from mammoth_cli.services import read_queries, text_dates
from mammoth_cli.services.append_blank_columns import (
    BLANK_COLUMNS_FIELD,
    acknowledged_blank_columns,
)
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.dashboard_review import UPLOAD_NOTE, upload_hints
from mammoth_cli.services.data_quality import column_warnings, duplicate_rows_fact
from mammoth_cli.services.listing import DATASET_LIST_FIELDS, compact_view_list
from mammoth_cli.services.local_time import local_time
from mammoth_cli.services.read_queries import ReadContext

HandlerResult = tuple[Any, dict[str, Any]]

# Wire-shape keys returned by the dataview data/preview/metadata endpoints,
# named so the column-relabel logic and any future reader share one source of
# truth instead of repeating magic strings.
_COLUMNS_KEY = "columns"
_ROWS_KEY = "data"
_METADATA_KEY = "metadata"
_INTERNAL_NAME_KEY = "internal_name"
_DISPLAY_NAME_KEY = "display_name"
_DATAVIEW_GET_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.get"
_DATASET_GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get"
# Public SDK resolver that finds the dataset containing a dataview, so the
# data-read commands can take the view id alone and fill the dataset for the
# caller. See :data:`mammoth_cli.services.positionals.POSITIONAL_OVERRIDES`.
_FIND_DATASET_SYMBOL = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_WAIT_FOR_PIPELINE_SYMBOL = "mammoth.api.pipeline.PipelineAPI.wait_for_pipeline"
_DATASET_ID_FIELD = "dataset_id"
_DRAFT_OPERATIONS = frozenset({"enter", "exit", "submit", "discard"})

# Preview input keys and their sensible defaults, so `mammoth view preview DS V`
# works with no --input: 50 rows, and enough columns to show every one (the
# preview endpoint otherwise caps at a narrow default and hides columns a
# transform just added at the end of the schema).
_ROWS_INPUT_KEY = "rows"
_COLS_INPUT_KEY = "cols"
_DEFAULT_PREVIEW_ROWS = 50

# Internal row-identity column the platform appends to every data/preview
# response. It is not a user column (never in the display metadata) and the app
# never shows it, so the CLI hides it from rows and headers.
_SYSTEM_COLUMNS = frozenset({"hash"})


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _int_positional_at(invocation: Invocation, index: int, name: str) -> int | None:
    """Parse the positional argument at ``index`` as an int, or return None."""
    if len(invocation.extra_args) <= index:
        return None
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Return the required positional argument at ``index`` as an int, or raise."""
    value = _int_positional_at(invocation, index, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs`` unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _int_field(value: Any, name: str) -> int:
    """``value`` as an integer, or an ``invalid_argument`` error naming the field."""
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The '{name}' input field must be an integer, got {value!r}.",
            exit_status=EXIT_USAGE,
        ) from exc


def _resolve_dataset_id(
    service: Any,
    invocation: Invocation,
    view_id: int,
    document: dict[str, Any],
    dataset_index: int = 1,
) -> int:
    """Return the dataset id for a view-scoped command.

    The dataset is an optional *trailing* positional at ``dataset_index`` (and a
    dual-sourced ``dataset_id`` --input field). When the caller supplies neither,
    it is resolved from the view via the public pipeline resolver, so
    ``mammoth view preview VIEW_ID`` works with no dataset id. An explicit value
    (positional first, then --input) is always honored and skips the lookup.

    ``dataset_index`` is the positional slot the trailing dataset id occupies: 1
    for the ``VIEW_ID [DATASET_ID]`` commands and 2 for the
    ``VIEW_ID SUB_ID [DATASET_ID]`` sub-resource commands.
    """
    explicit = _int_positional_at(invocation, dataset_index, "dataset id")
    if explicit is not None:
        return explicit
    field = document.get(_DATASET_ID_FIELD)
    if field is not None:
        return _int_field(field, _DATASET_ID_FIELD)
    profile_name = _profile_name(invocation)
    workspace_id = getattr(service, "_workspace_id", None)
    remembered = parents.lookup(profile_name, workspace_id, view_id)
    if remembered is not None:
        return remembered
    _require_discovery_allowed(invocation, view_id)
    dataset_id = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=view_id))
    parents.remember(profile_name, workspace_id, {view_id: dataset_id})
    return dataset_id


def _resolve_dataset_id_for_settle(
    service: Any,
    invocation: Invocation,
    view_id: int,
    document: dict[str, Any],
    dataset_index: int,
) -> int | None:
    """Best-effort :func:`_resolve_dataset_id`, for the settle step only.

    The write this settles has already happened by the time this runs; a
    parent that ``_resolve_dataset_id`` cannot resolve raises (these are
    mutation commands, so it refuses project-wide discovery) -- that must
    never surface as an exception past a write that already succeeded. A
    ``None`` here leaves the settle step unable to run, which
    ``_settle_async_view_write``/verify.py report as unverified rather than
    guessing "done".
    """
    try:
        return _resolve_dataset_id(service, invocation, view_id, document, dataset_index)
    except CliError:
        return None


def _profile_name(invocation: Invocation) -> str:
    return invocation.profile or profiles.get_selected()


def _require_discovery_allowed(invocation: Invocation, view_id: int) -> None:
    """Refuse project-wide parent discovery before anything but a read.

    Omitting the parent sends the resolver on a browse-and-probe walk over
    every dataset in the project. For a read that is a convenience; before a
    mutation, an export, or a delete it means the target is chosen by a
    probe whose first denied dataset can end the search on the wrong parent.
    Those commands therefore require the exact parent, and fail closed here
    with the read that supplies it.
    """
    record = command_by_id(invocation.command_id) or {}
    if record.get("mutation_class", "read") == "read":
        return
    project = f" --project {invocation.project}" if invocation.project else ""
    lookup = f"mammoth view get {view_id}{project}"
    takes_positional = any(
        positional.get("name") == "dataset_id" for positional in record.get("positionals", [])
    )
    where = (
        "the trailing DATASET_ID positional or the 'dataset_id' input field"
        if takes_positional
        else "the 'dataset_id' field of --input (this command takes no DATASET_ID positional)"
    )
    raise CliError(
        code=CODE_MISSING_ARGUMENT,
        message=(
            "This command changes or exports data, so it requires the exact parent "
            "DATASET_ID; project-wide parent discovery is only performed for reads."
        ),
        exit_status=EXIT_USAGE,
        hint=f"Read the parent first ({lookup}), then pass it as {where}.",
        details={"view_id": view_id, "mutation_class": record.get("mutation_class")},
        recovery_commands=[lookup],
    )


def _require_exact_parent(
    service: Any, invocation: Invocation, view_id: int, kwargs: dict[str, Any]
) -> None:
    """Pin the exact parent dataset of a write in ``kwargs``, or refuse the write.

    An explicit ``dataset_id`` or a remembered parent is used as it is; with
    neither, a write must not let the SDK pick the parent by project-wide
    discovery (see :func:`_require_discovery_allowed`). Reads pass untouched.
    """
    if kwargs.get(_DATASET_ID_FIELD) is not None:
        return
    remembered = parents.lookup(
        _profile_name(invocation), getattr(service, "_workspace_id", None), view_id
    )
    if remembered is not None:
        kwargs[_DATASET_ID_FIELD] = remembered
        return
    _require_discovery_allowed(invocation, view_id)


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a view command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _read_meta(
    service: Any,
    invocation: Invocation,
    workspace_id: int,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
) -> dict[str, Any]:
    """Envelope metadata for a data read, naming the dataset and view it read.

    A number in an answer needs its source; without the names an agent that
    silently used the wrong one of two look-alike datasets never says so.
    """
    meta = _meta(invocation, workspace_id, project_id)
    view = service.call(
        _DATAVIEW_GET_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=project_id,
        fields="__min",
    )
    dataset = service.call(
        _DATASET_GET_SYMBOL, dataset_id=dataset_id, project_id=project_id, fields="id,name"
    )
    dataset = dataset.get("dataset", dataset) if isinstance(dataset, dict) else {}
    meta["dataset"] = {"id": dataset_id, "name": dataset.get("name")}
    meta["view"] = {"id": view_id, "name": view.get("name") if isinstance(view, dict) else None}
    return meta


# ---------------------------------------------------------------------------
# view.list / view.bulk-delete (dataset-scoped, no dataview_id)
# ---------------------------------------------------------------------------


#: What an agent reads a view for: identity, parent, columns and types, row
#: count, and pipeline state. The record's ``dependencies_info`` and display
#: trees are several times that size and rarely wanted; ``fields`` (``"__full"``,
#: ``"__standard"`` or a list) returns them.
BRIEF_VIEW_FIELDS: tuple[str, ...] = (
    "id",
    "ds_id",
    "dataset_id",
    "name",
    "status",
    "row_count",
    "column_count",
    "metadata",
    "pipeline_status",
    "is_pipeline_running",
    "is_dataview_data_in_sync",
    "data_updated_at",
    "updated_at",
)


#: The dataview-record fields that say how current a view's data is.
_FRESHNESS_FIELDS: tuple[str, ...] = (
    "data_updated_at",
    "updated_at",
    "pipeline_status",
    "is_pipeline_running",
    "is_dataview_data_in_sync",
)


def view_freshness(record: dict[str, Any]) -> dict[str, Any]:
    """How current a view's data is, apart from whether the data is any good.

    The server's own fields, unchanged, plus ``state``: ``running`` (a
    pipeline is applying now), ``out_of_sync`` (the view's data does not
    match its pipeline), ``in_sync``, or ``unknown`` (the record says none of
    it). Data quality is ``column_warnings``, a separate question.
    """
    facts = {key: record[key] for key in _FRESHNESS_FIELDS if key in record}
    if record.get("is_pipeline_running"):
        state = "running"
    elif record.get("is_dataview_data_in_sync") is False:
        state = "out_of_sync"
    elif record.get("is_dataview_data_in_sync") is True:
        state = "in_sync"
    else:
        state = "unknown"
    return {"state": state, **facts}


def apply_column_renames(record: Any) -> Any:
    """Show renamed columns under their new names in a dataview record.

    A rename (``view transform rename-columns`` or the web grid) is stored in
    ``display_properties.COLUMN_NAMES`` as ``{internal_name: name}``; the
    server's ``metadata`` keeps the name the pipeline produced. Every CLI
    output uses the name the user sees, so the rename wins.
    """
    if not isinstance(record, dict):
        return record
    display = record.get("display_properties")
    renames = display.get("COLUMN_NAMES") if isinstance(display, dict) else None
    metadata = record.get(_METADATA_KEY)
    if not isinstance(renames, dict) or not renames or not isinstance(metadata, list):
        return record
    columns = []
    for column in metadata:
        new_name = renames.get(column.get(_INTERNAL_NAME_KEY)) if isinstance(column, dict) else None
        columns.append({**column, _DISPLAY_NAME_KEY: new_name} if new_name else column)
    return {**record, _METADATA_KEY: columns}


def brief_view_record(record: Any) -> Any:
    """Keep only :data:`BRIEF_VIEW_FIELDS` of a dataview record, renames applied."""
    if not isinstance(record, dict):
        return record
    record = apply_column_renames(record)
    return {key: record[key] for key in BRIEF_VIEW_FIELDS if key in record}


#: dataset.list_all's SDK symbol, reused from the pagination-safe helper item
#: A's discovery fix relies on (mammoth/api/datasets.py) rather than a
#: single unpaginated page, so a project with many datasets is not silently
#: truncated here either.
_DATASETS_LIST_ALL_SYMBOL = "mammoth.api.datasets.DatasetsAPI.list_all"
#: Soft floor for the no-DATASET_ID ``view list`` walk: whole per-dataset
#: pages are pulled and appended until at least this many views have been
#: collected (or the visit cap below is reached), so one call never returns a
#: single dataset's worth from a large project. Sized to what the agent output
#: cap shows (about 15 summaries): reading more only to cut them is waste.
_VIEW_LIST_ALL_DATASETS_MIN_VIEWS = 20
#: Most datasets one no-DATASET_ID ``view list`` call reads views of, whether or
#: not they hold any, so a project of many empty datasets costs a fixed number of
#: requests. The result carries ``next_dataset_offset`` to resume from.
_VIEW_LIST_ALL_DATASETS_MAX_VISITS = 25


def view_list(invocation: Invocation) -> HandlerResult:
    """List dataviews for a dataset, or every dataset in the active project.

    Omitting DATASET_ID used to fail outright with ``missing_argument`` --
    an agent's very first move is often ``view list`` before it knows any
    dataset id. It now walks every dataset in the active project instead
    (paged; see :data:`_VIEW_LIST_ALL_DATASETS_MIN_VIEWS`), same as passing
    an explicit id still does for a single dataset.

    Each view is summarised with what tells views apart: its dataset's name, size,
    times, source, column names and types, and per-column ``sample_values`` (values the
    backend stored, not one real row), cut to fit the agent tool output cap. No
    query runs: one stored-stats read per listed view.
    ``all_columns: true`` lists every column with its type instead of the first few.
    ``full: true`` returns the raw records instead.
    """
    project_id = require_project(invocation)
    dataset_id = _int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input() or {}
    if dataset_id is None and document.get(_DATASET_ID_FIELD) is not None:
        dataset_id = int(document[_DATASET_ID_FIELD])
    compact = not document.get("full")
    with open_service(invocation) as (service, auth):
        datasets: list[dict[str, Any]] = []
        if dataset_id is None:
            data, datasets = _view_list_across_project(
                service, _symbol(invocation), document, project_id, compact
            )
        else:
            kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
            _forward_optional(document, kwargs, ("limit", "sort", "offset"))
            data = service.call(_symbol(invocation), **kwargs)
            if compact:
                datasets = [_dataset_record(service, dataset_id, project_id)]
        parents.remember_records(
            _profile_name(invocation), auth.workspace_id, data, project_id=project_id
        )
        if compact and isinstance(data, dict) and isinstance(data.get("dataviews"), list):
            data = _compact_view_list(service, data, datasets, document)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _dataset_record(service: Any, dataset_id: int, project_id: int) -> dict[str, Any]:
    """One dataset with the fields a list summary shows."""
    response = service.call(
        _DATASET_GET_SYMBOL,
        dataset_id=dataset_id,
        project_id=project_id,
        fields=DATASET_LIST_FIELDS,
    )
    record = response.get("dataset", response) if isinstance(response, dict) else {}
    return {**record, "id": record.get("id", dataset_id)}


_PROFILE_SYMBOL = "mammoth.api.ai.AIAPI.generate_profile"


def _stored_stats_reader(service: Any) -> Any:
    """A reader of one view's stored column stats (``view ai profile`` action ``stats``).

    The backend answers from the stats it stored after ingest / the last pipeline
    run: no job is queued and no query runs.
    """

    def read(view: dict[str, Any]) -> Any:
        dataset_id = (
            view.get("dataset_id") if view.get("dataset_id") is not None else view.get("ds_id")
        )
        return service.call(
            _PROFILE_SYMBOL,
            dataview_id=view.get("id"),
            dataset_id=dataset_id,
            action="stats",
        )

    return read


def _compact_view_list(
    service: Any,
    data: dict[str, Any],
    datasets: list[dict[str, Any]],
    document: dict[str, Any],
) -> dict[str, Any]:
    """Summarise a view-list result and turn any cut into a way to the next page."""
    views = [apply_column_renames(v) for v in data["dataviews"] if isinstance(v, dict)]
    by_id = {d.get("id"): d for d in datasets if isinstance(d, dict)}
    summary = compact_view_list(
        views, by_id, _stored_stats_reader(service), bool(document.get("all_columns"))
    )
    dropped = summary.pop("first_dropped_dataset", None)
    result: dict[str, Any] = {**summary, "order": document.get("sort") or "newest first"}
    for key in ("datasets_visited", "next_dataset_offset"):
        if key in data:
            result[key] = data[key]
    if dropped is not None:
        start = int(document.get("dataset_offset", 0))
        stop = [d.get("id") for d in datasets].index(dropped)
        result["next_dataset_offset"] = stop
        result["datasets_visited"] = stop - start
    if "next_dataset_offset" in result and not summary.get("views_omitted"):
        result["more"] = (
            f"Datasets from position {result['next_dataset_offset']} on were not read; "
            "pass dataset_offset to continue, or list one dataset with 'view list DATASET_ID'."
        )
    if summary.get("views_omitted"):
        result["more"] = (
            "Some views were cut to fit the output cap; list one dataset with "
            "'view list DATASET_ID' and page it with offset/limit."
        )
    return result


def _view_list_across_project(
    service: Any,
    view_list_symbol: str,
    document: dict[str, Any],
    project_id: int,
    compact: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Aggregate dataviews from every dataset in the project (paged).

    Starts at ``dataset_offset`` (default 0) into the project's dataset
    list, pulling whole per-dataset view pages until either every dataset
    has been visited, at least ``_VIEW_LIST_ALL_DATASETS_MIN_VIEWS`` views
    have been collected, or ``_VIEW_LIST_ALL_DATASETS_MAX_VISITS`` datasets were
    read. ``next_dataset_offset`` names where to resume when the project holds
    more datasets than were visited. Returns the result and
    the project's dataset records (with the summary fields when ``compact``).
    """
    dataset_offset = int(document.get("dataset_offset", 0))
    list_kwargs: dict[str, Any] = {"project_id": project_id}
    if compact:
        list_kwargs["fields"] = DATASET_LIST_FIELDS
    datasets_page = service.call(_DATASETS_LIST_ALL_SYMBOL, **list_kwargs)
    datasets = datasets_page.get("datasets", []) if isinstance(datasets_page, dict) else []
    view_kwargs: dict[str, Any] = {}
    _forward_optional(document, view_kwargs, ("sort",))
    dataviews: list[Any] = []
    visited = dataset_offset
    for index in range(dataset_offset, len(datasets)):
        dataset = datasets[index]
        visited = index + 1
        dataset_id = dataset.get("id") if isinstance(dataset, dict) else None
        if not isinstance(dataset_id, int):
            continue
        page = service.call(
            view_list_symbol, dataset_id=dataset_id, project_id=project_id, **view_kwargs
        )
        for item in page.get("dataviews", []) if isinstance(page, dict) else []:
            if isinstance(item, dict):
                item = {**item, "dataset_id": dataset_id}
            dataviews.append(item)
        if (
            len(dataviews) >= _VIEW_LIST_ALL_DATASETS_MIN_VIEWS
            or visited - dataset_offset >= _VIEW_LIST_ALL_DATASETS_MAX_VISITS
        ):
            break
    result: dict[str, Any] = {"dataviews": dataviews, "datasets_visited": visited - dataset_offset}
    if visited < len(datasets):
        result["next_dataset_offset"] = visited
    return result, datasets


def view_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete several dataviews by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input()
    dataview_ids = _require_field(document, "dataview_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete dataviews of dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_ids=dataview_ids,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id (project-scoped)
# ---------------------------------------------------------------------------


def view_active_user_list(invocation: Invocation) -> HandlerResult:
    """List the active users on a dataview."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_active_user_mark(invocation: Invocation) -> HandlerResult:
    """Mark the caller as an active user on a dataview."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_parameter_context(invocation: Invocation) -> HandlerResult:
    """Get a dataview's parameter context."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def _dataview_metadata(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> list[dict[str, Any]]:
    """Return a dataview's column metadata records, or ``[]`` on any failure."""
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    except Exception:  # noqa: BLE001 -- labels are a presentation nicety, never fatal
        return []
    info = apply_column_renames(info)
    metadata = info.get(_METADATA_KEY) if isinstance(info, dict) else None
    if not isinstance(metadata, list):
        return []
    return [column for column in metadata if isinstance(column, dict)]


def _display_name_map(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> dict[str, str]:
    """Return an internal-name -> display-name map for a dataview.

    Data endpoints report internal column ids (``column_1``); the CLI presents
    the display names the user actually works with. Best-effort: any failure
    yields an empty map, so a data command still returns its rows.
    """
    mapping: dict[str, str] = {}
    for column in _dataview_metadata(service, dataset_id, dataview_id, project_id):
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            mapping[internal] = display
    return mapping


def _compile_query_filters(
    service: Any,
    dataset_id: int,
    dataview_id: int,
    project_id: int | None,
    document: dict[str, Any],
    kwargs: dict[str, Any],
    reads: ReadContext | None = None,
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    """Translate a data query's ``condition`` and ``columns`` to the wire format.

    The data route takes the backend condition shape (``{internal: {OP: ...}}``,
    the one every pipeline task uses), not the CLI's ``{column, operator,
    value}`` spec; forwarding the spec verbatim fails the job with "A clause can
    only have one key". The spec is compiled through the shared condition
    service and built against the view's display -> internal name and type
    maps, and ``columns`` given as display names are mapped the same way.
    Returns the internal -> display map and the display -> type map when
    metadata was fetched, so the row relabelling and checks can reuse them.
    """
    if CONDITION_KWARG not in document and "columns" not in document:
        return None, None
    metadata = _dataview_metadata(service, dataset_id, dataview_id, project_id)
    column_map: dict[str, str] = {}
    column_types: dict[str, str] = {}
    for column in metadata:
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            column_map[display] = internal
            if isinstance(column.get("type"), str):
                column_types[display] = column["type"]
    if CONDITION_KWARG in document:
        spec = document[CONDITION_KWARG]
        if reads is not None:
            reads.display_to_internal, reads.column_types = column_map, column_types
            spec = read_queries.resolve_text_date_conditions(reads, spec)
        compiled = compile_condition(spec)
        kwargs[CONDITION_KWARG] = compiled.build(column_map or None, column_types or None)
    columns = document.get("columns")
    if isinstance(columns, list):
        kwargs["columns"] = [column_map.get(c, c) if isinstance(c, str) else c for c in columns]
    if not metadata:
        return None, None
    return {internal: display for display, internal in column_map.items()}, column_types


def _relabel_columns(
    service: Any,
    dataset_id: int,
    dataview_id: int,
    project_id: int | None,
    payload: Any,
    mapping: dict[str, str] | None = None,
) -> Any:
    """Rewrite internal column ids to display names in a data/preview payload.

    Handles both shapes the API returns: a preview's ``{"columns": [...]}``
    header list, and a data page's ``{"data": [{col: value}, ...]}`` row dicts.
    System columns (see :data:`_SYSTEM_COLUMNS`) are dropped so output matches
    the columns the user works with. ``mapping`` may be supplied by a caller
    that already fetched it (avoids a second metadata request); otherwise it is
    fetched here, only when there is something to relabel.
    """
    if not isinstance(payload, dict):
        return payload
    columns = payload.get(_COLUMNS_KEY)
    # Preview uses a positional ``rows`` array, while data pages use a
    # ``data`` array of row objects. Keep both wire shapes distinct so preview
    # identity values can be trimmed without changing data-page handling.
    rows_key = "rows" if isinstance(payload.get("rows"), list) else _ROWS_KEY
    rows = payload.get(rows_key)
    has_header = isinstance(columns, list) and all(isinstance(c, str) for c in columns)
    has_rows = isinstance(rows, list) and any(isinstance(r, dict) for r in rows)
    if not (has_header or has_rows):
        return payload
    if mapping is None:
        mapping = _display_name_map(service, dataset_id, dataview_id, project_id)
    payload = dict(payload)
    if has_header and isinstance(columns, list):
        visible_columns = [c for c in columns if c not in _SYSTEM_COLUMNS]
        payload[_COLUMNS_KEY] = [mapping.get(c, c) for c in visible_columns]
        # Preview responses are positional rows.  The backend may append the
        # internal row identity value (``hash``) without appending a matching
        # header, notably after pipeline edits.  Only remove exactly one
        # trailing value; multiple extras indicate an unknown backend shape
        # and must remain visible for diagnosis rather than being discarded.
        if isinstance(rows, list):
            payload[rows_key] = [
                (
                    row[: len(visible_columns)]
                    if isinstance(row, list) and len(row) == len(visible_columns) + 1
                    else row
                )
                for row in rows
            ]
    if has_rows and isinstance(rows, list):
        payload[rows_key] = DataRows(
            (
                {mapping.get(k, k): v for k, v in row.items() if k not in _SYSTEM_COLUMNS}
                if isinstance(row, dict)
                else row
            )
            for row in rows
        )
    return payload


def view_preview(invocation: Invocation) -> HandlerResult:
    """Preview a dataview's rows and columns.

    Sensible defaults so no --input is needed: 50 rows, and every column (the
    preview endpoint otherwise hides columns beyond a narrow default, including
    ones a transform just added at the end of the schema). Override either with
    ``--input '{"rows": N, "cols": M}'``. The dataset is resolved from the view
    unless given as a trailing positional or a ``dataset_id`` --input field.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        # Fetch the display-name map once, up front: it drives both the column
        # relabel and the "show every column" default (its length is the real
        # column count, excluding system columns).
        mapping = _display_name_map(service, dataset_id, view_id, project_id)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
            "rows": document.get(_ROWS_INPUT_KEY, _DEFAULT_PREVIEW_ROWS),
        }
        cols = document.get(_COLS_INPUT_KEY)
        if cols is None and mapping:
            cols = len(mapping)
        if cols is not None:
            kwargs["cols"] = cols
        data = service.call(_symbol(invocation), **kwargs)
        data = _relabel_columns(service, dataset_id, view_id, project_id, data, mapping=mapping)
    return data, meta


def view_restore(invocation: Invocation) -> HandlerResult:
    """Restore a trashed dataview."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_trash(invocation: Invocation) -> HandlerResult:
    """Move one dataview to the project trash (reversible)."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_impact(invocation: Invocation) -> HandlerResult:
    """List what deleting a pipeline task or this whole view would affect (read-only).

    ``scope`` is ``task`` (then ``task_id`` is required) or ``view``. The dataset is
    resolved from the view unless given as a trailing positional or ``dataset_id``.
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
        "scope": _require_field(document, "scope"),
    }
    _forward_optional(document, kwargs, ("task_id",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_analyze(invocation: Invocation) -> HandlerResult:
    """List pipeline steps that can be dropped or moved without changing the result (read-only)."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_optimize(invocation: Invocation) -> HandlerResult:
    """Apply the safe pipeline findings, then wait for the rerun it queued.

    ``apply_rules`` limits the rules applied; omitted, every safe finding is applied.
    The result keeps the server's ``applied`` / ``skipped`` / step counts and adds
    ``job_state`` and ``job_result`` when a rerun job was queued.
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"optimize the pipeline of view {dataview_id}",
    )
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("apply_rules",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(_symbol(invocation), **kwargs)
        if isinstance(data, dict) and data.get("job_id") is not None:
            settled = service.wait_if_job({"job_id": data["job_id"]})
            data = {**data, "job_state": "success", "job_result": settled}
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_compare(invocation: Invocation) -> HandlerResult:
    """Compare dataviews pairwise: rows, column differences and checksums (read-only)."""
    document = invocation.load_input()
    pairs = _require_field(document, "pairs")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), pairs=pairs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_update(invocation: Invocation) -> HandlerResult:
    """Rename a view from the name input field; any other patch is refused.

    The dataview patch route leaves op, path and value unconstrained, so the only
    typed change offered is the rename (``replace`` on ``name``).
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    name = document.get("name")
    # ``dataview_id`` is the VIEW_ID positional, bound into the document by the contract.
    allowed = {"name", _DATASET_ID_FIELD, "dataview_id"}
    if set(document) - allowed or not isinstance(name, str) or not name.strip():
        raise _untyped_patch_error(invocation)
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            patch_data=[{"op": "replace", "path": "name", "value": name.strip()}],
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def _untyped_patch_error(invocation: Invocation) -> CliError:
    """The refusal for a view patch that is not the typed rename."""
    return CliError(
        code=CODE_UNSUPPORTED_CONTRACT,
        message="Raw dataview patch operations are not available through the CLI.",
        exit_status=EXIT_USAGE,
        hint=(
            "The OpenAPI operation leaves op, path, and value unconstrained. The typed "
            'change is the rename: view update VIEW_ID --input \'{"name": "New name"}\'.'
        ),
        details={
            "command_id": invocation.command_id,
            "blocker": "B09 DATAVIEW_INPUT_UNTYPED",
            "typed_alternatives": ['view update VIEW_ID --input \'{"name": "New name"}\''],
        },
        recovery_commands=[
            "mammoth schema find view",
            "mammoth schema get view.update",
        ],
    )


def view_data_get(invocation: Invocation) -> HandlerResult:
    """Fetch a dataview's data, waiting for the backing job to complete.

    The dataset is resolved from the view unless given as a trailing positional
    or a ``dataset_id`` --input field. ``offset`` (1-based) reads a later page
    through the query route. The result carries ``column_warnings`` when the
    rows show a text column of numbers or dates, or blanks.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    limit = document.get("limit", _DATA_GET_DEFAULT_LIMIT)
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
        }
        if document.get("offset") is not None:
            kwargs["offset"] = _int_field(document["offset"], "offset")
            page_limit = _int_field(limit, "limit")
            kwargs["limit"] = page_limit if page_limit > 0 else 400
            _forward_optional(document, kwargs, ("sequence",))
            data = service.call(_QUERY_DATA_SYMBOL, **kwargs)
        else:
            _forward_optional(document, kwargs, ("timeout", "poll_interval", "sequence"))
            data = service.call(_symbol(invocation), **kwargs)
        whole_view = document.get("offset") is None
        data = _relabel_and_check(
            service, dataset_id, view_id, project_id, data, whole_view=whole_view
        )
    page_size = _DATA_PAGE_ROWS if whole_view else kwargs["limit"]
    return _trim_rows(data, limit, page_size), meta


_QUERY_DATA_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.query_data"

_DATA_PAGE_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.get_data"
_MAX_UNMATCHED_KEYS = 5


def join_snapshot(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> dict[str, Any]:
    """Row count, columns and the first data page of a view (best effort)."""
    snapshot: dict[str, Any] = {"row_count": None, "columns": {}, "rows": []}
    try:
        info = apply_column_renames(
            service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=dataview_id,
                project_id=project_id,
            )
        )
        if isinstance(info, dict):
            snapshot["row_count"] = info.get("row_count")
            snapshot["columns"] = {
                c.get(_INTERNAL_NAME_KEY): c.get(_DISPLAY_NAME_KEY)
                for c in info.get(_METADATA_KEY) or []
                if isinstance(c, dict)
            }
            page = service.call(
                _DATA_PAGE_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=dataview_id,
                project_id=project_id,
            )
            page = _relabel_columns(
                service, dataset_id, dataview_id, project_id, page, snapshot["columns"]
            )
            rows = page.get(_ROWS_KEY) if isinstance(page, dict) else None
            snapshot["rows"] = [r for r in rows or [] if isinstance(r, dict)]
    except Exception:  # noqa: BLE001 -- the check is advice; the join already ran
        return snapshot
    return snapshot


def join_after_snapshot(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None, before: Any
) -> dict[str, Any]:
    """The view once the join has run, with ``unmatched_total`` counted over every row.

    A first-page sample says nothing about the rest of the view: a join whose
    first 400 rows all matched once reported a 100% match on a view where a
    quarter of the keys were blank.
    """
    wait_for_pipeline_to_settle(service, dataset_id, dataview_id)
    snapshot = join_snapshot(service, dataset_id, dataview_id, project_id)
    known = before.get("columns", {}) if isinstance(before, dict) else {}
    added = [internal for internal in snapshot["columns"] if internal not in known]
    if added:
        snapshot["unmatched_total"] = _count_all_blank(
            service, dataset_id, dataview_id, project_id, added
        )
        # A large view reads no row count right after the join; without one the
        # whole-view blank count was dropped for a first-page sample (UQA-RT8-01).
        if snapshot["row_count"] is None:
            snapshot["row_count"] = _count_rows(service, dataset_id, dataview_id, project_id)
    return snapshot


def _count_all_blank(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None, internals: list[str]
) -> int | None:
    """Rows where every one of ``internals`` is blank; ``None`` when the count could not run."""
    condition = compile_condition(
        {"and": [{"column": name, "operator": "IS_EMPTY"} for name in internals]}
    )
    return _count_rows(service, dataset_id, dataview_id, project_id, condition.build())


def _count_rows(
    service: Any,
    dataset_id: int,
    dataview_id: int,
    project_id: int | None,
    condition: dict[str, Any] | None = None,
) -> int | None:
    """Rows of the view matching ``condition`` (all rows without one); ``None`` when the
    count could not run."""
    try:
        result = service.call(
            read_queries.AGGREGATE_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
            aggregations=[{"function": "COUNT", "as_name": "rows"}],
            condition=condition,
        )
    except Exception:  # noqa: BLE001 -- the check is advice; the join already ran
        return None
    if not isinstance(result, dict):
        return None
    rows = [row for row in result.get("data") or [] if isinstance(row, dict)]
    return int(rows[0].get("agg_0") or 0) if rows else 0


def _match_counts(
    after: dict[str, Any], added: list[str], rows: list[dict[str, Any]]
) -> tuple[int, int, bool] | None:
    """``(unmatched, checked, whole_view)``: the full count when there is one, else the sample."""
    total, after_n = after.get("unmatched_total"), after.get("row_count")
    if isinstance(total, int) and isinstance(after_n, int) and after_n > 0:
        return total, after_n, True
    if not added or not rows:
        return None
    unmatched = sum(1 for r in rows if all(r.get(c) in (None, "") for c in added))
    return unmatched, len(rows), False


#: Most distinct key values read per side for a dry-run key overlap.
_JOIN_PREVIEW_KEYS = 10000


def _unmatched(counts: dict[Any, int], other: set[Any]) -> list[str]:
    """Keys of ``counts`` absent from ``other`` (blank keys always), most rows first."""
    missing = [k for k in counts if k in (None, "") or k not in other]
    missing.sort(key=lambda key: -counts[key])
    return [str(k) for k in missing[:_MAX_UNMATCHED_KEYS]]


def key_overlap(left_counts: dict[Any, int], right_counts: dict[Any, int]) -> dict[str, Any]:
    """Match rate of each side against the other (blank keys never match).

    ``unmatched_keys`` are left keys with no right partner, ``right_unmatched_keys``
    the reverse, each most rows first: both lists show a spelling mismatch
    (``EIRE`` here, ``Ireland`` there) that one side alone would hide.
    """
    right_keys, left_keys = set(right_counts), set(left_counts)
    total = sum(left_counts.values())
    matched = sum(
        n for key, n in left_counts.items() if key not in (None, "") and key in right_keys
    )
    right_total = sum(right_counts.values())
    right_matched = sum(
        n for key, n in right_counts.items() if key not in (None, "") and key in left_keys
    )
    return {
        "rows_checked": total,
        "matched_rows": matched,
        "unmatched_rows": total - matched,
        "match_rate": round(matched / total, 3) if total else None,
        "unmatched_keys": _unmatched(left_counts, right_keys),
        "right_rows_checked": right_total,
        "right_match_rate": round(right_matched / right_total, 3) if right_total else None,
        "right_unmatched_rows": right_total - right_matched,
        "right_unmatched_key_count": sum(
            1 for key in right_counts if key in (None, "") or key not in left_keys
        ),
        "right_unmatched_keys": _unmatched(right_counts, left_keys),
    }


def _key_values(
    service: Any, dataset_id: int, view_id: int, project_id: int | None, column: str
) -> tuple[dict[Any, int], bool]:
    """``({key value: rows}, truncated)`` of one display-named column, via one aggregate."""
    mapping, _types = _column_profile(service, dataset_id, view_id, project_id)
    internal = next((i for i, display in mapping.items() if display == column), column)
    result = service.call(
        read_queries.AGGREGATE_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=project_id,
        aggregations=[{"function": "COUNT", "as_name": "n"}],
        group_by=[internal],
        limit=_JOIN_PREVIEW_KEYS + 1,
    )
    rows = [r for r in (result or {}).get("data") or [] if isinstance(r, dict)]
    counts = {r.get("group_0"): int(r.get("agg_0") or 0) for r in rows[:_JOIN_PREVIEW_KEYS]}
    return counts, len(rows) > _JOIN_PREVIEW_KEYS


def join_dry_run_preview(
    service: Any,
    left: tuple[int, int],
    right: tuple[int, int],
    document: dict[str, Any],
    project_id: int | None,
) -> dict[str, Any]:
    """Key overlap of the join a dry run describes: reads both key columns, writes nothing.

    ``left``/``right`` are ``(dataset_id, view_id)``. Never raises: a failed
    read comes back as ``{"checked": False, "error": ...}``.
    """
    try:
        on = document.get("on")
        pair = on[0] if isinstance(on, list) and on and isinstance(on[0], dict) else {}
        if not pair.get("left") or not pair.get("right"):
            return {"checked": False, "error": "the join has no left/right key to compare"}
        left_counts, left_cut = _key_values(service, *left, project_id, str(pair["left"]))
        right_counts, right_cut = _key_values(service, *right, project_id, str(pair["right"]))
    except Exception as exc:  # noqa: BLE001 -- the dry run itself must still report
        return {"checked": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "checked": True,
        "left_key": pair["left"],
        "right_key": pair["right"],
        **key_overlap(left_counts, right_counts),
        "truncated": left_cut or right_cut,
        "note": (
            "Key overlap by exact value, before any write, for each side: a low match_rate "
            "or keys unmatched on both sides (EIRE / Ireland) mean compare type, case, "
            "padding and spelling of the two key columns, or ask the user how they relate."
        ),
    }


_RIGHT_CHECK_FIELDS = (
    "right_rows_checked",
    "right_match_rate",
    "right_unmatched_rows",
    "right_unmatched_key_count",
    "right_unmatched_keys",
)


def with_join_check(
    data: Any,
    before: Any,
    after: dict[str, Any],
    document: dict[str, Any],
    right: dict[str, Any] | None = None,
) -> Any:
    """Add ``join_check`` (row counts, columns added, match rate) to a join result.

    ``unmatched_rows`` counts rows where every added column is blank: for a
    LEFT join these are rows whose key found no match in the other view. It is
    counted over the whole view when ``after`` carries ``unmatched_total``
    (see :func:`join_after_snapshot`), else over the sampled first page.
    ``right`` is a :func:`join_dry_run_preview` of the same join: its right-side
    fields (keys only the other view has) are copied in, so a LEFT join does not
    hide them.
    """
    if not isinstance(data, dict) or not isinstance(before, dict):
        return data
    added = [
        name
        for internal, name in after.get("columns", {}).items()
        if internal not in before.get("columns", {}) and isinstance(name, str)
    ]
    rows = after.get("rows") or []
    check: dict[str, Any] = {
        "rows_before": before.get("row_count"),
        "rows_after": after.get("row_count"),
        "columns_added": added,
        "rows_checked": len(rows),
    }
    notes: list[str] = []
    on = document.get("on")
    left_key = None
    if isinstance(on, list) and on and isinstance(on[0], dict):
        left_key = on[0].get("left")
    counts = _match_counts(after, added, rows)
    if counts is not None:
        unmatched, checked, whole_view = counts
        check.update(
            unmatched_rows=unmatched,
            match_rate=round((checked - unmatched) / checked, 3),
            rows_checked=checked,
        )
        if unmatched:
            missing = [r for r in rows if all(r.get(c) in (None, "") for c in added)]
            keys = sorted({str(r.get(left_key)) for r in missing if left_key in r})
            check["unmatched_keys"] = keys[:_MAX_UNMATCHED_KEYS]
            notes.append(
                f"{unmatched} of {checked} rows found no match. If that is more "
                "than a few, compare the key columns in both views (type, case, "
                "padding) before you build on this; otherwise say so in your report."
            )
        if not whole_view:
            notes.append(f"Match rate is from the first {checked} rows only, not the whole view.")
    before_n, after_n = check["rows_before"], check["rows_after"]
    if isinstance(before_n, int) and isinstance(after_n, int):
        if after_n > before_n:
            notes.append(
                f"The join added {after_n - before_n} rows: a key repeats in the other "
                "view, so matching rows repeat. Totals over this view count them twice; "
                "use view transform lookup for one value per key."
            )
        elif after_n < before_n:
            notes.append(
                f"{before_n - after_n} rows had no match and were dropped "
                "(an INNER join keeps matched rows only)."
            )
    if right and right.get("checked"):
        check.update({k: right[k] for k in _RIGHT_CHECK_FIELDS})
        if right["right_unmatched_key_count"]:
            notes.append(
                f"{right['right_unmatched_key_count']} key(s) in the other view found no "
                "partner here (right_unmatched_keys lists the first ones); report them "
                "as well as the unmatched rows on this side."
            )
    if notes:
        check["notes"] = notes
    return {**data, "join_check": check}


def _column_profile(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> tuple[dict[str, str], dict[str, str]]:
    """One metadata read: internal-to-display names, and display name to type."""
    mapping: dict[str, str] = {}
    types: dict[str, str] = {}
    for column in _dataview_metadata(service, dataset_id, dataview_id, project_id):
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            mapping[internal] = display
            types[display] = str(column.get("type") or "")
    return mapping, types


def _relabel_and_check(
    service: Any,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
    data: Any,
    mapping: dict[str, str] | None = None,
    types: dict[str, str] | None = None,
    whole_view: bool = False,
) -> Any:
    """Relabel a data page to display names and add ``column_warnings`` and ``duplicates``.

    Only read-only data reads call this, so a dates-as-text finding carries no convert fix.

    The metadata read happens only when the page has rows and the caller has
    not read it already (one read serves both the names and the types).
    """
    rows = data.get(_ROWS_KEY) if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        data = _relabel_columns(service, dataset_id, view_id, project_id, data, mapping)
        return _with_column_warnings(data, types or {}, view_id, dataset_id, read_only=True)
    if mapping is None or types is None:
        mapping, types = _column_profile(service, dataset_id, view_id, project_id)
    data = _relabel_columns(service, dataset_id, view_id, project_id, data, mapping)
    data = _with_column_warnings(data, types, view_id, dataset_id, read_only=True)
    return _with_duplicates_fact(data, view_id, dataset_id, whole_view)


def _with_duplicates_fact(data: Any, view_id: int, dataset_id: int | None, whole_view: bool) -> Any:
    """Add ``duplicates``: the read's own statement about exact duplicate rows."""
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY), list):
        return data
    fact = duplicate_rows_fact(data[_ROWS_KEY], view_id, dataset_id, whole_view=whole_view)
    return {**data, "duplicates": fact} if fact is not None else data


#: Issue types ``column_warnings`` looks for; ``column_checks.checked`` names them.
COLUMN_CHECK_ISSUES = (
    "numbers_stored_as_text",
    "dates_stored_as_text",
    "variant_spellings",
    "renamed_label",
    "blank_values",
    "duplicate_rows",
)


def _with_column_warnings(
    data: Any,
    types: dict[str, str],
    view_id: int,
    dataset_id: int | None = None,
    read_only: bool = False,
) -> Any:
    """Add ``column_checks`` (always) and ``column_warnings`` (when found).

    ``column_checks`` says the page was checked, over how many rows and for
    which issues, so an absent ``column_warnings`` reads as "clean" and never
    as "not checked". A check that throws is reported in ``column_checks.error``.
    """
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY, []), list):
        return data
    checks, warnings = _check_columns(
        data.get(_ROWS_KEY) or [], types, view_id, dataset_id, read_only
    )
    out = {**data, "column_checks": checks}
    return {**out, "column_warnings": warnings} if warnings else out


def _check_columns(
    rows: list[Any],
    types: dict[str, str],
    view_id: int,
    dataset_id: int | None,
    read_only: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run ``column_warnings`` and describe what was checked (never raises)."""
    checks: dict[str, Any] = {
        "scope": "page",
        "rows_checked": len(rows),
        "checked": list(COLUMN_CHECK_ISSUES) if rows and types else [],
        "found": 0,
    }
    warnings: list[dict[str, Any]] = []
    if rows and types:
        try:
            warnings = column_warnings(rows, types, view_id, dataset_id, read_only)
        except Exception as exc:  # noqa: BLE001 -- a presentation aid must not fail the read
            checks["checked"] = []
            checks["error"] = f"{type(exc).__name__}: {exc}"
    checks["found"] = len(warnings)
    return checks, warnings


#: Rows a plain ``view data get`` returns unless ``limit`` says otherwise.
_DATA_GET_DEFAULT_LIMIT = 50

#: Rows the server returns per data read when no ``offset`` is given (its page size).
_DATA_PAGE_ROWS = 400


def _trim_rows(data: Any, limit: Any, page_size: int | None = None) -> Any:
    """Keep the first ``limit`` rows of a data page and say what was cut.

    The route returns one page of the view (``page_size`` rows at most); an
    agent reading back a transform needs a sample and the total. ``limit`` 0
    or a negative value means "all rows of the page". A page that came back
    full may have more rows behind it, so it is reported as truncated too.
    """
    if not isinstance(data, dict) or not isinstance(data.get(_ROWS_KEY), list):
        return data
    try:
        cap = int(limit)
    except TypeError:
        cap = _DATA_GET_DEFAULT_LIMIT
    except ValueError:
        cap = _DATA_GET_DEFAULT_LIMIT
    rows = data[_ROWS_KEY]
    total = len(rows)
    if cap <= 0 or total <= cap:
        page_full = page_size is not None and total >= page_size
        result = {**data, "rows_returned": total, "rows_total_in_page": total}
        result["truncated"] = page_full
        if page_full:
            result["more_rows_may_exist"] = "The page is full; read the next page with offset."
        return result
    return {
        **data,
        _ROWS_KEY: DataRows(rows[:cap]),
        "rows_returned": cap,
        "rows_total_in_page": total,
        "truncated": True,
    }


def view_data_query(invocation: Invocation) -> HandlerResult:
    """Query a dataview's data with optional filtering, sorting, and paging.

    The dataset is resolved from the view unless given as a trailing positional
    or a ``dataset_id`` --input field.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
        }
        _forward_optional(document, kwargs, ("sequence", "offset", "limit", "sort"))
        reads = ReadContext(
            service,
            dataset_id,
            view_id,
            project_id,
            {},
            {},
            document.get("sequence"),
            document.get("text_date_format"),
        )
        mapping, types = _compile_query_filters(
            service, dataset_id, view_id, project_id, document, kwargs, reads
        )
        data = service.call(_symbol(invocation), **kwargs)
        data = _relabel_and_check(service, dataset_id, view_id, project_id, data, mapping, types)
        columns = read_queries.condition_columns(document.get(CONDITION_KWARG))
        data = read_queries.with_observed_range(reads, data, columns)
        data = read_queries.with_assumptions(reads, data)
    return data, meta


def _resolved_aggregate_item(agg: dict[str, Any], column_map: dict[str, str]) -> dict[str, Any]:
    """Resolve one ``{column, function, as_name}`` input entry's column to its
    internal name and default its ``as_name``, ready to forward to the SDK.

    Function/column validity is the SDK's job (:meth:`DataviewsAPI.aggregate`
    raises ``MammothValidationError``, mapped to an ``invalid_arguments``
    envelope) — this only resolves the display name and computes the default
    label so the result can be relabeled below.
    """
    function = str(agg.get("function") or "").upper()
    column = agg.get("column")
    resolved: dict[str, Any] = {
        "function": function,
        "as_name": agg.get("as_name") or (f"{function}_{column}" if column else function),
    }
    if column:
        resolved["column"] = column_map.get(column, column)
    return resolved


def _build_pivot_fields(
    document: dict[str, Any], column_map: dict[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve ``aggregations``/``group_by`` into SDK kwargs and an as_map.

    The as_map (``agg_0``/``group_0``/... -> the display label) mirrors the
    internal-name scheme :func:`mammoth.api.dataviews._build_pivot_param`
    assigns from the same list, in the same order — keep the two in step.
    """
    aggregations = document.get("aggregations")
    if not isinstance(aggregations, list) or not aggregations:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="'aggregations' is required for a PIVOT and must be a non-empty list.",
            exit_status=EXIT_USAGE,
            hint='--input \'{"aggregations": [{"column": "Sales", "function": "SUM"}]}\'',
        )
    resolved_aggregations = [_resolved_aggregate_item(agg, column_map) for agg in aggregations]
    as_map = {f"agg_{index}": item["as_name"] for index, item in enumerate(resolved_aggregations)}
    fields: dict[str, Any] = {"aggregations": resolved_aggregations}
    group_by = document.get("group_by")
    if group_by:
        # A string groups by the column's values; {column, truncate|resolution}
        # buckets a DATE (DAY..YEAR) or NUMERIC column first, like Explore.
        columns = [item["column"] if isinstance(item, dict) else item for item in group_by]
        fields["group_by"] = [
            (
                {**item, "column": column_map.get(item["column"], item["column"])}
                if isinstance(item, dict)
                else column_map.get(item, item)
            )
            for item in group_by
        ]
        as_map.update({f"group_{index}": column for index, column in enumerate(columns)})
    return fields, as_map


def _build_metric_fields(
    document: dict[str, Any], column_map: dict[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve a ``metric`` field into SDK kwargs and an as_map."""
    metric = document.get("metric")
    if not isinstance(metric, dict):
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="'metric' is required and must be an object.",
            exit_status=EXIT_USAGE,
            hint='--input \'{"metric": {"column": "Sales", "function": "SUM"}}\'',
        )
    resolved = _resolved_aggregate_item(metric, column_map)
    return {"metric": resolved}, {"metric": resolved["as_name"]}


_METRIC_ANY_TYPE_FUNCTIONS = frozenset({"COUNT", "DISTINCT_COUNT"})


def _require_numeric_metric(
    document: dict[str, Any], column_types: dict[str, str], view_id: int
) -> None:
    """Refuse a METRIC the backend cannot compute: it stores a NUMERIC value,
    so only COUNT/DISTINCT_COUNT work on a non-numeric column."""
    metric = document.get("metric")
    if not isinstance(metric, dict):
        return
    column = metric.get("column")
    function = str(metric.get("function", "")).upper()
    column_type = column_types.get(str(column), "")
    if function in _METRIC_ANY_TYPE_FUNCTIONS or column_type in ("", "NUMERIC"):
        return
    if column_type == "TEXT":
        hint = (
            f"MIN/MAX of a TEXT column is alphabetical, never chronological. If '{column}' "
            f"holds dates, run: mammoth view data explore {view_id} {column} --input "
            '\'{"column_type": "DATE", "level": "YEAR"}\' for its range by year '
            "(the format is detected from the data and stated in the result)."
        )
    else:
        hint = (
            f"For the latest or earliest value run: mammoth view data explore {view_id} "
            f'{column} --input \'{{"column_type": "{column_type}", "level": "DAY", '
            '"sort": "value_desc", "limit": 1}\' (value_asc for the earliest).'
        )
    raise CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=f"A metric is a number: {function} of the {column_type} column '{column}' "
        "cannot be computed here.",
        exit_status=EXIT_USAGE,
        hint=hint,
    )


def _plain_text_date_groups(
    document: dict[str, Any], levels: dict[int, str], column_types: dict[str, str]
) -> dict[str, Any]:
    """The document with each CLI-bucketed group_by entry reduced to what the backend groups by.

    A TEXT date is grouped by its raw stored string; a DATE column with a ``part``
    by day. The CLI buckets the result afterwards.
    """
    if not levels:
        return document
    group_by = [
        _backend_group(item, column_types) if index in levels else item
        for index, item in enumerate(document["group_by"])
    ]
    return {**document, "group_by": group_by}


def _backend_group(item: dict[str, Any], column_types: dict[str, str]) -> Any:
    if column_types.get(str(item["column"])) == "TEXT":
        return item["column"]
    return {"column": item["column"], "truncate": "DAY"}


def _aggregate_range_columns(document: dict[str, Any], column_types: dict[str, str]) -> list[str]:
    """Columns an empty aggregate should report the observed range of."""
    columns = read_queries.condition_columns(document.get(CONDITION_KWARG))
    for item in document.get("group_by") or []:
        if isinstance(item, dict) and (item.get("truncate") or item.get("part")) is not None:
            columns.append(str(item["column"]))
    return list(dict.fromkeys(columns))


def _reject_order_on_metric(document: dict[str, Any]) -> None:
    if any(document.get(key) is not None for key in ("order_by", "top")):
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="'order_by' and 'top' rank the rows of a group-by; a single 'metric' has none.",
            exit_status=EXIT_USAGE,
            hint="Use 'aggregations' with 'group_by' to rank groups.",
        )


def _run_aggregate(
    reads: ReadContext,
    symbol: str,
    document: dict[str, Any],
    fields: dict[str, Any],
    order: tuple[list[list[str]] | None, int | None],
    levels: dict[int, str],
) -> Any:
    """Run the aggregate: on the backend, or (a TEXT-date group) bucketed in the CLI."""
    sort, top = order
    limit = top if top is not None else document.get("limit")
    kwargs: dict[str, Any] = {
        "dataset_id": reads.dataset_id,
        "dataview_id": reads.view_id,
        "project_id": reads.project_id,
        **fields,
    }
    condition = None
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        condition = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
        kwargs[CONDITION_KWARG] = condition
    _forward_optional(document, kwargs, ("sequence",))
    if levels:
        response = read_queries.pivot_with_text_dates(
            reads,
            aggregations=fields["aggregations"],
            group_by=fields["group_by"],
            levels=levels,
            condition=condition,
        )
        rows = read_queries.sort_locally(response["data"], sort)
        return {**response, "data": rows[:limit] if limit else rows}
    if sort:
        kwargs["sort"] = sort
    if limit is not None:
        kwargs["limit"] = limit
    data = reads.service.call(symbol, **kwargs)
    return read_queries.with_leader_share(reads, data, fields, condition, limit)


def view_data_aggregate(invocation: Invocation) -> HandlerResult:
    """Aggregate a dataview's data: a PIVOT group-by or a single METRIC value.

    Read-only: computes and returns the aggregated result without adding a
    task to the view's pipeline or otherwise changing it. Pass exactly one of
    ``aggregations`` (a PIVOT; ``group_by`` is optional) or ``metric`` (a
    METRIC). ``function`` is one of SUM, COUNT, AVG, MIN, MAX, STDDEV, DISTINCT_COUNT. An optional
    ``condition`` filters rows before aggregating, and ``sequence`` pins the
    read to a pipeline step (default: latest). ``order_by`` (result labels,
    ``"Total desc"``) with ``top`` ranks the groups on the backend (and adds
    ``share_of_total``: the filtered total and the share held by the first row and
    by the returned rows); a ``limit`` without ``order_by`` is flagged unordered.
    A ``truncate`` on a TEXT column of dates is bucketed here from the detected
    format, stated in ``text_dates``.
    A group_by ``{"column": ..., "part": weekday|month|quarter|year}`` on a DATE (or
    TEXT-date) column groups by the named part of the date -- ``Monday``..``Sunday``,
    ``January``..``December``, ``Q1``..``Q4``, the year -- in calendar order: the
    read-only way to answer by-weekday and by-month questions.
    Figures are rounded for display (2 decimals; 4 below 1).
    Never use ``view transform pivot`` just to read a number -- it mutates the
    view's pipeline.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    has_pivot = "aggregations" in document or "group_by" in document
    has_metric = "metric" in document
    if has_pivot == has_metric:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="Pass exactly one of 'aggregations' (a PIVOT group-by, 'group_by' optional) "
            "or 'metric' (a single METRIC value).",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        internal_to_display, column_types = _column_profile(
            service, dataset_id, view_id, project_id
        )
        display_to_internal = {
            display: internal for internal, display in internal_to_display.items()
        }
        reads = ReadContext(
            service,
            dataset_id,
            view_id,
            project_id,
            display_to_internal,
            column_types,
            document.get("sequence"),
            document.get("text_date_format"),
        )
        levels: dict[int, str] = {}
        if has_pivot:
            levels = read_queries.text_date_group_levels(document.get("group_by"), column_types)
            fields, as_map = _build_pivot_fields(
                _plain_text_date_groups(document, levels, column_types), display_to_internal
            )
        else:
            _reject_order_on_metric(document)
            _require_numeric_metric(document, column_types, view_id)
            fields, as_map = _build_metric_fields(document, display_to_internal)
        order = read_queries.parse_order(document, as_map)
        data = _run_aggregate(reads, _symbol(invocation), document, fields, order, levels)
        data = _relabel_columns(service, dataset_id, view_id, project_id, data, as_map)
        data = read_queries.mark_unordered(document, data)
        data = read_queries.with_observed_range(
            reads, data, _aggregate_range_columns(document, column_types), coverage=True
        )
        data = read_queries.with_assumptions(reads, data)
    return data, meta


def view_data_aggregate_rounded(invocation: Invocation) -> HandlerResult:
    """``view data aggregate`` as the user reads it: floats rounded (2 decimals; 4 below 1).

    ``view data compare`` calls :func:`view_data_aggregate` itself, at full precision.
    """
    data, meta = view_data_aggregate(invocation)
    return read_queries.round_result_rows(data), meta


def _compare_key_and_value_columns(document: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return the (key, value) display-column names an aggregate call over
    ``document`` will produce, without making the call -- mirrors the label
    rules :func:`_build_pivot_fields`/:func:`_build_metric_fields` apply.
    """
    group_by = document.get("group_by") or []
    key_columns = [item["column"] if isinstance(item, dict) else item for item in group_by]
    if "metric" in document:
        value_columns = [_resolved_aggregate_item(document["metric"], {})["as_name"]]
    else:
        value_columns = [
            _resolved_aggregate_item(agg, {})["as_name"] for agg in document.get("aggregations", [])
        ]
    return key_columns, value_columns


def _run_aggregate_for_compare(
    invocation: Invocation, view_id: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run ``view data aggregate``'s own handler against one view, for compare."""
    sub_invocation = dataclasses.replace(
        invocation, command_id="view.data.aggregate", extra_args=[str(view_id)], positionals={}
    )
    data, meta = view_data_aggregate(sub_invocation)
    rows = data.get(_ROWS_KEY, [])
    return (rows if isinstance(rows, list) else []), meta


def _index_by_key(
    rows: list[dict[str, Any]], key_columns: list[str]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row.get(column) for column in key_columns): row for row in rows}


def _require_matched_keys(
    keyed_a: dict[tuple[Any, ...], dict[str, Any]],
    keyed_b: dict[tuple[Any, ...], dict[str, Any]],
    key_columns: list[str],
    view_id_a: int,
    view_id_b: int,
) -> None:
    """Fail loud -- never silently drop -- when a key is on only one side."""
    only_a = sorted(keyed_a.keys() - keyed_b.keys(), key=str)
    only_b = sorted(keyed_b.keys() - keyed_a.keys(), key=str)
    if not only_a and not only_b:
        return

    def _describe(keys: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
        return [dict(zip(key_columns, key, strict=True)) for key in keys[:10]]

    raise CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=(
            f"view {view_id_a} and view {view_id_b} do not share the same "
            f"{'/'.join(key_columns) or 'rows'}: {len(only_a)} only in view {view_id_a}, "
            f"{len(only_b)} only in view {view_id_b}."
        ),
        exit_status=EXIT_USAGE,
        hint="compare only reports a row where both views have the key; reconcile or "
        "narrow with 'condition' before comparing.",
        details={"only_in_first": _describe(only_a), "only_in_second": _describe(only_b)},
    )


def _decimal_or_raise(value: Any, column: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=f"'{column}' is not numeric ({value!r}); compare only works on "
            "numeric aggregates.",
            exit_status=EXIT_USAGE,
        ) from exc


def _compare_rows(
    keyed_a: dict[tuple[Any, ...], dict[str, Any]],
    keyed_b: dict[tuple[Any, ...], dict[str, Any]],
    key_columns: list[str],
    value_columns: list[str],
) -> list[dict[str, Any]]:
    compared: list[dict[str, Any]] = []
    for key in sorted(keyed_a.keys(), key=str):
        row_a, row_b = keyed_a[key], keyed_b[key]
        entry: dict[str, Any] = dict(zip(key_columns, key, strict=True))
        for column in value_columns:
            value_a = _decimal_or_raise(row_a.get(column), column)
            value_b = _decimal_or_raise(row_b.get(column), column)
            entry[f"{column}_a"] = str(value_a)
            entry[f"{column}_b"] = str(value_b)
            entry[f"{column}_delta"] = str(value_a - value_b)
        compared.append(entry)
    return compared


def view_data_compare(invocation: Invocation) -> HandlerResult:
    """Compare the same PIVOT/METRIC aggregate across two views, joined by key.

    T2-WPP-W8: an agent subtracted two views' totals by hand and mis-stated the
    difference. Compare takes ``view data aggregate``'s exact input shape
    (``aggregations``/``group_by``, or ``metric``) and runs it against both
    views, joining the rows on the group-by key (or as a single row for a bare
    metric) and returning an exact Decimal delta per key -- never ask the
    caller to subtract. A key present on only one side fails loud instead of
    silently reporting a partial diff.
    """
    require_project(invocation)
    view_id_a = _require_int_positional_at(invocation, 0, "first view id")
    view_id_b = _require_int_positional_at(invocation, 1, "second view id")
    document = invocation.load_input() or {}
    key_columns, value_columns = _compare_key_and_value_columns(document)
    rows_a, meta = _run_aggregate_for_compare(invocation, view_id_a)
    rows_b, _meta_b = _run_aggregate_for_compare(invocation, view_id_b)
    keyed_a = _index_by_key(rows_a, key_columns)
    keyed_b = _index_by_key(rows_b, key_columns)
    _require_matched_keys(keyed_a, keyed_b, key_columns, view_id_a, view_id_b)
    compared = _compare_rows(keyed_a, keyed_b, key_columns, value_columns)
    return {_ROWS_KEY: compared}, meta


def _require_string_positional_at(invocation: Invocation, index: int, name: str) -> str:
    """Return the positional argument at ``index`` as a nonblank string, or raise."""
    if len(invocation.extra_args) <= index or not str(invocation.extra_args[index]).strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return str(invocation.extra_args[index])


def _explore_wants_text_dates(document: dict[str, Any], column: str, stored: str) -> bool:
    """Whether this explore buckets a TEXT column of dates; fail loud on a type it cannot honour.

    The column's stored type decides how it is read. A ``column_type`` that
    disagrees is refused with the reason (a read cannot re-type a column), except
    DATE over a TEXT column, which is parsed from the data. A bucket ``level`` on
    a TEXT column means the same.
    """
    requested = str(document.get("column_type") or "").upper()
    level = document.get("level")
    if requested and stored and requested != stored:
        if stored == "TEXT" and requested == "DATE":
            return True
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=f"column_type {requested} does not match '{column}', which is stored as "
            f"{stored}; a read cannot re-type a column.",
            exit_status=EXIT_USAGE,
            hint="Drop column_type (the stored type is used), or convert the column with "
            "'view transform convert-type' (a pipeline write).",
        )
    if level is not None and stored and stored not in ("DATE", "NUMERIC", "TEXT"):
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=f"'level' buckets a DATE, NUMERIC or TEXT-date column; '{column}' is {stored}.",
            exit_status=EXIT_USAGE,
        )
    return stored == "TEXT" and level is not None


def _explore_text_dates(
    reads: ReadContext, document: dict[str, Any], internal_column: str, metric: Any
) -> dict[str, Any]:
    """Explore a TEXT column of dates: count per ``level`` bucket, parsed from the data."""
    level = text_dates.require_level(document.get("level"))
    aggregations: list[dict[str, Any]] = [{"function": "COUNT", "as_name": "count"}]
    if metric is not None:
        aggregations.append(metric)
    condition = None
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        condition = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
    response = read_queries.pivot_with_text_dates(
        reads,
        aggregations=aggregations,
        group_by=[internal_column],
        levels={0: level},
        condition=condition,
    )
    page = (document.get("offset"), document.get("limit"))
    rows = read_queries.apply_explore_order(
        response["data"], document.get("sort"), page, bool(document.get("cumulative"))
    )
    return {**response, "data": rows}


def view_data_explore(invocation: Invocation) -> HandlerResult:
    """Explore one column: trend, distribution, or top values, like the web app's
    column Explore card.

    Read-only: computes and returns the result without adding a task to the
    view's pipeline or otherwise changing it. Buckets by the column's type --
    a DATE column by ``level`` (default "AUTO"; or DAY/WEEK/MONTH/QUARTER/
    YEAR/...) for a trend "over time"/"by month"/"by year"; a NUMERIC column
    by ``level`` resolution (default "AUTO") for a distribution/histogram; any
    other column (TEXT) as its top values by count, ``limit`` (default 20).
    A TEXT column of dates with a ``level`` (or ``column_type`` DATE) is parsed
    from the data -- the format is detected and stated in ``text_dates``, and an
    ambiguous or unreadable column fails loud.
    Every bucket carries ``count`` and ``percentage`` of the column's total.
    A TEXT column also carries ``spelling_variants``: how many groups of one value
    spelled several ways its values hold (``view data profile`` lists them).
    An optional ``metric`` ``{"column": ..., "function": ...}`` (SUM, COUNT,
    AVG, MIN, MAX, STDDEV or DISTINCT_COUNT) adds a second aggregate per bucket over another column,
    and an optional ``condition`` filters rows first -- same as ``view data
    aggregate``, which this command wraps for the raw PIVOT shape. A date range
    is one ``and`` condition (``>=`` a start, ``<=`` an end); one year is
    ``{"column": ..., "operator": "=", "value": 2017, "component": "year"}``.
    ``cumulative: true`` adds a running total of the metric (of ``count`` without
    one) over the buckets in date order, whatever ``sort`` or ``limit`` shows:
    the answer to "cumulative / running total through X". Figures are rounded for
    display (2 decimals; 4 below 1). Never use
    ``view transform pivot`` just to explore a column; it mutates the
    pipeline.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    column_arg = _require_string_positional_at(invocation, 1, "column")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document, 2)
        meta = _read_meta(service, invocation, auth.workspace_id, dataset_id, view_id, project_id)
        internal_to_display, column_types = _column_profile(
            service, dataset_id, view_id, project_id
        )
        display_to_internal = {
            display: internal for internal, display in internal_to_display.items()
        }
        internal_column = display_to_internal.get(column_arg, column_arg)
        column_type = column_types.get(column_arg, "")
        reads = ReadContext(
            service,
            dataset_id,
            view_id,
            project_id,
            display_to_internal,
            column_types,
            document.get("sequence"),
            document.get("text_date_format"),
        )
        bucket_dates = _explore_wants_text_dates(document, column_arg, column_type)
        as_map: dict[str, str] = {"group_0": "bucket", "agg_0": "count"}
        metric = document.get("metric")
        resolved_metric = None
        if isinstance(metric, dict):
            resolved_metric = _resolved_aggregate_item(metric, display_to_internal)
            as_map["agg_1"] = resolved_metric["as_name"]
        if document.get("cumulative"):
            as_map["cumulative"] = f"{as_map.get('agg_1', 'count')} (running total)"
        if bucket_dates:
            data = _explore_text_dates(reads, document, internal_column, resolved_metric)
        else:
            data = _explore_on_backend(
                invocation, reads, document, (internal_column, column_type), resolved_metric
            )
        data = _relabel_columns(service, dataset_id, view_id, project_id, data, as_map)
        range_columns = read_queries.condition_columns(document.get(CONDITION_KWARG))
        if bucket_dates:
            range_columns.append(column_arg)
        data = read_queries.with_observed_range(reads, data, list(dict.fromkeys(range_columns)))
        data = read_queries.with_assumptions(reads, data)
        if not bucket_dates:
            data = read_queries.with_variant_hint(reads, data, column_arg)
    return read_queries.round_result_rows(data), meta


def _explore_on_backend(
    invocation: Invocation,
    reads: ReadContext,
    document: dict[str, Any],
    column: tuple[str, str],
    metric: dict[str, Any] | None,
) -> Any:
    """Explore a DATE, NUMERIC or plain TEXT column through the SDK's own bucketing."""
    kwargs: dict[str, Any] = {
        "dataset_id": reads.dataset_id,
        "dataview_id": reads.view_id,
        "project_id": reads.project_id,
        "column": column[0],
        "column_type": column[1],
    }
    if metric is not None:
        kwargs["metric"] = metric
    if document.get(CONDITION_KWARG) is not None:
        spec = read_queries.resolve_text_date_conditions(reads, document[CONDITION_KWARG])
        kwargs[CONDITION_KWARG] = compile_condition(spec).build(
            reads.display_to_internal or None, reads.column_types or None
        )
    _forward_optional(
        document, kwargs, ("level", "sequence", "limit", "offset", "sort", "cumulative")
    )
    return reads.service.call(_symbol(invocation), **kwargs)


def view_exportable_config_get(invocation: Invocation) -> HandlerResult:
    """Get a dataview's exportable pipeline configuration."""
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    if view_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT, message="view id must be positive.", exit_status=EXIT_USAGE
        )
    document = invocation.load_input() or {}
    explicit_dataset = _int_positional_at(invocation, 1, "dataset id")
    if explicit_dataset is None and document.get("dataset_id") is not None:
        explicit_dataset = int(document["dataset_id"])
    if explicit_dataset is not None and explicit_dataset <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dataset id must be positive.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=view_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_exportable_config_apply(invocation: Invocation) -> HandlerResult:
    """Apply exactly one exportable config or clipboard item list."""
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    if view_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT, message="view id must be positive.", exit_status=EXIT_USAGE
        )
    document = invocation.load_input() or {}
    explicit_dataset = _int_positional_at(invocation, 1, "dataset id")
    if explicit_dataset is None and document.get("dataset_id") is not None:
        explicit_dataset = int(document["dataset_id"])
    if explicit_dataset is not None and explicit_dataset <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dataset id must be positive.",
            exit_status=EXIT_USAGE,
        )
    items = document.get("items")
    config = document.get("config")
    if (items is None) == (config is None):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Exactly one of 'items' or 'config' is required.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"apply exportable config to view {view_id}",
        target=str(view_id),
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "items": items,
            "config": config,
            "project_id": project_id,
        }
        _forward_optional(document, kwargs, ("insert_after_sequence", "is_paste_mode"))
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_create(invocation: Invocation) -> HandlerResult:
    """Colour cells in many columns by one threshold in a single command (columns + operator + value + color): each cell is judged by its own value. applies_to=row colours whole rows when any/all of the columns match.

    Per-cell means one rule per column, all made in this one call. A raw ``rule`` body still
    works instead.
    """  # noqa: E501
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    has_typed = any(field in document for field in cf_rules.TYPED_FIELDS)
    if "rule" in document and has_typed:
        raise CliError(
            code=cf_rules.CODE_INVALID_RULE,
            message="Pass either 'rule' or the typed fields (columns, operator, value, color).",
            exit_status=EXIT_USAGE,
        )
    if "rule" not in document and not has_typed:
        _require_field(document, "rule")
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        if has_typed:
            metadata = _dataview_metadata(service, dataset_id, dataview_id, project_id)
            column_map, column_types = _column_maps(metadata)
            rules = cf_rules.build_rules(document, column_map, column_types)
        else:
            cf_rules.validate_rule(document["rule"])
            rules = [document["rule"]]
        data = _create_cf_rules(service, invocation, rules, (dataset_id, dataview_id, project_id))
    return data, _meta(invocation, auth.workspace_id, project_id)


def _cf_sequence(rule: Any) -> int:
    return rule.get("SEQUENCE", -1) if isinstance(rule, dict) else -1


def _create_cf_rules(
    service: Any, invocation: Invocation, rules: list[dict[str, Any]], scope: tuple[Any, ...]
) -> Any:
    """POST each rule in turn; a mid-way failure names the rule ids already created.

    Every response is the dataview's whole rule map; the new rule has the highest SEQUENCE.
    """
    dataset_id, dataview_id, project_id = scope
    ids: list[str] = []
    data: Any = None
    for rule in rules:
        try:
            data = service.call(
                _symbol(invocation),
                dataset_id=dataset_id,
                dataview_id=dataview_id,
                rule=rule,
                project_id=project_id,
            )
        except DryRunStop as stop:
            stop.record["rules"] = rules  # every body that would be sent, not just the first
            raise
        except CliError as error:
            if ids:
                error.details = {**error.details, "created_rule_ids": ids}
                error.message += f" Rules already created before the failure: {ids}."
            raise
        if isinstance(data, dict) and data:
            ids.append(max(data, key=lambda k: _cf_sequence(data[k])))
    if len(rules) == 1:
        return data
    note = f"{len(rules)} rules, one per column, so each cell is coloured by its own value."
    return {"created_rule_ids": ids, "rules_created": len(rules), "note": note}


def _column_maps(metadata: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    """Display -> internal name and display -> type maps from a view's column metadata."""
    names: dict[str, str] = {}
    types: dict[str, str] = {}
    for column in metadata:
        internal = column.get(_INTERNAL_NAME_KEY)
        display = column.get(_DISPLAY_NAME_KEY)
        if isinstance(internal, str) and isinstance(display, str):
            names[display] = internal
            if isinstance(column.get("type"), str):
                types[display] = column["type"]
    return names, types


def view_conditional_format_delete_all(invocation: Invocation) -> HandlerResult:
    """Delete a conditional-format rule on a dataview. Prompt or ``--yes``.

    The release route deletes one rule per call and requires ``rule_id`` as a
    query parameter (``view conditional-format list`` shows the ids).
    """
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    rule_id = document.get("rule_id")
    if rule_id is None:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="This command requires the 'rule_id' input field.",
            exit_status=EXIT_USAGE,
            hint="List rules with 'view conditional-format list VIEW_ID', then pass "
            "--input '{\"rule_id\": ...}'.",
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete conditional-format rule {rule_id} on view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rule_id=rule_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_list(invocation: Invocation) -> HandlerResult:
    """List conditional-format rules on a dataview."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_conditional_format_update(invocation: Invocation) -> HandlerResult:
    """Update a conditional-format rule on a dataview. ``rule`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    rule = _require_field(document, "rule")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            rule=rule,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + checkpoint_id (project-scoped)
# ---------------------------------------------------------------------------


def view_checkpoint_create(invocation: Invocation) -> HandlerResult:
    """Create a checkpoint on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_delete(invocation: Invocation) -> HandlerResult:
    """Delete one checkpoint by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    checkpoint_id = _require_int_positional_at(invocation, 1, "checkpoint id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete checkpoint {checkpoint_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            checkpoint_id=checkpoint_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_get(invocation: Invocation) -> HandlerResult:
    """Get one checkpoint by id."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    checkpoint_id = _require_int_positional_at(invocation, 1, "checkpoint id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "checkpoint_id": checkpoint_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_list(invocation: Invocation) -> HandlerResult:
    """List checkpoints on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "sequence", "status"))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_checkpoint_update(invocation: Invocation) -> HandlerResult:
    """Update one checkpoint by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    checkpoint_id = _require_int_positional_at(invocation, 1, "checkpoint id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            checkpoint_id=checkpoint_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + data_check_id (project-scoped)
# ---------------------------------------------------------------------------


def view_data_check_create(invocation: Invocation) -> HandlerResult:
    """Create a data check on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_delete(invocation: Invocation) -> HandlerResult:
    """Delete one data check by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    data_check_id = _require_int_positional_at(invocation, 1, "data check id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete data check {data_check_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            data_check_id=data_check_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_get(invocation: Invocation) -> HandlerResult:
    """Get one data check by id."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    data_check_id = _require_int_positional_at(invocation, 1, "data check id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "data_check_id": data_check_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_list(invocation: Invocation) -> HandlerResult:
    """List data checks on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "sequence", "status"))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_data_check_update(invocation: Invocation) -> HandlerResult:
    """Update one data check by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    data_check_id = _require_int_positional_at(invocation, 1, "data check id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            data_check_id=data_check_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + derivative_id (project-scoped)
# ---------------------------------------------------------------------------


def view_derivative_create(invocation: Invocation) -> HandlerResult:
    """Create a derivative on a dataview. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_data(invocation: Invocation) -> HandlerResult:
    """Fetch data for one derivative by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    derivative_id = _require_int_positional_at(invocation, 1, "derivative id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            derivative_id=derivative_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_delete(invocation: Invocation) -> HandlerResult:
    """Delete one derivative by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    derivative_id = _require_int_positional_at(invocation, 1, "derivative id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete derivative {derivative_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            derivative_id=derivative_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_list(invocation: Invocation) -> HandlerResult:
    """List derivatives on a dataview."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_derivative_update(invocation: Invocation) -> HandlerResult:
    """Update one derivative by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    derivative_id = _require_int_positional_at(invocation, 1, "derivative id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            derivative_id=derivative_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataset_id + dataview_id + version_id (project-scoped)
# ---------------------------------------------------------------------------


def view_version_apply(invocation: Invocation) -> HandlerResult:
    """Apply one pipeline version by id."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            version_id=version_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_delete(invocation: Invocation) -> HandlerResult:
    """Delete one pipeline version by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete version {version_id} of view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            version_id=version_id,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_get(invocation: Invocation) -> HandlerResult:
    """Get one pipeline version by id."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "version_id": version_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields",))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_version_list(invocation: Invocation) -> HandlerResult:
    """List pipeline versions on a dataview, with optional filters from ``--input``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("fields", "sort", "limit", "offset", "name"))
    with open_service(invocation) as (service, auth):
        kwargs["dataset_id"] = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = _with_version_times(service.call(_symbol(invocation), **kwargs))
    return data, _meta(invocation, auth.workspace_id, project_id)


def _with_version_times(data: Any) -> Any:
    """Give each version a ``when`` with an explicit offset.

    ``created_at`` is naive UTC and the server-made ``name`` ("30-Sep-2026 11:17 AM")
    is that same UTC wall time, so neither can be shown to a user as local time.
    """
    versions = data.get("versions") if isinstance(data, dict) else None
    if not isinstance(versions, list):
        return data
    stamped = [
        {**v, "when": local_time(v.get("created_at"))} if isinstance(v, dict) else v
        for v in versions
    ]
    return {
        **data,
        "versions": stamped,
        "time_note": "created_at and the version name are UTC; `when` carries its offset.",
    }


def view_version_update(invocation: Invocation) -> HandlerResult:
    """Update one pipeline version by id. ``body`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    version_id = _require_int_positional_at(invocation, 1, "version id")
    document = invocation.load_input()
    body = _require_field(document, "body")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document, 2)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            version_id=version_id,
            body=body,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


# ---------------------------------------------------------------------------
# dataview_id (+ optional dataset_id), NOT project-scoped: ai, draft.command,
# pipeline.*, task.*
# ---------------------------------------------------------------------------


def view_ai_generate_data(invocation: Invocation) -> HandlerResult:
    """Generate synthetic data for a dataview with an AI prompt. ``prompt`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    prompt = _require_field(document, "prompt")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "prompt": prompt}
    assert document is not None
    _forward_optional(document, kwargs, ("no_of_rows", "columns", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_ai_generation_info(invocation: Invocation) -> HandlerResult:
    """Get the status/info of an AI data-generation run for a dataview."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_ai_profile(invocation: Invocation) -> HandlerResult:
    """Generate an AI profile for a dataview."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id", "action"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_draft_command(invocation: Invocation) -> HandlerResult:
    """Run a release-valid draft operation against a dataview.

    Submit and discard are persisted/destructive draft transitions and require
    exact target confirmation before the SDK is reached.
    """
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    command = _require_field(document, "command")
    if command not in _DRAFT_OPERATIONS:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The draft command must be one of: {', '.join(sorted(_DRAFT_OPERATIONS))}.",
            exit_status=EXIT_USAGE,
            hint=(
                "Use 'view draft status' to read state; submit/discard require "
                "--yes --confirm DATAVIEW_ID."
            ),
        )
    if command in {"submit", "discard"}:
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            target=str(dataview_id),
            action=f"{command} the draft for view {dataview_id}",
        )
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "command": command}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


#: Pipeline patch paths that throw work away: a discarded rule or draft, a reset view.
_DISCARDING_PATCH_PATHS = frozenset({"discard", "reset", "discard-changes"})


def _discards_pipeline_work(patches: Any) -> bool:
    """Whether any patch in ``patches`` is a ``discard``, ``reset`` or ``discard-changes``."""
    if not isinstance(patches, list):
        return False
    for patch in patches:
        path = str(patch.get("path", "")) if isinstance(patch, dict) else ""
        if path.strip("/").lower().replace("_", "-") in _DISCARDING_PATCH_PATHS:
            return True
    return False


def view_pipeline_edit(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to a dataview's pipeline. ``patches`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
    if _discards_pipeline_work(patches):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            target=str(dataview_id),
            action=f"discard or reset pipeline work of view {dataview_id}",
        )
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "patches": patches}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        service.call(_symbol(invocation), **kwargs)
        # edit_pipeline returns the immediate (possibly still-processing) state;
        # run/reset-class patches kick off async work, so block until the
        # pipeline reaches a terminal state and return that settled state. When
        # nothing is processing this returns the current state right away.
        wait_kwargs: dict[str, Any] = {"dataview_id": dataview_id}
        dataset_id = kwargs.get("dataset_id")
        if dataset_id is not None:
            wait_kwargs["dataset_id"] = dataset_id
        data = service.call(_WAIT_FOR_PIPELINE_SYMBOL, **wait_kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


#: OpenAPI ``PipelineInfo`` (the exact ``get_pipeline`` payload) pins
#: ``draft_mode`` as a top-level string enum and ``auto_run`` as a top-level
#: bool. "dirty" means unsubmitted draft changes are pending; ``auto_run``
#: false means new tasks stop short of computing. Both leave a dataview
#: looking finished when it is not (WPP/T3 evidence: agents that never ran
#: 'view pipeline get' had no way to notice either).
_DRAFT_MODE_DIRTY = "dirty"


def _pipeline_action_hint(view_id: int, data: dict[str, Any]) -> str | None:
    """Best-effort hint naming the exact command a stale pipeline needs."""
    if data.get("draft_mode") == _DRAFT_MODE_DIRTY:
        return (
            f"This view has an unsubmitted draft with pending changes; run "
            f"'mammoth view draft submit {view_id}' to apply them."
        )
    if data.get("auto_run") is False:
        return (
            f"Auto-run is off for this pipeline; new tasks will not compute "
            f"automatically. Run 'mammoth view pipeline rerun {view_id}' to "
            f"compute pending tasks now."
        )
    return None


def view_pipeline_get(invocation: Invocation) -> HandlerResult:
    """Get a dataview's full pipeline."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    hint = _pipeline_action_hint(dataview_id, data) if isinstance(data, dict) else None
    if hint is not None:
        data = {**data, "hint": hint}
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_items(invocation: Invocation) -> HandlerResult:
    """List a dataview's pipeline items, with optional filters from ``--input``."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(
        document, kwargs, ("dataset_id", "fields", "limit", "offset", "sort", "sequence", "status")
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_items_all(invocation: Invocation) -> HandlerResult:
    """Read all pipeline items through bounded, exact-parent pagination."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = dict(invocation.load_input() or {})
    # The schema advertises an optional trailing DATASET_ID positional that
    # falls back to the input field; honour both, and reject a disagreement.
    positional_parent = _int_positional_at(invocation, 1, "dataset id")
    if positional_parent is not None:
        if document.get("dataset_id") not in (None, positional_parent):
            raise CliError(
                code="ambiguous_resource_identity",
                message="Conflicting dataset ids identify different parent resources.",
                exit_status=EXIT_USAGE,
                hint="Pass one exact dataset id matching the target view.",
            )
        document["dataset_id"] = positional_parent
    if "dataset_id" not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="This command requires the exact parent dataset id.",
            exit_status=EXIT_USAGE,
            hint="Pass it as the trailing DATASET_ID positional or the 'dataset_id' input field.",
        )
    dataset_id = document["dataset_id"]
    if isinstance(dataset_id, bool) or not isinstance(dataset_id, int) or dataset_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'dataset_id' input field must be a positive integer.",
            exit_status=EXIT_USAGE,
        )
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(
        document,
        kwargs,
        ("dataset_id", "fields", "limit", "sort", "sequence", "status", "max_pages"),
    )
    for field in ("limit", "max_pages"):
        value = kwargs.get(field, 100 if field == "limit" else 1000)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"The '{field}' input field must be a positive integer.",
                exit_status=EXIT_USAGE,
            )
    if kwargs.get("limit", 100) > 100:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'limit' input field must be <= 100.",
            exit_status=EXIT_USAGE,
        )
    if kwargs.get("max_pages", 1000) > 1000:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'max_pages' input field must be <= 1000.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_rerun(invocation: Invocation) -> HandlerResult:
    """Rerun a dataview's pipeline, optionally from a given sequence."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("from_sequence", "dataset_id"))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        dataset_id = kwargs.get("dataset_id")
        if dataset_id is None:
            dataset_id = _resolve_dataset_id_for_settle(
                service, invocation, dataview_id, document, 1
            )
        before = _rows_before(service, dataset_id, dataview_id, invocation.project)
        fired = _end_of_pipeline_exports(
            service, dataview_id, dataset_id, with_blank_columns=invocation.dry_run
        )
        try:
            data = service.call(_symbol(invocation), **kwargs)
        except DryRunStop as stop:
            # The dry run's report names the exports the real run would fire, and
            # the destination columns each append would leave blank.
            stop.record["exports_fired"] = fired
            raise
        data = _settle_async_view_write(
            service, dataset_id, dataview_id, invocation.project, data, before
        )
    if fired and isinstance(data, dict):
        data = {**data, "exports_fired": fired}
    return data, _meta(invocation, auth.workspace_id, None)


#: Non-secret ``target_properties`` keys that say where an export writes.
_EXPORT_TARGET_HINT_KEYS = (
    "table",
    "host",
    "database",
    "TARGET_DS_ID",
    "DS_NAME",
    "SAVE_AS_DS_MODE",
    "emails",
)
_INTERNAL_DATASET_HANDLER = "internal_dataset"
_WRITE_INTO_EXISTING_MODES = ("APPEND_TO_DS", "REPLACE_IN_DS")


def _end_of_pipeline_exports(
    service: Any, dataview_id: int, dataset_id: int | None, *, with_blank_columns: bool = False
) -> list[dict[str, Any]]:
    """The live end-of-pipeline exports a rerun of this view fires again.

    A rerun re-sends every one of them to its destination (database, email, REST
    endpoint, another dataset), so the caller is told which, not just that the
    pipeline ran. Soft-deleted exports do not fire. ``with_blank_columns`` (dry run
    only) also reads the schemas to name the destination columns each append would
    leave blank; a real rerun makes no such reads.
    """
    listing = service.call(
        _EXPORTS_LIST_SYMBOL,
        dataview_id=dataview_id,
        dataset_id=dataset_id,
        end_of_pipeline=True,
    )
    fired: list[dict[str, Any]] = []
    source_columns: Any = None
    for export in getattr(listing, "exports", None) or []:
        if export.status is ExportStatus.DELETED:
            continue
        handler = getattr(export.handler_type, "value", export.handler_type)
        properties = export.target_properties or {}
        entry: dict[str, Any] = {
            "export_id": export.id,
            "handler_type": handler,
            "target": {
                key: properties[key] for key in _EXPORT_TARGET_HINT_KEYS if key in properties
            },
        }
        if with_blank_columns and _writes_into_existing_dataset(handler, properties):
            if source_columns is None:
                source_columns = _source_column_names(service, dataview_id, dataset_id)
            entry[BLANK_COLUMNS_FIELD] = _blank_destination_columns(
                source_columns,
                set(_target_dataset_schema(service, int(properties["TARGET_DS_ID"]))),
                properties.get("COLUMN_MAPPING"),
            )
        fired.append(entry)
    return fired


def _writes_into_existing_dataset(handler: Any, properties: dict[str, Any]) -> bool:
    """Whether an export appends or replaces into a dataset that already exists."""
    return (
        handler == _INTERNAL_DATASET_HANDLER
        and properties.get("TARGET_DS_ID") is not None
        and properties.get("SAVE_AS_DS_MODE") in _WRITE_INTO_EXISTING_MODES
    )


def _source_column_names(service: Any, dataview_id: int, dataset_id: int | None) -> set[str]:
    """The source view's column display names; unreadable is an error, never "none"."""
    columns = service.call_view(dataview_id, "columns", dataset_id=dataset_id)
    if not isinstance(columns, dict):
        raise CliError(
            code="append_schema_unreadable",
            message=f"Could not read view {dataview_id}'s columns before the append.",
            hint="Read the source view before appending from it.",
            details={"side": "source", "dataview_id": dataview_id},
        )
    return set(columns)


def _blank_destination_columns(
    source_names: set[str], target_names: set[str], column_mapping: Any
) -> list[str]:
    """The destination columns an append leaves NULL: in the target, fed by nothing.

    That is a target column that is neither a source column (matched by name) nor a
    ``column_mapping`` destination. The one rule behind both the export-create
    acknowledgement and the rerun report.
    """
    mapping = column_mapping if isinstance(column_mapping, dict) else {}
    return sorted(target_names - source_names - set(mapping.values()))


#: Seconds ``view pipeline wait`` waits when the caller names no ``timeout`` (the SDK's own
#: default is an hour, one request every few seconds for as long as it runs).
_PIPELINE_WAIT_TIMEOUT = 300.0


def view_pipeline_wait(invocation: Invocation) -> HandlerResult:
    """Wait for a dataview's pipeline to finish running.

    Waits up to ``_PIPELINE_WAIT_TIMEOUT`` seconds unless ``timeout`` says more,
    polling less often the longer it waits.
    """
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "timeout": _PIPELINE_WAIT_TIMEOUT}
    _forward_optional(document, kwargs, ("dataset_id", "timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_add(invocation: Invocation) -> HandlerResult:
    """Add a pipeline task to a dataview. ``task_spec`` is required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_spec": task_spec}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    # Imported here: view_ops imports this module for the brief record helpers.
    from mammoth_cli.commands.view_ops import (
        reject_pipeline_reference_errors,
        reject_task_runtime_error,
        require_expected_task_count,
        with_in_place_note,
    )

    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        require_expected_task_count(service, dataview_id, kwargs.get("dataset_id"), document)
        submitted_at = datetime.now(UTC)
        data = service.call(_symbol(invocation), **kwargs)
        reject_pipeline_reference_errors(service, dataview_id, kwargs.get("dataset_id"), data)
        reject_task_runtime_error(
            service, dataview_id, kwargs.get("dataset_id"), data, submitted_at
        )
    return with_in_place_note(data, dataview_id), _meta(invocation, auth.workspace_id, None)


def view_task_delete(invocation: Invocation) -> HandlerResult:
    """Delete one pipeline task by id. Prompt or ``--yes`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    task_id = _require_int_positional_at(invocation, 1, "task id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete task {task_id} of view {dataview_id}",
    )
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_id": task_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        dataset_id = kwargs.get("dataset_id")
        if dataset_id is None:
            dataset_id = _resolve_dataset_id_for_settle(
                service, invocation, dataview_id, document, 2
            )
        before = _rows_before(service, dataset_id, dataview_id, invocation.project)
        data = service.call(_symbol(invocation), **kwargs)
        data = _settle_async_view_write(
            service, dataset_id, dataview_id, invocation.project, data, before
        )
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_get(invocation: Invocation) -> HandlerResult:
    """Get one pipeline task by id."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    task_id = _require_int_positional_at(invocation, 1, "task id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_id": task_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_list(invocation: Invocation) -> HandlerResult:
    """List a dataview's pipeline tasks."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_preview(invocation: Invocation) -> HandlerResult:
    """Preview the effect of a pipeline task without persisting it. ``task_spec`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_spec": task_spec}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_update(invocation: Invocation) -> HandlerResult:
    """Update one pipeline task by id. ``task_spec`` is required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    task_id = _require_int_positional_at(invocation, 1, "task id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "task_id": task_id,
        "task_spec": task_spec,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        dataset_id = kwargs.get("dataset_id")
        if dataset_id is None:
            dataset_id = _resolve_dataset_id_for_settle(
                service, invocation, dataview_id, document, 2
            )
        before = _rows_before(service, dataset_id, dataview_id, invocation.project)
        data = service.call(_symbol(invocation), **kwargs)
        data = _settle_async_view_write(
            service, dataset_id, dataview_id, invocation.project, data, before
        )
    return data, _meta(invocation, auth.workspace_id, None)


# ---------------------------------------------------------------------------
# view.export.* (mixed: most project-scoped; csv and list are not)
# ---------------------------------------------------------------------------


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
    ``--input '{"output_path": "path.csv"}'``.

    Embedded (see ``mammoth_cli.runtime.embedded``), no file is written: the
    signed download URL is returned instead so the host can hand it to its
    user. ``output_path`` is refused in that case.
    """
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    if embedded.active():
        return _view_export_csv_embedded(invocation, dataview_id, document)
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("output_path", "timeout", "dataset_id"))
    with open_service(invocation) as (service, auth):
        _require_exact_parent(service, invocation, dataview_id, kwargs)
        data = service.call(_symbol(invocation), **kwargs)
    # The SDK returns a Path; render it as a string so the written location is
    # visible in every output mode and serializes cleanly to JSON.
    return {"output_path": str(data)}, _meta(invocation, auth.workspace_id, None)


def _view_export_csv_embedded(
    invocation: Invocation, dataview_id: int, document: dict[str, Any]
) -> HandlerResult:
    """``view.export.csv`` for an embedded call: never writes a local file."""
    if "output_path" in document:
        raise CliError(
            code=CODE_UNSUPPORTED_CONTRACT,
            message="output_path is not supported here; files are not written in embedded mode.",
            exit_status=EXIT_USAGE,
            hint="Drop output_path -- an embedded call returns a download_url instead.",
        )
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("timeout", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call("mammoth.api.exports.ExportsAPI.to_csv_url", **kwargs)
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
    if dataset_id is not None:
        kwargs["dataset_id"] = dataset_id
    with open_service(invocation) as (service, auth):
        if kwargs.get("dataset_id") is None:
            # A remembered parent spares the SDK its scan of every dataset.
            remembered = parents.lookup(_profile_name(invocation), auth.workspace_id, dataview_id)
            if remembered is not None:
                kwargs["dataset_id"] = remembered
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


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

# The SDK exposes these destinations as typed helpers on ``View.export``.  A
# generic ``view export create`` cannot stand in for them: the helpers have
# destination-specific required fields, secret handling, and safety policy.
# Keep the allow-list here deliberately closed so a misspelled input field can
# never silently become an arbitrary ``**kwargs`` export option.
_SPECIAL_EXPORTS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "view.export.dataset": (
        "to_dataset",
        ("dataset_name",),
        (),
    ),
    "view.export.managed-s3": ("to_s3", (), ()),
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


def _reject_export_into_draft(service: Any, dataview_id: int, dataset_id: int) -> None:
    """Refuse a dataset export on a view whose changes are held in a draft.

    With auto-run off the view keeps new pipeline changes in a draft, so the
    export would only be staged and write nothing; the SDK then waits out its
    whole timeout for a write that cannot happen (eval T1-O-11).
    """
    pipeline = service.call(_PIPELINE_GET_SYMBOL, dataview_id=dataview_id, dataset_id=dataset_id)
    draft_mode = pipeline.get("draft_mode") if isinstance(pipeline, dict) else None
    if draft_mode in (None, "off"):
        return
    raise CliError(
        code="view_in_draft",
        message=(
            f"View {dataview_id} holds its changes in a draft (auto-run is off), so an "
            "export added now would be staged and write nothing."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Turn auto-run on with mammoth view draft auto-run {dataview_id} --input "
            "'{\"enabled\": true}', add the export, then turn auto-run off again if the "
            f"dataset should only update when asked (mammoth view pipeline rerun {dataview_id})."
        ),
        details={"dataview_id": dataview_id, "draft_mode": draft_mode},
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
        try:
            data = service.call_view(dataview_id, method, dataset_id=dataset_id, **kwargs)
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
    if table_note is not None:
        data = _with_recurrence_note(data, table_note)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _pending_dataset_export(error: CliError, view_id: int, project_id: int) -> dict[str, Any]:
    """A dataset export that was accepted but whose dataset id is not known yet.

    The export was submitted and the server is writing it (or has written it); only
    the lookup of its id ran out of time. That is not a failure, so say what is known
    and how to read the dataset when it lands, never an error.
    """
    name = error.details.get("dataset_name")
    pending: dict[str, Any] = {
        "status": "pending",
        "source_view_id": view_id,
        "project_id": project_id,
        "refreshes_on_pipeline_run": True,
        "note": (
            "The export was submitted and is still being written, so its dataset id is not "
            "known yet. Do not export again: that would create a second dataset. Look it up "
            f"in a moment with the next command (its source reads 'export of view {view_id}')."
        ),
    }
    if name is not None:
        pending["dataset_name"] = name
        pending["next"] = f"mammoth dataset find {shlex.quote(str(name))} --project {project_id}"
    if error.details.get("dataset_id") is not None:
        pending["dataset_id"] = error.details["dataset_id"]
    return pending


_EXPORTS_LIST_SYMBOL = "mammoth.api.exports.ExportsAPI.list"
_INTERNAL_DATASET_HANDLER_TYPE = "internal_dataset"


def _existing_internal_dataset_export(
    service: Any, dataview_id: int, dataset_id: int | None, target_ds_id: int
) -> Any | None:
    """This dataview's ``internal_dataset`` export already writing into
    ``target_ds_id``, if one exists (the most recent by id, when more than
    one somehow matches). ``None`` on no match.

    ``TARGET_DS_ID`` is compared as ``int``: the wire value can come back as
    a string, which would otherwise never match (mirrors the same int/str
    fix already applied to the SDK's own write-confirmation poll). A
    soft-deleted export (``status == ExportStatus.DELETED``) is never a
    match: the backend soft-deletes triggers rather than removing the row,
    and the list endpoint does not filter on status, so a deleted export
    would otherwise block every later export into that target forever.
    """
    listing = service.call(
        _EXPORTS_LIST_SYMBOL,
        dataview_id=dataview_id,
        dataset_id=dataset_id,
        handler_type=_INTERNAL_DATASET_HANDLER_TYPE,
    )
    exports = getattr(listing, "exports", None) or []
    matches = [
        export
        for export in exports
        if export.status is not ExportStatus.DELETED
        and (target := (export.target_properties or {}).get("TARGET_DS_ID")) is not None
        and int(target) == target_ds_id
    ]
    return max(matches, key=lambda export: export.id or 0) if matches else None


def _hidden_column_names(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> list[str]:
    """Display names of the view's hidden columns, which a new-dataset export leaves out."""
    info = apply_column_renames(
        service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    )
    if not isinstance(info, dict):
        return []
    display = info.get("display_properties")
    hidden = display.get("HIDDEN_COLUMNS") if isinstance(display, dict) else None
    if not isinstance(hidden, list) or not hidden:
        return []
    names = {
        column.get(_INTERNAL_NAME_KEY): column.get(_DISPLAY_NAME_KEY) or column.get("name")
        for column in info.get(_METADATA_KEY) or []
        if isinstance(column, dict)
    }
    return [str(names.get(column) or column) for column in hidden]


def reject_dataset_export_conflicts(
    service: Any, dataview_id: int, dataset_id: int, target_ds_id: int | None
) -> None:
    """Refuse a dataset export (or crosstab) that cannot write, or would double-write.

    Not into the view's own dataset, not from a view holding its changes in a
    draft, and not into a target this view already exports into. Each dataset
    export creates its own PERSISTENT trigger on the view, which re-runs on
    every pipeline run; REPLACE_IN_DS/APPEND_TO_DS only touch that trigger's OWN
    rows, so a second export into the same target is a second writer, not a
    refresh -- the fix is to rerun the pipeline, not to export again.
    """
    if target_ds_id is not None and target_ds_id == dataset_id:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="target_ds_id equals the view's own dataset.",
            exit_status=EXIT_USAGE,
            hint=(
                "A view cannot write into its own dataset. Export to a new "
                "dataset name (omit target_ds_id), or target a different dataset."
            ),
            details={"dataset_id": dataset_id, "target_ds_id": target_ds_id},
        )
    _reject_export_into_draft(service, dataview_id, dataset_id)
    if target_ds_id is None:
        return
    existing_export = _existing_internal_dataset_export(
        service, dataview_id, dataset_id, target_ds_id
    )
    if existing_export is not None:
        raise CliError(
            code="export_already_exists",
            message=(
                f"View {dataview_id} already exports into dataset "
                f"{target_ds_id} (export {existing_export.id}). This export "
                "re-runs on every pipeline run, and REPLACE_IN_DS replaces only "
                "its own rows -- a second export into the same target duplicates "
                "rows instead of refreshing them."
            ),
            exit_status=EXIT_USAGE,
            hint="Refresh the target by rerunning the pipeline, not by exporting again.",
            recovery_commands=[f"mammoth view pipeline rerun {dataview_id}"],
            details={
                "dataview_id": dataview_id,
                "target_ds_id": target_ds_id,
                "export_id": existing_export.id,
            },
        )


_DATASET_GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get"


def _target_dataset_schema(service: Any, target_ds_id: int) -> dict[str, str]:
    """The target dataset's own schema: column display name -> type ('' if absent).

    ``dataset.get``'s ``data_schema`` is the dataset's base schema, not any
    view's live/rendered columns -- a view's own rename task can show a
    different display name than the dataset's schema still uses (evidence:
    a target view renamed 'Cust ID' -> 'cust_id' while the dataset's
    data_schema still said 'Cust ID'). The backend's own append-schema match
    (``match_existing_target_schema``) compares against this dataset-level
    schema, not a view's, so this check must too. An unreadable or
    malformed response is never treated as "no columns" -- fail loud,
    rather than let an append write past a check that could not actually
    run. The response nests the dataset under ``dataset``, and each schema
    column carries its name as ``c_name`` (``c_id`` is the internal id).
    """
    response = service.call(_DATASET_GET_SYMBOL, dataset_id=target_ds_id)
    dataset = response.get("dataset") if isinstance(response, dict) else None
    data_schema = dataset.get("data_schema") if isinstance(dataset, dict) else None
    if not isinstance(data_schema, list):
        raise CliError(
            code="append_schema_unreadable",
            message=f"Could not read target dataset {target_ds_id}'s schema before the append.",
            hint="Read the target dataset before appending to it.",
            details={"side": "target", "dataset_id": target_ds_id},
        )
    names: dict[str, str] = {}
    for column in data_schema:
        display_name = column.get("c_name") if isinstance(column, dict) else None
        if not isinstance(display_name, str):
            raise CliError(
                code="append_schema_unreadable",
                message=(f"Target dataset {target_ds_id}'s schema had a malformed column entry."),
                hint="Read the target dataset before appending to it.",
                details={"side": "target", "dataset_id": target_ds_id},
            )
        names[display_name] = str(column.get("c_type") or "")
    return names


def _reject_append_type_mismatch(
    source_types: Any,
    target_schema: dict[str, str],
    mapping: dict[str, str],
    ids: tuple[int, int],
) -> None:
    """Refuse an append where a column both sides name has a different type.

    The backend does not coerce: a same-named column of another type lands in
    a separate new column, splitting the data. Columns only on one side, or
    renamed through ``column_mapping``, are not compared; an unknown type
    (empty) on either side is not a mismatch.
    """
    if not isinstance(source_types, dict):
        return
    mismatched = {
        name: (str(source_types[name]).lower(), target_schema[name].lower())
        for name in sorted(source_types.keys() & target_schema.keys() - set(mapping))
        if source_types[name]
        and target_schema[name]
        and str(source_types[name]).lower() != target_schema[name].lower()
    }
    if not mismatched:
        return
    view_id, target_ds_id = ids
    listed = "; ".join(f"{n}: source {src}, target {tgt}" for n, (src, tgt) in mismatched.items())
    raise CliError(
        code="append_type_mismatch",
        message=(
            f"View {view_id} has column(s) whose type differs from target dataset "
            f"{target_ds_id}: {listed}. An append would create separate columns."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Run mammoth view transform convert-type on view {view_id} so each column "
            "matches the target type, then retry the export."
        ),
        details={"mismatched": {n: {"source": s, "target": t} for n, (s, t) in mismatched.items()}},
    )


def _reject_partial_append_mapping(
    source_names: set[str],
    target_names: set[str],
    mapping: dict[str, str],
    ids: tuple[int, int],
) -> None:
    """Refuse a non-empty append ``column_mapping`` that drops or invents columns.

    The backend maps every column by name when the mapping is empty, but uses
    a non-empty one as-is: unmapped source columns are not appended (their
    target cells stay NULL) and a destination the target lacks becomes a new
    column named after the source.
    """
    if not mapping:
        return
    unknown = {src: dest for src, dest in sorted(mapping.items()) if dest not in target_names}
    unmapped = sorted(source_names - set(mapping))
    if not unknown and not unmapped:
        return
    view_id, target_ds_id = ids
    problems = []
    if unknown:
        listed = ", ".join(f"{dest!r} (for {src!r})" for src, dest in unknown.items())
        problems.append(f"destination column(s) not in target dataset {target_ds_id}: {listed}")
    if unmapped:
        problems.append(f"source column(s) left unmapped and not appended: {', '.join(unmapped)}")
    raise CliError(
        code="append_mapping_incomplete",
        message=(
            f"column_mapping for appending view {view_id} into dataset {target_ds_id} would "
            f"corrupt the append: {'; '.join(problems)}. A non-empty column_mapping is used "
            "as-is: unmapped columns are not appended and an unknown destination creates a "
            "new column."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            "Omit column_mapping to map all columns by name, or map every source column to "
            f"an existing column of dataset {target_ds_id}."
        ),
        details={
            "unknown_destinations": unknown,
            "unmapped_source_columns": unmapped,
            "target_columns": sorted(target_names),
        },
    )


def _mapped_type_warnings(
    source_types: Any, target_schema: dict[str, str], mapping: dict[str, str]
) -> list[str]:
    """Warn where a mapped source column's type differs from its target column's."""
    if not isinstance(source_types, dict):
        return []
    return [
        f"mapped column {src!r} is {str(source_types[src]).lower()} but target column "
        f"{dest!r} is {target_schema[dest].lower()}"
        for src, dest in sorted(mapping.items())
        if source_types.get(src)
        and target_schema.get(dest)
        and str(source_types[src]).lower() != target_schema[dest].lower()
    ]


def _reject_append_schema_mismatch(
    service: Any,
    dataview_id: int,
    dataset_id: int | None,
    target_ds_id: int,
    column_mapping: Any,
) -> tuple[list[str], list[str]]:
    """Refuse an ``APPEND_TO_DS``/``REPLACE_IN_DS`` export into an existing target
    whose source has a column the target
    dataset's schema does not, and ``column_mapping`` does not cover.

    A non-empty ``column_mapping`` is stricter: the backend then copies only
    the mapped columns and turns an unknown destination into a new column, so
    every source column must be mapped to a column the target already has
    (``_reject_partial_append_mapping``).

    An append writes into rows the target dataset already has; a source
    column with no home in the target schema and no explicit mapping would
    otherwise reach the backend as a malformed write. Checked here, before
    the call, so the refusal costs nothing and names exactly what to fix.

    Returns the target-only column names (present in the target schema, not
    in the source, not a ``column_mapping`` destination) and the type
    warnings for mapped pairs -- both allowed, but worth a warning.
    """
    source_names = _source_column_names(service, dataview_id, dataset_id)
    target_schema = _target_dataset_schema(service, target_ds_id)
    target_names = set(target_schema)
    mapping = column_mapping if isinstance(column_mapping, dict) else {}
    # View.columns (mammoth/view.py) maps display name -> internal name; these
    # dict keys are display names, matching what the backend's own schema
    # match compares by -- never the internal ids in the dict's values.
    _reject_partial_append_mapping(source_names, target_names, mapping, (dataview_id, target_ds_id))
    source_only = sorted(source_names - target_names - set(mapping))
    target_only = _blank_destination_columns(source_names, target_names, mapping)
    source_types = service.call_view(dataview_id, "column_types", dataset_id=dataset_id)
    _reject_append_type_mismatch(source_types, target_schema, mapping, (dataview_id, target_ds_id))
    if source_only:
        raise CliError(
            code="append_schema_mismatch",
            message=(
                f"View {dataview_id} has column(s) the target dataset {target_ds_id} "
                f"does not: {', '.join(source_only)}."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                "Map these in column_mapping (source column -> an existing target "
                "column), or rename them in the source view to match the target schema."
            ),
            details={"source_only": source_only, "target_only": target_only},
        )
    return target_only, _mapped_type_warnings(source_types, target_schema, mapping)


def _dataset_view_info(
    service: Any, dataset_id: int, project_id: int | None
) -> dict[str, Any] | None:
    """Id, name, and row count of a dataset's current (most recent) view, best effort.

    Used right after ``view.export.dataset`` writes to ``dataset_id``: the
    id/name let the response carry the view an agent needs next instead of a
    'go list it' hint (an append never changes it), and the row count feeds
    ``rows_after`` -- one listing call instead of two. Any failure returns
    None; the caller falls back to the 'next' hint and skips ``rows_after``.
    """
    try:
        listing = service.call(_DATAVIEW_LIST_SYMBOL, dataset_id=dataset_id, project_id=project_id)
        views = listing.get("dataviews") if isinstance(listing, dict) else None
        if not isinstance(views, list) or not views or not isinstance(views[0], dict):
            return None
        view_id = views[0].get("id")
        if not isinstance(view_id, int):
            return None
    except Exception:  # noqa: BLE001 -- best effort; the caller's fallbacks still work
        return None
    row_count = views[0].get("row_count")
    return {
        "id": view_id,
        "name": views[0].get("name"),
        "row_count": int(row_count) if row_count is not None else None,
    }


#: Bound on the best-effort pipeline-settle wait before a row-count
#: read-back. This is advice for the caller, not the write itself, so it
#: must not turn a fast command into a slow one even when a recompute is
#: large.
_ROW_CHECK_SETTLE_TIMEOUT = 60.0

UNFINISHED_STATE = "unfinished"
JOB_FAILED_STATE = "job_failed"
_PIPELINE_GET_SYMBOL = "mammoth.api.pipeline.PipelineAPI.get_pipeline"
_TASK_LIST_SYMBOL = "mammoth.api.pipeline.PipelineAPI.list_tasks"
_ERROR_TRANSFORM_STATUSES = {"ERROR", "REFERROR"}
#: ``wait_for_pipeline`` polls the pipeline's ``state`` and can see it settle
#: back to ``ready`` even though the backend's own ``execution_state`` -- a
#: separate field -- already recorded the task that actually failed. Only
#: ``execution_state`` is trustworthy here.
_PIPELINE_ERROR_EXECUTION_STATES = frozenset({"runtime_error", "ref_error"})


def wait_for_pipeline_to_settle(
    service: Any, dataset_id: int, view_id: int, settle_timeout: float = _ROW_CHECK_SETTLE_TIMEOUT
) -> dict[str, Any] | None:
    """Bounded wait for a view's pipeline to reach a terminal state.

    A row-count read taken immediately after a write can catch the pipeline
    still recomputing and return a stale or missing count (evidence: a
    `view transform filter`/`view transform json-extract` whose result held
    0 rows still read back an unreadable count right after the write).
    Bounded so a slow recompute cannot turn a fast command into a slow one.
    Whichever way this ends the caller still reads the row count afterward.

    Returns the pipeline's problem, or ``None`` when it settled cleanly: its
    execution error (see :func:`_pipeline_execution_error`) if a fresh read
    finds one, so the caller can flag it even when the write's own envelope
    said ``status: done`` / ``pipeline_state: ready``; else, when the wait
    itself failed (a timeout, a failed read) and the pipeline is not known to
    have settled, ``execution_state: "unfinished"`` with the wait's error --
    never a silent success on a count read mid-run.
    """
    wait_error: str | None = None
    try:
        service.call(
            _WAIT_FOR_PIPELINE_SYMBOL,
            dataview_id=view_id,
            dataset_id=dataset_id,
            timeout=settle_timeout,
        )
    except CliError as exc:
        wait_error = exc.message
    error = _pipeline_execution_error(service, dataset_id, view_id)
    if wait_error is None:
        return error
    if error is None:
        return {"execution_state": UNFINISHED_STATE, "wait_error": wait_error}
    return {**error, "wait_error": wait_error}


def wait_for_followon_job(service: Any, write_result: Any) -> dict[str, Any] | None:
    """Wait for the job a write result names (``future_id``/``job_id``), if any.

    The backend runs the pipeline as a follow-on job; a readback taken before
    it finishes races it. Returns ``None`` when there is nothing to wait for or
    the job succeeded, else ``execution_state: "job_failed"`` with the job's own
    error text -- reported, never swallowed.
    """
    if not isinstance(write_result, dict) or not any(
        isinstance(write_result.get(key), int) for key in ("future_id", "job_id")
    ):
        return None
    try:
        service.wait_if_job(write_result)
    except CliError as exc:
        return {"execution_state": JOB_FAILED_STATE, "wait_error": exc.message}
    return None


def _pipeline_execution_error(service: Any, dataset_id: int, view_id: int) -> dict[str, Any] | None:
    """A settled pipeline's ``execution_state``, if it names an error.

    A failed read here must not be silently treated as "no error" -- that
    would report the write as verified when nobody actually confirmed it
    (fail loud, no silent fallbacks). It returns ``execution_state:
    "unknown"`` with a ``read_error``, which verify.py reports as
    unverified instead. ``service.call`` maps every SDK exception to
    :class:`CliError` (see ``MammothService.call``'s contract), so that is
    the one identifiable type caught here. When a task list read cheaply
    finds the failing task, its id and ``reference_errors.error_code``
    (evidence: transform_status ERROR, error_code 7000) are added; a failed
    read there is recorded as ``task_detail_error`` rather than swallowed.
    """
    try:
        pipeline = service.call(_PIPELINE_GET_SYMBOL, dataview_id=view_id, dataset_id=dataset_id)
    except CliError as exc:
        return {"execution_state": "unknown", "read_error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(pipeline, dict):
        return {
            "execution_state": "unknown",
            "read_error": f"the pipeline read returned {type(pipeline).__name__}, not a dict",
        }
    execution_state = pipeline.get("execution_state")
    if (
        not isinstance(execution_state, str)
        or execution_state.lower() not in _PIPELINE_ERROR_EXECUTION_STATES
    ):
        return None
    error: dict[str, Any] = {"execution_state": execution_state}
    task_id = pipeline.get("executing_task_id")
    if task_id is not None:
        error["task_id"] = task_id
    try:
        listing = service.call(_TASK_LIST_SYMBOL, dataview_id=view_id, dataset_id=dataset_id)
        tasks = listing.get("tasks") if isinstance(listing, dict) else None
        failing = next(
            (
                task
                for task in tasks or []
                if isinstance(task, dict)
                and task.get("transform_status") in _ERROR_TRANSFORM_STATUSES
            ),
            None,
        )
        if failing is not None:
            if failing.get("id") is not None:
                error["task_id"] = failing["id"]
            reference_errors = failing.get("reference_errors")
            error_code = (
                reference_errors.get("error_code") if isinstance(reference_errors, dict) else None
            )
            if error_code is not None:
                error["error_code"] = error_code
    except CliError as exc:
        error["task_detail_error"] = f"{type(exc).__name__}: {exc}"
    return error


def wait_for_view_row_count(
    service: Any,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
    write_result: Any = None,
    settle_timeout: float = _ROW_CHECK_SETTLE_TIMEOUT,
) -> tuple[Any, dict[str, Any] | None]:
    """A view's row count once its pipeline has settled, best effort.

    Returns ``(rows_after, pipeline_error)``. ``rows_after`` is ``None`` if
    the read still cannot be made; the caller (and
    :mod:`mammoth_cli.runtime.verify`) must treat that as unverified, never
    as a known count. ``pipeline_error`` is the settled pipeline's own
    execution error (see :func:`_pipeline_execution_error`), if any.
    """
    job_error = wait_for_followon_job(service, write_result)
    pipeline_error = wait_for_pipeline_to_settle(service, dataset_id, view_id, settle_timeout)
    pipeline_error = job_error or pipeline_error
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
    except Exception:  # noqa: BLE001 -- best effort; the write already ran
        return None, pipeline_error
    rows_after = info.get("row_count") if isinstance(info, dict) else None
    return rows_after, pipeline_error


def _row_count_now(service: Any, dataset_id: int, view_id: int, project_id: int | None) -> Any:
    """A view's row count, read directly with no settle wait.

    Raises the read's own :class:`CliError` rather than swallowing it -- the
    caller records it in ``row_check`` instead of silently reporting "no
    rows yet" for a read that never actually happened.
    """
    info = service.call(
        _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
    )
    return info.get("row_count") if isinstance(info, dict) else None


def _rows_before(
    service: Any, dataset_id: Any, view_id: int, project_id: int | None
) -> dict[str, Any] | None:
    """The view's row count read BEFORE an async write is sent.

    Read after the call, a small view may already have recomputed, so the
    "before" would be the new count and a real change would look like none.
    None when the parent dataset is unknown (the settle step is skipped then).
    """
    if dataset_id is None:
        return None
    try:
        return {"rows_before": _row_count_now(service, int(dataset_id), view_id, project_id)}
    except CliError as exc:
        return {"rows_before": None, "rows_before_error": f"{type(exc).__name__}: {exc}"}


def _settle_async_view_write(
    service: Any,
    dataset_id: Any,
    view_id: int,
    project_id: int | None,
    data: Any,
    before: dict[str, Any] | None,
) -> Any:
    """Turn an async view write's immediate response into a final one.

    ``view task delete``/``update`` and ``view pipeline rerun`` can return
    ``status: processing`` right away, before the pipeline has actually run
    (evidence: ``view task delete`` -> ``{"status":"processing",
    "type_of_modification":"discard_rule"}``); a caller -- and
    :mod:`mammoth_cli.runtime.verify`, which reports ``status`` verbatim --
    must never see that as the final outcome. Only runs when ``dataset_id``
    is known, like every other settle-and-check path; an unknown parent is
    skipped rather than guessed (verify.py still catches a leftover
    ``processing`` status either way).
    """
    if dataset_id is None or not isinstance(data, dict):
        return data
    dataset_id = int(dataset_id)
    row_check: dict[str, Any] = dict(before or {"rows_before": None})
    rows_after, pipeline_error = wait_for_view_row_count(service, dataset_id, view_id, project_id)
    row_check["rows_after"] = rows_after
    data = {**data, "row_check": row_check}
    if pipeline_error is not None:
        data["pipeline_error"] = pipeline_error
        # A pipeline still running (or unreadable) is not a failed one: keep the
        # write's own status, and let verify report the pipeline_error.
        if pipeline_error.get("execution_state") not in (UNFINISHED_STATE, "unknown"):
            data["status"] = "failed"
    elif data.get("status") == "processing":
        data["status"] = "done"
    return data


def _view_info_after_settling(
    service: Any, dataset_id: int, project_id: int | None
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """A dataset's current view info, re-read once its pipeline has settled.

    Used right after a `view.export.dataset` write, for a brand-new dataset
    or an existing ``target_ds_id`` alike: id/name/row_count all come from
    this settled read, not the discovery lookup that finds the view id, so
    a still-recomputing pipeline can never leave ``row_count`` stale.

    Returns ``(view_info, pipeline_error)`` -- ``pipeline_error`` is the
    settled pipeline's own execution error (see :func:`_pipeline_execution_error`),
    if any.
    """
    view_info = _dataset_view_info(service, dataset_id, project_id)
    if view_info is None:
        return None, None
    pipeline_error = wait_for_pipeline_to_settle(service, dataset_id, view_info["id"])
    return _dataset_view_info(service, dataset_id, project_id) or view_info, pipeline_error


_DATAVIEW_LIST_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.list"
#: Rows an upload shows of each new view (enough to see keys and formats).
_UPLOAD_SAMPLE_ROWS = 3


def _select_view(views: list[Any], view_id: int | None) -> dict[str, Any] | None:
    """The view with ``view_id``, or the first (most recent) one when none is named."""
    if view_id is None:
        return views[0]
    return next((v for v in views if isinstance(v, dict) and v.get("id") == view_id), None)


def upload_preview(
    service: Any, dataset_id: int, project_id: int | None, view_id: int | None = None
) -> dict[str, Any]:
    """A view of a dataset (the first unless ``view_id``): columns, types, sample rows, warnings.

    ``before_dashboard`` names the columns to add before any dashboard is
    made (revenue from a unit price and a quantity), since a dashboard does
    not see columns added after it.

    An agent that has just uploaded files tends to read the local copies
    instead of the data in Mammoth, and so misses what Mammoth made of them
    (a price read as TEXT, blanks). The upload result carries the answer.
    Best effort, but never silent: a preview that could not be built comes
    back as ``{"preview_error": reason}`` (no ``view_id``), and one that was
    built says so with ``column_checks`` and an always-present
    ``column_warnings`` list.
    """
    try:
        listing = service.call(_DATAVIEW_LIST_SYMBOL, dataset_id=dataset_id, project_id=project_id)
        views = listing.get("dataviews") if isinstance(listing, dict) else None
        if not isinstance(views, list) or not views or not isinstance(views[0], dict):
            return {"preview_error": f"dataset {dataset_id} has no view to preview"}
        chosen = _select_view(views, view_id)
        if chosen is None:
            return {"preview_error": f"dataset {dataset_id} has no view {view_id}"}
        # A dataset with more than one live view has one previewed here; the
        # rest are named (id + name) so a caller (``project.check``) can say
        # a view besides the one checked exists, rather than silently acting
        # on the single view this function happens to preview.
        other_views = [
            {"id": other.get("id"), "name": other.get("name")}
            for other in views
            if other is not chosen and isinstance(other, dict) and isinstance(other.get("id"), int)
        ]
        record = apply_column_renames(chosen)
        view_id = record.get("id")
        if not isinstance(view_id, int):
            return {"preview_error": f"dataset {dataset_id}'s first view has no id"}
        mapping: dict[str, str] = {}
        types: dict[str, str] = {}
        for column in record.get(_METADATA_KEY) or []:
            if not isinstance(column, dict):
                continue
            internal = column.get(_INTERNAL_NAME_KEY)
            display = column.get(_DISPLAY_NAME_KEY)
            if isinstance(internal, str) and isinstance(display, str):
                mapping[internal] = display
                types[display] = str(column.get("type") or "")
        page = service.call(
            _DATA_PAGE_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        page = _relabel_columns(service, dataset_id, view_id, project_id, page, mapping)
        rows = page.get(_ROWS_KEY) if isinstance(page, dict) else None
        rows = [row for row in rows or [] if isinstance(row, dict)]
    except Exception as exc:  # noqa: BLE001 -- a preview must never fail the upload
        return {"preview_error": f"{type(exc).__name__}: {exc}"}
    checks, warnings = _check_columns(rows, types, view_id, dataset_id)
    preview: dict[str, Any] = {
        "view_id": view_id,
        "view_name": record.get("name"),
        "row_count": record.get("row_count"),
        "columns": types,
        "sample_rows": rows[:_UPLOAD_SAMPLE_ROWS],
        "column_checks": {**checks, "scope": "first_page"},
        "column_warnings": warnings,
        "freshness": view_freshness(record),
    }
    try:
        text_numbers = [
            str(w.get("column"))
            for w in warnings
            if isinstance(w, dict) and w.get("issue") == "numbers_stored_as_text"
        ]
        hints = upload_hints(
            view_id, record.get(_METADATA_KEY) or [], rows, dataset_id, text_numbers
        )
    except Exception:  # noqa: BLE001
        hints = []
    if hints:
        preview["before_dashboard"] = {"warnings": hints, "note": UPLOAD_NOTE}
    if other_views:
        preview["other_views"] = other_views
    return preview


def view_profiles(
    service: Any, dataset_id: int, view_id: int, project_id: int | None
) -> list[dict[str, Any]] | None:
    """Column profile of a view (types and blank shares) for the dashboard check."""
    from mammoth_cli.services.dashboard_review import profiles_from_view

    try:
        info = apply_column_renames(
            service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=view_id,
                project_id=project_id,
            )
        )
        metadata = [c for c in (info or {}).get(_METADATA_KEY) or [] if isinstance(c, dict)]
        mapping = {
            c[_INTERNAL_NAME_KEY]: c[_DISPLAY_NAME_KEY]
            for c in metadata
            if isinstance(c.get(_INTERNAL_NAME_KEY), str)
            and isinstance(c.get(_DISPLAY_NAME_KEY), str)
        }
        page = service.call(
            _DATA_PAGE_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        page = _relabel_columns(service, dataset_id, view_id, project_id, page, mapping)
        rows = page.get(_ROWS_KEY) if isinstance(page, dict) else None
        return profiles_from_view(metadata, rows or [])
    except Exception:  # noqa: BLE001 -- advice only
        return None
