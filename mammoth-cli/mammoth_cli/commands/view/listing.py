"""View listing, bulk delete, active-user and parameter-context handlers."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _DATASET_GET_SYMBOL,
    _DATASET_ID_FIELD,
    _forward_optional,
    _int_positional_at,
    _meta,
    _profile_name,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
    apply_column_renames,
)
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.services.listing import DATASET_LIST_FIELDS, compact_view_list

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
#: Datasets whose views one wave of a project-wide ``view list`` reads at the same time.
_VIEW_LIST_WAVE = 5


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
            if compact:
                # The views and their dataset's name do not depend on each other:
                # one round trip's wait, not two.
                data, record = service.call_many(
                    [
                        (_symbol(invocation), kwargs),
                        (_DATASET_GET_SYMBOL, _dataset_get_kwargs(dataset_id, project_id)),
                    ]
                )
                if isinstance(data, CliError):
                    raise data
                if isinstance(record, CliError):
                    raise record
                datasets = [_dataset_record_from(record, dataset_id)]
            else:
                data = service.call(_symbol(invocation), **kwargs)
        parents.remember_records(
            _profile_name(invocation), auth.workspace_id, data, project_id=project_id
        )
        if compact and isinstance(data, dict) and isinstance(data.get("dataviews"), list):
            data = _compact_view_list(service, data, datasets, document)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _dataset_get_kwargs(dataset_id: int, project_id: int) -> dict[str, Any]:
    """Arguments of the dataset read a list summary shows its views under."""
    return {"dataset_id": dataset_id, "project_id": project_id, "fields": DATASET_LIST_FIELDS}


def _dataset_record_from(response: Any, dataset_id: int) -> dict[str, Any]:
    """The dataset record out of a ``dataset get`` response."""
    record = response.get("dataset", response) if isinstance(response, dict) else {}
    return {**record, "id": record.get("id", dataset_id)}


_PROFILE_SYMBOL = "mammoth.api.ai.AIAPI.generate_profile"


def _stored_stats_reader(service: Any) -> Callable[[list[dict[str, Any]]], list[Any]]:
    """A reader of the stored column stats of several views at once (``view ai profile``
    action ``stats``): one result per view, or the error that read raised.

    The backend answers from the stats it stored after ingest / the last pipeline
    run: no job is queued and no query runs.
    """

    def read(views: list[dict[str, Any]]) -> list[Any]:
        results: list[Any] = service.call_many(
            [
                (
                    _PROFILE_SYMBOL,
                    {
                        "dataview_id": view.get("id"),
                        "dataset_id": _view_dataset_id(view),
                        "action": "stats",
                    },
                )
                for view in views
            ]
        )
        return results

    return read


def _view_dataset_id(view: dict[str, Any]) -> Any:
    """The dataset a listed view belongs to (``dataset_id``, else the record's ``ds_id``)."""
    return view.get("dataset_id") if view.get("dataset_id") is not None else view.get("ds_id")


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
    for index, dataset_id, page in _view_pages_in_waves(
        service, view_list_symbol, datasets, dataset_offset, project_id, view_kwargs
    ):
        visited = index + 1
        if dataset_id is None:
            continue
        if isinstance(page, BaseException):
            raise page
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


def _view_pages_in_waves(
    service: Any,
    view_list_symbol: str,
    datasets: list[Any],
    dataset_offset: int,
    project_id: int,
    view_kwargs: dict[str, Any],
) -> Iterator[tuple[int, int | None, Any]]:
    """``(position, dataset id, view page or error)`` from ``dataset_offset`` on, in order.

    The views of :data:`_VIEW_LIST_WAVE` datasets are read at once, and a wave is only
    read when the caller asks for its first entry, so a walk that stops early never
    reads the waves after it. An entry that is not a dataset record has no id and no page.
    """
    window = range(
        dataset_offset, min(len(datasets), dataset_offset + _VIEW_LIST_ALL_DATASETS_MAX_VISITS)
    )
    for start in range(0, len(window), _VIEW_LIST_WAVE):
        wave = [(i, _dataset_id_of(datasets[i])) for i in window[start : start + _VIEW_LIST_WAVE]]
        readable = [dataset_id for _i, dataset_id in wave if dataset_id is not None]
        pages = iter(
            service.call_many(
                [
                    (
                        view_list_symbol,
                        {"dataset_id": dataset_id, "project_id": project_id, **view_kwargs},
                    )
                    for dataset_id in readable
                ]
            )
            if readable
            else []
        )
        for index, dataset_id in wave:
            yield index, dataset_id, next(pages) if dataset_id is not None else None


def _dataset_id_of(dataset: Any) -> int | None:
    """A dataset record's integer id, else None."""
    dataset_id = dataset.get("id") if isinstance(dataset, dict) else None
    return dataset_id if isinstance(dataset_id, int) else None


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
