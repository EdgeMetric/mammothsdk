"""Shared helpers for the ``view`` command package: id resolution, parent checks, envelope meta."""

from __future__ import annotations

from typing import Any

from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_RESOURCE_NOT_FOUND,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.invocation import Invocation

# Wire-shape keys returned by the dataview data/preview/metadata endpoints,
# named so the column-relabel logic and any future reader share one source of
# truth instead of repeating magic strings.
_COLUMNS_KEY = "columns"
_ROWS_KEY = "data"
_METADATA_KEY = "metadata"
_INTERNAL_NAME_KEY = "internal_name"
_DISPLAY_NAME_KEY = "display_name"
_DATAVIEW_GET_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.get"
_ANALYSIS_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.analysis"
_PIPELINE_ITEMS_ALL_SYMBOL = "mammoth.api.pipeline.PipelineAPI.items_all"
_DATASET_GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get"
# Public SDK resolver that finds the dataset containing a dataview, so the
# data-read commands can take the view id alone and fill the dataset for the
# caller. See :data:`mammoth_cli.services.positionals.POSITIONAL_OVERRIDES`.
_FIND_DATASET_SYMBOL = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_EXPLORE_PANEL_GET_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.explore_panel"
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


def _check_parent_matches(view_id: int, given: int, real: int) -> None:
    """Refuse a DATASET_ID that is not the view's parent, before any write."""
    if given == real:
        return
    raise CliError(
        code=CODE_INVALID_ARGUMENT,
        message=f"view {view_id} belongs to dataset {real}, not {given}",
        exit_status=EXIT_USAGE,
        hint=f"Run it again with dataset {real}, or leave DATASET_ID out: mammoth looks it up.",
        details={"view_id": view_id, "given_dataset_id": given, "dataset_id": real},
    )


def _view_parent_dataset_id(service: Any, invocation: Invocation, view_id: int) -> int:
    """The view's own dataset: the remembered parent, else one read of the view's row."""
    profile_name = _profile_name(invocation)
    workspace_id = getattr(service, "_workspace_id", None)
    remembered = parents.lookup(profile_name, workspace_id, view_id)
    if remembered is not None:
        return remembered
    dataset_id = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=view_id))
    parents.remember(profile_name, workspace_id, {view_id: dataset_id})
    return dataset_id


def _explain_swapped_ids(
    service: Any, error: CliError, invocation: Invocation, view_id: int, dataset_id: int
) -> None:
    """Raise a clear refusal when a not-found call was given DATASET_ID then VIEW_ID.

    The arguments are ``VIEW_ID [DATASET_ID]``; passing them the other way round
    only produces a bare 404. If the first number is really a view of the second,
    say so. Any other outcome leaves the original error to be re-raised.
    """
    if error.code != CODE_RESOURCE_NOT_FOUND:
        return
    try:
        parent = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=dataset_id))
    except CliError:
        return
    if parent != view_id:
        return
    raise CliError(
        code=CODE_INVALID_ARGUMENT,
        message=(
            f"{view_id} is a dataset id and {dataset_id} is its view; "
            "the order is VIEW_ID DATASET_ID"
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Run it again as: mammoth {invocation.command_path} {dataset_id} {view_id}"
            " (same options)"
        ),
        details={"view_id": dataset_id, "dataset_id": view_id},
    ) from error


