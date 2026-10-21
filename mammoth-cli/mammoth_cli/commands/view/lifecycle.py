"""Preview, restore, trash, impact, analyze, optimize, compare, update, explore-panel handlers."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.view._common import (
    _ANALYSIS_SYMBOL,
    _COLS_INPUT_KEY,
    _DATASET_GET_SYMBOL,
    _DATASET_ID_FIELD,
    _DATAVIEW_GET_SYMBOL,
    _DEFAULT_PREVIEW_ROWS,
    _EXPLORE_PANEL_GET_SYMBOL,
    _PIPELINE_ITEMS_ALL_SYMBOL,
    _ROWS_INPUT_KEY,
    HandlerResult,
    _forward_optional,
    _meta,
    _read_meta,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id,
    _symbol,
    _verified_dataset_id,
    apply_column_renames,
)
from mammoth_cli.commands.view.columns import (
    _dataview_metadata,
    _display_name_map,
    _relabel_columns,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import (
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
    require_project,
)
from mammoth_cli.services import view_analysis
from mammoth_cli.services.explore_cards import resolve_panel as resolve_explore_panel
from mammoth_cli.services.listing import DATASET_LIST_FIELDS


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
    """List pipeline steps that can be dropped or moved without changing the result (read-only).

    ``VIEW_ID`` may be several ids joined by commas. Each result carries the
    ``findings`` plus the view's name, dataset, rows, columns and state and its
    pipeline ``steps`` count, all read concurrently: the reads that always followed
    it. One id failing is an entry in ``errors``, not a failed call; a single id that
    fails fails the command, as before.
    """
    project_id = require_project(invocation)
    if not invocation.extra_args:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a view id argument.",
            exit_status=EXIT_USAGE,
            hint="Pass the view id as a positional argument.",
        )
    ids = view_analysis.view_ids(str(invocation.extra_args[0]))
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        outcomes = _analyze_views(service, invocation, ids, document, project_id)
    if len(ids) == 1:
        only = outcomes[ids[0]]
        if isinstance(only, CliError):
            raise only
        return only, _meta(invocation, auth.workspace_id, project_id)
    return view_analysis.many_result(ids, outcomes), _meta(
        invocation, auth.workspace_id, project_id
    )


def _analyze_views(
    service: Any,
    invocation: Invocation,
    ids: list[int],
    document: dict[str, Any],
    project_id: int,
) -> dict[int, dict[str, Any] | CliError]:
    """Analyze each view: its entry, or the error that stopped that id."""
    outcomes: dict[int, dict[str, Any] | CliError] = {}
    parents_of: dict[int, int] = {}
    for view_id in ids:
        try:
            parents_of[view_id] = _resolve_dataset_id(service, invocation, view_id, document)
        except CliError as error:
            outcomes[view_id] = error
    reads = _analysis_reads(parents_of, project_id)
    results = dict(zip(reads, service.call_many(list(reads.values())), strict=True))
    for view_id, dataset_id in parents_of.items():
        outcomes[view_id] = _analysis_outcome(results, view_id, dataset_id)
    return outcomes


def _analysis_reads(
    parents_of: dict[int, int], project_id: int
) -> dict[tuple[str, int], tuple[str, dict[str, Any]]]:
    """Every read an analysis needs, keyed by (kind, id): per view, and once per dataset."""
    reads: dict[tuple[str, int], tuple[str, dict[str, Any]]] = {}
    for view_id, dataset_id in parents_of.items():
        scope = {"dataset_id": dataset_id, "dataview_id": view_id}
        with_project = {**scope, "project_id": project_id}
        reads[("analysis", view_id)] = (_ANALYSIS_SYMBOL, with_project)
        reads[("view", view_id)] = (_DATAVIEW_GET_SYMBOL, with_project)
        reads[("steps", view_id)] = (_PIPELINE_ITEMS_ALL_SYMBOL, scope)
        reads[("dataset", dataset_id)] = (
            _DATASET_GET_SYMBOL,
            {"dataset_id": dataset_id, "project_id": project_id, "fields": DATASET_LIST_FIELDS},
        )
    return reads


def _analysis_outcome(
    results: dict[tuple[str, int], Any], view_id: int, dataset_id: int
) -> dict[str, Any] | CliError:
    """One view's entry from its reads; the first failed read is the id's error."""
    keys = [("analysis", view_id), ("view", view_id), ("steps", view_id), ("dataset", dataset_id)]
    for key in keys:
        failed = results[key]
        if isinstance(failed, CliError):
            return failed
    view = apply_column_renames(results[("view", view_id)])
    dataset = results[("dataset", dataset_id)]
    record = dataset.get("dataset", dataset) if isinstance(dataset, dict) else {}
    return view_analysis.analysis_entry(
        results[("analysis", view_id)],
        view if isinstance(view, dict) else {},
        {**record, "id": record.get("id", dataset_id)},
        view_analysis.step_count(results[("steps", view_id)]),
    )


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
        kwargs["dataset_id"] = _verified_dataset_id(service, invocation, dataview_id, document)
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


def _read_explore_panel(
    service: Any, symbol: str, dataset_id: int, dataview_id: int, project_id: int
) -> Any:
    """The Explore panel the caller saved on a view (``{}`` when none is saved)."""
    return service.call(
        symbol, dataset_id=dataset_id, dataview_id=dataview_id, project_id=project_id
    )


def view_explore_panel_get(invocation: Invocation) -> HandlerResult:
    """Read the Explore panel the caller saved on a view (empty when none is saved)."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, dataview_id, document)
        data = _read_explore_panel(
            service, _symbol(invocation), dataset_id, dataview_id, project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def _panel_to_write(
    service: Any, panel: Any, dataset_id: int, dataview_id: int, project_id: int
) -> dict[str, Any]:
    """The panel as the web app reads it; ``{"columns": ...}`` becomes a card per column."""
    if not isinstance(panel, dict):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message='"panel" must be an object.',
            exit_status=EXIT_USAGE,
        )
    saved = _read_explore_panel(
        service, _EXPLORE_PANEL_GET_SYMBOL, dataset_id, dataview_id, project_id
    )
    metadata = _dataview_metadata(service, dataset_id, dataview_id, project_id)
    return resolve_explore_panel(panel, metadata, saved)


def view_explore_panel_set(invocation: Invocation) -> HandlerResult:
    """Replace the caller's saved Explore panel; the result carries the panel read back after."""
    project_id = require_project(invocation)
    dataview_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    panel = _require_field(document, "panel")
    with open_service(invocation) as (service, auth):
        dataset_id = _verified_dataset_id(service, invocation, dataview_id, document)
        panel = _panel_to_write(service, panel, dataset_id, dataview_id, project_id)
        data = service.call(
            _symbol(invocation),
            dataset_id=dataset_id,
            dataview_id=dataview_id,
            panel=panel,
            project_id=project_id,
        )
        saved = _read_explore_panel(
            service, _EXPLORE_PANEL_GET_SYMBOL, dataset_id, dataview_id, project_id
        )
    return {**data, "panel": saved}, _meta(invocation, auth.workspace_id, project_id)


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
