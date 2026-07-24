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

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
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
    return int(service.call(_FIND_DATASET_SYMBOL, dataview_id=view_id))


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
    rows = payload.get(_ROWS_KEY)
    has_header = isinstance(columns, list) and all(isinstance(c, str) for c in columns)
    has_rows = isinstance(rows, list) and any(isinstance(r, dict) for r in rows)
    if not (has_header or has_rows):
        return payload
    if mapping is None:
        mapping = _display_name_map(service, dataset_id, dataview_id, project_id)
    payload = dict(payload)
    if has_header and isinstance(columns, list):
        payload[_COLUMNS_KEY] = [mapping.get(c, c) for c in columns if c not in _SYSTEM_COLUMNS]
    if has_rows and isinstance(rows, list):
        payload[_ROWS_KEY] = [
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
    """Apply JSON Patch operations to a dataview. ``patch_data`` is required."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input()
    patch_data = _require_field(document, "patch_data")
    assert document is not None
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            patch_data=patch_data,
            project_id=project_id,
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


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
    _forward_optional(document, kwargs, ("dataset_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, None)


def view_draft_command(invocation: Invocation) -> HandlerResult:
    """Run a raw draft pipeline command against a dataview. ``command`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    command = _require_field(document, "command")
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
        ),
    )
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