def _verified_dataset_id(
    service: Any, invocation: Invocation, view_id: int, document: dict[str, Any]
) -> int:
    """The view's dataset for a write, so the caller never has to supply it.

    A DATASET_ID (positional or ``dataset_id`` input field) is checked against the
    view's real parent and refused when it differs; with none, the parent is looked up.
    """
    explicit = _int_positional_at(invocation, 1, "dataset id")
    if explicit is None and document.get(_DATASET_ID_FIELD) is not None:
        explicit = _int_field(document[_DATASET_ID_FIELD], _DATASET_ID_FIELD)
    try:
        real = _view_parent_dataset_id(service, invocation, view_id)
    except CliError as exc:
        if explicit is not None:
            _explain_swapped_ids(service, exc, invocation, view_id, explicit)
        raise
    if explicit is not None:
        _check_parent_matches(view_id, explicit, real)
    return real


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
    silently used the wrong one of two look-alike datasets never says so. Both
    carry their row count: a view's steps can filter rows, so a total read from
    it is not the dataset's total, and the two counts are how an agent sees that.
    """
    meta = _meta(invocation, workspace_id, project_id)
    view = service.call(
        _DATAVIEW_GET_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=project_id,
        fields="id,name,row_count",
    )
    # The read just proved this dataset holds the view; keep the pair so the
    # next command on it (a transform) needs no ``dataset_id`` of its own.
    parents.remember(_profile_name(invocation), workspace_id, {view_id: dataset_id})
    dataset = service.call(
        _DATASET_GET_SYMBOL,
        dataset_id=dataset_id,
        project_id=project_id,
        fields="id,name,stats",
    )
    return _finish_meta(invocation, meta, view, dataset, dataset_id, view_id)


def _read_meta_and_info(
    service: Any,
    invocation: Invocation,
    workspace_id: int,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """:func:`_read_meta` plus the view's full info, from one dataview read.

    The full record carries the name and row count the metadata needs, and the
    columns a data read relabels with, so the view is read once, not twice. The
    view and dataset reads are independent and run together.
    """
    meta = _meta(invocation, workspace_id, project_id)
    view, dataset = service.call_many(
        [
            (
                _DATAVIEW_GET_SYMBOL,
                {"dataset_id": dataset_id, "dataview_id": view_id, "project_id": project_id},
            ),
            (
                _DATASET_GET_SYMBOL,
                {"dataset_id": dataset_id, "project_id": project_id, "fields": "id,name,stats"},
            ),
        ]
    )
    for outcome in (view, dataset):
        if isinstance(outcome, CliError):
            raise outcome
    parents.remember(_profile_name(invocation), workspace_id, {view_id: dataset_id})
    info = apply_column_renames(view)
    info = info if isinstance(info, dict) else {}
    object.__setattr__(invocation, "read_info", info)
    return _finish_meta(invocation, meta, view, dataset, dataset_id, view_id), info


def _finish_meta(
    invocation: Invocation,
    meta: dict[str, Any],
    view: Any,
    dataset: Any,
    dataset_id: int,
    view_id: int,
) -> dict[str, Any]:
    """Fill ``meta`` with the dataset and view facts the two reads returned."""
    dataset = dataset.get("dataset", dataset) if isinstance(dataset, dict) else {}
    view = view if isinstance(view, dict) else {}
    stats = dataset.get("stats")
    meta["dataset"] = {
        "id": dataset_id,
        "name": dataset.get("name"),
        "row_count": stats.get("row_count") if isinstance(stats, dict) else None,
    }
    meta["view"] = {"id": view_id, "name": view.get("name"), "row_count": view.get("row_count")}
    # A read that goes async raises before it returns; the executor reads this.
    object.__setattr__(invocation, "read_meta", meta)
    return meta


# ---------------------------------------------------------------------------
# view.list / view.bulk-delete (dataset-scoped, no dataview_id)
# ---------------------------------------------------------------------------


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


def _page_offset(value: Any) -> int:
    """A 0-based ``offset`` input: a non-negative integer."""
    offset = _int_field(value, "offset")
    if offset < 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The 'offset' input field must be 0 or more (rows to skip), got {offset}.",
            exit_status=EXIT_USAGE,
            hint="The first page is offset 0; use next_command from the previous page.",
        )
    return offset


_QUERY_DATA_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.query_data"

_DATA_PAGE_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.get_data"
_MAX_UNMATCHED_KEYS = 5


_DATAVIEW_LIST_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.list"
