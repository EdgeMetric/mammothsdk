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

import inspect
from typing import Any

from mammoth.view import ViewExport

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.conditions import CONDITION_KWARG

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
        return int(field)
    _require_discovery_allowed(invocation, view_id)
    return int(service.call(_FIND_DATASET_SYMBOL, dataview_id=view_id))


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
    lookup = f"mammoth view get {view_id}{project} --output json --no-input"
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


def _meta(invocation: Invocation, workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a view command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


# ---------------------------------------------------------------------------
# view.list / view.bulk-delete (dataset-scoped, no dataview_id)
# ---------------------------------------------------------------------------


def view_list(invocation: Invocation) -> HandlerResult:
    """List dataviews for a dataset in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional_at(invocation, 0, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "sort"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


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


def _display_name_map(
    service: Any, dataset_id: int, dataview_id: int, project_id: int | None
) -> dict[str, str]:
    """Return an internal-name -> display-name map for a dataview.

    Data endpoints report internal column ids (``column_1``); the CLI presents
    the display names the user actually works with. Best-effort: any failure
    yields an empty map, so a data command still returns its rows.
    """
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL,
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            project_id=project_id,
        )
    except Exception:  # noqa: BLE001 -- labels are a presentation nicety, never fatal
        return {}
    metadata = info.get(_METADATA_KEY) if isinstance(info, dict) else None
    if not isinstance(metadata, list):
        return {}
    mapping: dict[str, str] = {}
    for column in metadata:
        if isinstance(column, dict):
            internal = column.get(_INTERNAL_NAME_KEY)
            display = column.get(_DISPLAY_NAME_KEY)
            if isinstance(internal, str) and isinstance(display, str):
                mapping[internal] = display
    return mapping


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
        payload[rows_key] = [
            (
                {mapping.get(k, k): v for k, v in row.items() if k not in _SYSTEM_COLUMNS}
                if isinstance(row, dict)
                else row
            )
            for row in rows
        ]
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
    return data, _meta(invocation, auth.workspace_id, project_id)


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


def view_update(invocation: Invocation) -> HandlerResult:
    """Reject free-form dataview patches until the API supplies typed variants."""
    raise CliError(
        code=CODE_UNSUPPORTED_CONTRACT,
        message="Raw dataview patch operations are not available through the CLI.",
        exit_status=EXIT_USAGE,
        hint=(
            "The OpenAPI operation leaves op, path, and value unconstrained. "
            "Use a separately typed view command when its schema covers the intended change."
        ),
        details={
            "command_id": invocation.command_id,
            "blocker": "B09 DATAVIEW_INPUT_UNTYPED",
            "typed_alternatives": [],
        },
        recovery_commands=[
            "mammoth schema find view --output json --no-input",
            "mammoth schema get view.update --output json --no-input",
        ],
    )


def view_data_get(invocation: Invocation) -> HandlerResult:
    """Fetch a dataview's data, waiting for the backing job to complete.

    The dataset is resolved from the view unless given as a trailing positional
    or a ``dataset_id`` --input field.
    """
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document)
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
        }
        _forward_optional(document, kwargs, ("timeout", "poll_interval"))
        data = service.call(_symbol(invocation), **kwargs)
        data = _relabel_columns(service, dataset_id, view_id, project_id, data)
    return data, _meta(invocation, auth.workspace_id, project_id)


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
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            "project_id": project_id,
        }
        _forward_optional(
            document, kwargs, ("sequence", "offset", "limit", "columns", CONDITION_KWARG, "sort")
        )
        data = service.call(_symbol(invocation), **kwargs)
        data = _relabel_columns(service, dataset_id, view_id, project_id, data)
    return data, _meta(invocation, auth.workspace_id, project_id)


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
    """Create a conditional-format rule on a dataview. ``rule`` is required."""
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


def view_conditional_format_delete_all(invocation: Invocation) -> HandlerResult:
    """Delete all conditional-format rules on a dataview. Prompt or ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"delete all conditional-format rules on view {dataview_id}",
    )
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
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
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


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


def view_pipeline_edit(invocation: Invocation) -> HandlerResult:
    """Apply JSON Patch operations to a dataview's pipeline. ``patches`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    patches = _require_field(document, "patches")
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


def view_pipeline_get(invocation: Invocation) -> HandlerResult:
    """Get a dataview's full pipeline."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
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
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_pipeline_wait(invocation: Invocation) -> HandlerResult:
    """Wait for a dataview's pipeline to finish running."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
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
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


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
        data = service.call(_symbol(invocation), **kwargs)
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
        data = service.call(_symbol(invocation), **kwargs)
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
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def view_export_csv(invocation: Invocation) -> HandlerResult:
    """Export a dataview to a local CSV file.

    With no --input the file is written to the current directory under an
    auto-generated name; the dataset is resolved from the view. Override with
    ``--input '{"output_path": "path.csv"}'``.
    """
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataview_id": dataview_id}
    _forward_optional(document, kwargs, ("output_path", "timeout", "dataset_id"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    # The SDK returns a Path; render it as a string so the written location is
    # visible in every output mode and serializes cleanly to JSON.
    return {"output_path": str(data)}, _meta(invocation, auth.workspace_id, None)


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
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_export_publish_db(invocation: Invocation) -> HandlerResult:
    """Publish a dataview to a database endpoint. Always requires ``--yes``."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    odbc_type = _require_field(document, "odbc_type")
    target_properties = _require_field(document, "target_properties")
    enforce_confirmation(
        invocation, policy=POLICY_YES_ALWAYS, action=f"publish-db on view {dataview_id}"
    )
    kwargs: dict[str, Any] = {
        "dataview_id": dataview_id,
        "odbc_type": odbc_type,
        "target_properties": target_properties,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
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
    allowed = explicit_fields | set(_SPECIAL_EXPORT_COMMON_FIELDS) | {_DATASET_ID_FIELD}
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise CliError(
            code="unknown_input_field",
            message=(
                f"Unknown input field(s) for '{invocation.command_id.replace('.', ' ')}': "
                f"{', '.join(unknown)}."
            ),
            exit_status=EXIT_USAGE,
            hint=f"Accepted fields: {', '.join(sorted(allowed - {_DATASET_ID_FIELD}))}.",
            details={"unknown": unknown, "accepted": sorted(allowed - {_DATASET_ID_FIELD})},
        )
    for field in required:
        _require_field(document, field)
    # Every typed destination is an external effect except internal dataset
    # creation, which is still a mutation. Requiring --yes keeps all helpers
    # promptless and makes the side effect explicit for agents.
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"export view {dataview_id} via {invocation.command_id.rsplit('.', 1)[-1]}",
    )
    kwargs = dict(document)
    kwargs.pop(_DATASET_ID_FIELD, None)
    with open_service(invocation) as (service, auth):
        if dataset_id is None:
            dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call_view(dataview_id, method, dataset_id=dataset_id, **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)
