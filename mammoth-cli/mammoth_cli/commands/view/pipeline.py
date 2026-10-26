"""AI, draft, pipeline and task handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import (
    _DRAFT_OPERATIONS,
    _WAIT_FOR_PIPELINE_SYMBOL,
    _forward_optional,
    _int_positional_at,
    _meta,
    _page_offset,
    _require_exact_parent,
    _require_field,
    _require_int_positional_at,
    _resolve_dataset_id_for_settle,
    _symbol,
)
from mammoth_cli.commands.view.export_dataset import (
    _EXPORTS_LIST_SYMBOL,
    _blank_destination_columns,
    _source_column_names,
    _target_dataset_schema,
)
from mammoth_cli.commands.view.settle import (
    _rows_before,
    _settle_async_view_write,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_FIELD,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import (
    open_service,
)
from mammoth_cli.services.append_blank_columns import (
    BLANK_COLUMNS_FIELD,
)
from mammoth_cli.services.paging import paging_block


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
    if "offset" in kwargs:
        kwargs["offset"] = _page_offset(kwargs["offset"])
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    data = _with_list_paging(
        data, invocation, f"mammoth view pipeline items {dataview_id}", kwargs, "items", 100
    )
    return data, _meta(invocation, auth.workspace_id, None)


def _with_list_paging(
    data: Any,
    invocation: Invocation,
    command: str,
    kwargs: dict[str, Any],
    key: str,
    default_limit: int,
) -> Any:
    """Give a list read the CLI paging block, from the request and the rows that came back.

    The route echoes ``offset`` as the next page's and leaves ``next`` empty, so
    neither is trusted; they are replaced by the block.
    """
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        return data
    limit = kwargs.get("limit")
    block = paging_block(
        command=command,
        project=invocation.project,
        offset=int(kwargs.get("offset") or 0),
        limit=int(limit) if limit is not None else default_limit,
        returned=len(data[key]),
    )
    rest = {k: v for k, v in data.items() if k not in ("offset", "next", "limit")}
    return {**rest, "paging": block}


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
    from mammoth.models.exports import ExportStatus

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
    if isinstance(data, dict) and "offset" in data:
        # The route is never asked for a later page, but echoes ``offset`` equal to its
        # page size on the first one; this is the first page.
        data = {**data, "offset": 0}
    return data, _meta(invocation, auth.workspace_id, None)


def view_task_preview(invocation: Invocation) -> HandlerResult:
    """Preview the effect of a pipeline task without persisting it. ``task_spec`` required."""
    dataview_id = _require_int_positional_at(invocation, 0, "dataview id")
    document = invocation.load_input()
    task_spec = _require_field(document, "task_spec")
    kwargs: dict[str, Any] = {"dataview_id": dataview_id, "task_spec": task_spec}
    assert document is not None
    _forward_optional(document, kwargs, ("dataset_id", "sample_size"))
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
