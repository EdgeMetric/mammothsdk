"""Handlers for the ``view`` draft, transform, and view-CRUD commands.

Three kinds of command live here:

* ViewsResource CRUD (``view create``/``get``/``delete``) dispatch through the
  generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to
  the reviewed manifest ``sdk_symbol``, exactly like
  :mod:`mammoth_cli.commands.folder`.
* Draft commands (``view draft *``) and transform commands
  (``view transform *``) dispatch through
  :meth:`~mammoth_cli.services.protocol.MammothService.call_view`, which
  resolves the dataview into a rich ``View`` and calls the named public
  method. A ``condition`` field, when the underlying method accepts one, is
  forwarded unchanged as a plain spec; the service layer compiles it.

Command modules never import the SDK's condition builder or any enum type;
enum-typed fields are forwarded as the plain string given on ``--input``.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from mammoth_cli.commands.view import (
    _DATAVIEW_GET_SYMBOL,
    _FIND_DATASET_SYMBOL,
    BRIEF_VIEW_FIELDS,
    UNFINISHED_STATE,
    _dataview_metadata,
    _require_discovery_allowed,
    apply_column_renames,
    brief_view_record,
    join_after_snapshot,
    join_dry_run_preview,
    join_snapshot,
    wait_for_followon_job,
    wait_for_pipeline_to_settle,
    wait_for_refreshed_view,
    wait_for_view_row_count,
    with_join_check,
)
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_INVALID_ARGUMENTS,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition
from mammoth_cli.services.input_fields import TASK_COUNT_FIELD
from mammoth_cli.services.sql_check import check_sql_binds
from mammoth_cli.services.write_impact import (
    ImpactRead,
    Measure,
    empties_view_error,
    measure_bulk_replace,
    measure_duplicates,
    measure_fill_missing,
    measure_filter,
    measure_replace,
    no_op_error,
)

HandlerResult = tuple[Any, dict[str, Any]]

#: Error code for a task the backend accepted but could not bind to the view.
CODE_PIPELINE_REFERENCE_ERROR = "pipeline_reference_error"
#: Error code for a task that bound fine but errored while it ran.
CODE_TASK_RUNTIME_ERROR = "task_runtime_error"
_PIPELINE_SYMBOL = "mammoth.api.pipeline.PipelineAPI.get_pipeline"
_PIPELINE_ITEMS_SYMBOL = "mammoth.api.pipeline.PipelineAPI.items"
_PIPELINE_ITEMS_ALL_SYMBOL = "mammoth.api.pipeline.PipelineAPI.items_all"
_PIPELINE_ITEMS_FULL = "__full"
_ERROR_TRANSFORM_STATUSES = {"ERROR", "REFERROR"}
#: Tolerance for clock skew between this process and the server when deciding
#: whether a task's ``created_at`` falls at or after this call's submit time.
_TASK_CLOCK_SKEW = timedelta(seconds=5)
_REFERROR_REASON_HINTS = {
    "type mismatch": (
        "the task needs a different column type (find/replace and text operations "
        "take TEXT columns, math takes NUMERIC); convert-type the column first or "
        "use a transform for that type"
    ),
    "not available": "the column does not exist in the view at that point in the pipeline",
}


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


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Return the first positional argument parsed as an int, or raise usage."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _view_id(invocation: Invocation) -> int:
    """Return the target view id from the first positional argument."""
    return _require_int_positional(invocation, "view id")


def _resolve_exact_dataset_id(
    invocation: Invocation,
    view_id: int,
    document: dict[str, Any],
    *,
    required: bool = False,
    allow_missing: bool = False,
) -> int | None:
    """Resolve and reconcile optional exact parent identity for one view.

    Every supplied resource reference, positional, and input value must agree.
    Supplying the parent is important: ``ViewsResource.delete`` only invokes
    its legacy parent discovery when ``dataset_id`` is omitted, and that
    discovery can select a different dataset for the same view id.
    """
    resource = invocation.resource_ref
    if resource is not None and resource.view_id not in (None, view_id):
        raise CliError(
            code="invalid_resource_context",
            message="The resource reference view_id does not match the target view.",
            exit_status=EXIT_USAGE,
            hint="Use a resource reference for the same view id as the command target.",
        )
    if resource is not None and resource.project_id is not None:
        # Match the effective project the service will use: explicit --project
        # first, otherwise the selected profile's project.  Do not require a
        # project here; projectless view routes keep their existing semantics.
        effective_project = resolved_project(invocation)
        if effective_project is not None and resource.project_id != effective_project:
            raise CliError(
                code="invalid_resource_context",
                message=(
                    "The resource reference project does not match the effective project scope."
                ),
                exit_status=EXIT_USAGE,
            )
    raw_values = [
        value
        for value in (
            resource.dataset_id if resource is not None else None,
            invocation.positional("dataset_id"),
            document.get("dataset_id"),
        )
        if value is not None
    ]
    if not raw_values:
        if required:
            raise CliError(
                code="resource_identity_required",
                message="This operation requires the exact parent dataset id.",
                exit_status=EXIT_USAGE,
                hint="Pass DATASET_ID or include dataset_id in --input.",
            )
        if allow_missing:
            # The caller consults the local parent memory before deciding.
            return None
        # Transforms, exports and other non-read view commands must not fall
        # into the SDK's project-wide browse-and-probe discovery: on large
        # projects it can 500 on a folder or miss the view entirely and
        # surface as an opaque failure. Fail closed with the read that
        # supplies the parent.
        _require_discovery_allowed(invocation, view_id)
        return None
    try:
        values = {int(value) for value in raw_values}
    except (TypeError, ValueError) as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The dataset id must be an integer.",
            exit_status=EXIT_USAGE,
        ) from exc
    if len(values) != 1:
        raise CliError(
            code="ambiguous_resource_identity",
            message="Conflicting dataset ids identify different parent resources.",
            exit_status=EXIT_USAGE,
            hint="Pass one exact dataset id matching the target view.",
        )
    value = values.pop()
    if value <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The dataset id must be a positive integer.",
            exit_status=EXIT_USAGE,
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
    """Copy each present field from ``document`` into ``kwargs``, unchanged."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _meta(invocation: Invocation, workspace_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a view command.

    View routes are not project-scoped on the wire, but the project the call
    ran under (``--project`` or the profile's active project) is what the agent
    needs to correlate with its other envelopes, so it is reported when known.
    """
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": resolved_project(invocation),
    }


def _view_row_count(service: Any, dataset_id: int, view_id: int, project_id: int | None) -> Any:
    """Return a view's current row count via the cheapest read (best effort)."""
    try:
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
    except Exception:  # noqa: BLE001 -- the check is advice; the write already ran
        return None
    return info.get("row_count") if isinstance(info, dict) else None


def _dispatch_view(
    invocation: Invocation,
    view_id: int,
    method: str,
    *,
    before: Callable[[Any, int], Any] | None = None,
    after: Callable[[Any, int, Any, Any], Any] | None = None,
    prepare: Callable[[Any, int, dict[str, Any]], Any] | None = None,
    reduces_rows: bool = False,
    **kwargs: Any,
) -> HandlerResult:
    """Open the service, dispatch a View method call, and build the envelope.

    ``before(service, dataset_id)`` runs ahead of the call and its value is
    handed to ``after(service, dataset_id, state, data)``, which returns the
    result to emit. ``prepare(service, dataset_id, kwargs)`` may edit the call
    arguments in place; when it returns a value, that value is emitted and no
    call is made. All three need the exact parent; without one they are skipped.

    When neither ``before`` nor ``after`` is given (every plain transform),
    the view's row count is read before and after the call and added to the
    result as ``row_check``, so a caller always sees whether the write changed
    the row count -- the join path builds its own richer ``join_check`` instead.
    ``reduces_rows`` marks a write meant to remove rows (a filter, a discard of
    duplicates), so verify can flag one that removed none.
    A result staged as a draft never ran the pipeline, so no ``row_check`` is
    added and there is nothing to wait for.
    """
    auto_row_check = before is None and after is None
    # ``dataset_id`` is invocation-local resource context.  It is not a View
    # transform argument, but passing it through lets the service fetch the
    # exact parent endpoint and prevents the SDK's legacy bare-view resolver
    # from probing an unrelated dataset.
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(
        invocation,
        view_id,
        document,
        # Reject conflicting explicit identities rather than selecting one;
        # an omitted parent is filled from the local parent memory below and
        # only then refused for a mutation.
        required=False,
        allow_missing=True,
    )
    with open_service(invocation) as (service, auth):
        if dataset_id is None:
            dataset_id = parents.lookup(_profile_name(invocation), auth.workspace_id, view_id)
        if dataset_id is not None:
            # Verify and the state readback reuse it; neither may walk datasets.
            object.__setattr__(invocation, "known_dataset_id", int(dataset_id))
        require_expected_task_count(service, view_id, dataset_id, document)
        if prepare is not None and dataset_id is not None:
            early = prepare(service, int(dataset_id), kwargs)
            if early is not None:
                return early, _meta(invocation, auth.workspace_id)
        state = before(service, int(dataset_id)) if before and dataset_id is not None else None
        rows_before = (
            _view_row_count(service, int(dataset_id), view_id, invocation.project)
            if auto_row_check and dataset_id is not None
            else None
        )
        try:
            if dataset_id is None:
                _require_discovery_allowed(invocation, view_id)
                data = service.call_view(view_id, method, **kwargs)
            else:
                data = service.call_view(view_id, method, dataset_id=int(dataset_id), **kwargs)
        except CliError as exc:
            # SDK >= 0.7.12 raises on the same job result; enrich it the same way.
            response = exc.details.get("response") if isinstance(exc.details, dict) else None
            reject_pipeline_reference_errors(service, view_id, dataset_id, response)
            raise
        reject_pipeline_reference_errors(service, view_id, dataset_id, data)
        if dataset_id is not None:
            # Later commands that know only the view (a dashboard's check) use it.
            parents.remember(
                _profile_name(invocation), auth.workspace_id, {view_id: int(dataset_id)}
            )
        if after is not None and dataset_id is not None:
            data = after(service, int(dataset_id), state, data)
            _flag_unsettled_pipeline(service, int(dataset_id), view_id, data)
        elif (
            auto_row_check
            and dataset_id is not None
            and isinstance(data, dict)
            and data.get("status") != "staged"
        ):
            # A read taken right away can catch the pipeline still
            # recomputing and read back no row_count at all; wait for it to
            # settle (bounded) before trusting this one. A staged draft never
            # ran the pipeline, so there is nothing to wait for or read.
            rows_after, pipeline_error = wait_for_view_row_count(
                service, int(dataset_id), view_id, invocation.project, write_result=data
            )
            data["row_check"] = {"rows_before": rows_before, "rows_after": rows_after}
            if reduces_rows:
                data["row_check"]["expected_row_decrease"] = True
            if pipeline_error is not None:
                data["pipeline_error"] = pipeline_error
    return data, _meta(invocation, auth.workspace_id)


def with_in_place_note(data: Any, view_id: int) -> Any:
    """Tell the caller this write changed view ``view_id`` itself, and how to avoid that.

    An agent asked for a NEW dataset edited the source's own view; the way to
    leave the source untouched is a working view, then ``view export dataset``.
    """
    if not isinstance(data, dict):
        return data
    return {
        **data,
        "in_place_note": (
            f"This edited existing view {view_id} in place. If the user asked for a NEW "
            "dataset or the source must stay untouched, do not edit it: run 'mammoth view "
            "create DATASET_ID' for a working view, make the steps on that view, then "
            "'mammoth view export dataset' it into the new dataset."
        ),
    }


def _flag_unsettled_pipeline(service: Any, dataset_id: int, view_id: int, data: Any) -> None:
    """Wait for the pipeline after a write with no row check, and record what it finds.

    A ``pipeline_error`` (an execution error, or a wait that ended unfinished)
    keeps the write from reading ``done`` and verified. A staged draft ran nothing.
    """
    if not isinstance(data, dict) or data.get("status") == "staged":
        return
    error = wait_for_pipeline_to_settle(service, dataset_id, view_id)
    if error is not None:
        data["pipeline_error"] = error


CODE_PIPELINE_CHANGED = "pipeline_changed"
_DRAFT_STATUS_SYMBOL = "mammoth.api.pipeline.PipelineAPI.get_draft_status"
_TASK_LIST_SYMBOL = "mammoth.api.pipeline.PipelineAPI.list_tasks"


def require_expected_task_count(
    service: Any, view_id: int, dataset_id: Any, document: dict[str, Any] | None
) -> None:
    """Refuse a pipeline write when the view's task count is not the one read.

    ``expected_task_count`` is the count from the caller's last ``view task
    list``. A different live count means the pipeline changed since that read
    (another agent, a person in the web app), and an append planned against
    the old shape must not land. Without the field nothing is checked.
    """
    if not document or TASK_COUNT_FIELD not in document:
        return
    expected = int(document[TASK_COUNT_FIELD])
    kwargs: dict[str, Any] = {"dataview_id": view_id}
    if dataset_id is not None:
        kwargs["dataset_id"] = int(dataset_id)
    listing = service.call(_TASK_LIST_SYMBOL, **kwargs)
    tasks = listing.get("tasks") if isinstance(listing, dict) else None
    if not isinstance(tasks, list):
        raise CliError(
            code=CODE_PIPELINE_CHANGED,
            message=f"Could not read the task list of view {view_id} to check the precondition.",
            exit_status=EXIT_USAGE,
            details={"view_id": view_id, "expected_task_count": expected, "response": listing},
        )
    actual = len(tasks)
    if actual == expected:
        return
    raise CliError(
        code=CODE_PIPELINE_CHANGED,
        message=(
            f"View {view_id} has {actual} pipeline task(s), not the {expected} expected; "
            "the pipeline changed since it was read, so nothing was written."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            "Re-read the pipeline, decide whether the plan still holds, and retry "
            f"with expected_task_count {actual}."
        ),
        details={
            "view_id": view_id,
            "dataset_id": int(dataset_id) if dataset_id is not None else None,
            "expected_task_count": expected,
            "actual_task_count": actual,
            "task_ids": [t.get("id") for t in tasks if isinstance(t, dict)],
        },
        recovery_commands=[f"mammoth view task list {view_id}"],
    )


def _compact_reference_error(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        return {"reason": str(entry)}
    raw_column = entry.get("column")
    column: dict[str, Any] = raw_column if isinstance(raw_column, dict) else {}
    return {
        "column": column.get("display_name"),
        "internal_name": column.get("internal_name"),
        "type": column.get("type"),
        "reason": entry.get("reason"),
        "error_code": entry.get("error_code"),
    }


def reject_pipeline_reference_errors(
    service: Any, view_id: int, dataset_id: Any, data: Any
) -> None:
    """Fail a pipeline mutation whose task the backend accepted but could not bind.

    A task that references a missing column or the wrong column type is stored
    with ``reference_errors`` and answered with ``has_error: true``; the
    pipeline then sits in ``ref_error`` and every read of the view fails with
    4DTVW019 until the task is removed. The SDK reads the view's draft flag
    after the submit, and the backend flips that flag on a reference error, so
    the SDK returns the job result instead of raising. Turn that into one
    envelope that names the column, the reason and the exact repair command.
    """
    if not (isinstance(data, dict) and data.get("has_error") is True):
        return
    kwargs: dict[str, Any] = {"dataview_id": view_id}
    if dataset_id is not None:
        kwargs["dataset_id"] = int(dataset_id)
    pipeline: dict[str, Any] = {}
    broken: list[dict[str, Any]] = []
    try:
        read = service.call(_PIPELINE_SYMBOL, **kwargs)
        if isinstance(read, dict):
            pipeline = read
        # Every page: a broken task past the first 50 items must still be found.
        items = (
            service.call(_PIPELINE_ITEMS_ALL_SYMBOL, fields=_PIPELINE_ITEMS_FULL, **kwargs)
            if "dataset_id" in kwargs
            else service.call(
                _PIPELINE_ITEMS_SYMBOL, fields=_PIPELINE_ITEMS_FULL, limit=100, **kwargs
            )
        )
        if isinstance(items, dict):
            broken = [
                item
                for item in items.get("items") or []
                if isinstance(item, dict) and item.get("reference_errors")
            ]
    except CliError:
        # The mutation already failed; a failed follow-up read must not hide that.
        pass
    reference_errors = [
        _compact_reference_error(entry)
        for item in broken
        for entry in (item.get("reference_errors") or {}).get("reference_errors") or []
    ]
    task_ids = [item.get("id") for item in broken if item.get("id") is not None]
    first = reference_errors[0] if reference_errors else {}
    reason = str(first.get("reason") or "").lower()
    column = first.get("column")
    what = f"column '{column}' ({first.get('type')})" if column else "a column it references"
    why = _REFERROR_REASON_HINTS.get(reason, f"reason: {reason or 'unknown'}")
    raise CliError(
        code=CODE_PIPELINE_REFERENCE_ERROR,
        message=(
            f"The task was added to view {view_id} but cannot bind to {what}; "
            "the pipeline is in ref_error and the data did not change."
        ),
        exit_status=EXIT_API,
        hint=(
            f"Reads of view {view_id} fail (4DTVW019) until the task is removed: "
            f"run the recovery command, then fix the input ({why})."
        ),
        details={
            "view_id": view_id,
            "dataset_id": kwargs.get("dataset_id"),
            "pipeline_state": pipeline.get("state"),
            "task_ids": task_ids,
            "reference_errors": reference_errors,
            "response": data,
        },
        recovery_commands=[
            f"mammoth view task delete {view_id} {task_id} --yes"
            + (
                f" --input '{{\"dataset_id\": {kwargs['dataset_id']}}}'"
                if "dataset_id" in kwargs
                else ""
            )
            for task_id in task_ids
        ]
        or [f'mammoth view pipeline items {view_id} --input \'{{"fields": "__full"}}\''],
    )


def _parse_created_at(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _newest_task_created_at_or_after(tasks: list[Any], floor: datetime) -> dict[str, Any] | None:
    """The task with the latest ``created_at`` at or after ``floor``, if any."""
    newest: dict[str, Any] | None = None
    newest_created: datetime | None = None
    for task in tasks:
        if not isinstance(task, dict):
            continue
        created = _parse_created_at(task.get("created_at"))
        if created is None or created < floor:
            continue
        if newest_created is None or created > newest_created:
            newest_created, newest = created, task
    return newest


def reject_task_runtime_error(
    service: Any, view_id: int, dataset_id: Any, data: Any, submitted_at: datetime
) -> None:
    """Fail a task add whose step errored at run time without flipping has_error.

    A GEN_AI (or other runtime-dependent) step can fail after the backend has
    already accepted and bound the task -- a workspace AI quota outage, for
    example -- leaving the new column blank while the SDK's ``has_error``
    stays false and ``pipeline_state`` reads ``ready``. The only signal is
    the task's own ``transform_status`` (``ERROR``/``REFERROR``), which
    ``list_tasks`` now reads back at ``__full``. A reference-binding failure
    already raised via :func:`reject_pipeline_reference_errors` before this
    runs, so ``has_error`` here is always false or absent.

    Checks the task *this call* created, not the pipeline's last step by
    sequence: a task can be inserted mid-pipeline (lower sequence than an
    existing later step), and a step already in ERROR before this call must
    not fail every later add just because it sorts last. Neither the add
    response nor its job names the created task's id (the server's
    ``PipelineModificationResp`` has none; ``process_single_task`` only
    echoes the submitted ``task_param`` back), so the newest task by
    ``created_at`` -- accepted only if created at or after ``submitted_at``,
    with a small clock-skew allowance -- stands in for it.
    """
    kwargs: dict[str, Any] = {"dataview_id": view_id}
    if dataset_id is not None:
        kwargs["dataset_id"] = int(dataset_id)
    listing = service.call(_TASK_LIST_SYMBOL, **kwargs)
    tasks = listing.get("tasks") if isinstance(listing, dict) else None
    if not isinstance(tasks, list) or not tasks:
        return
    newest = _newest_task_created_at_or_after(tasks, submitted_at - _TASK_CLOCK_SKEW)
    if newest is None:
        return
    status = newest.get("transform_status")
    if status not in _ERROR_TRANSFORM_STATUSES:
        return
    task_id = newest.get("id")
    dataset_kwarg = kwargs.get("dataset_id")
    recovery = f"mammoth view task get {view_id} {task_id}"
    if dataset_kwarg is not None:
        recovery += f" --input '{{\"dataset_id\": {dataset_kwarg}}}'"
    raise CliError(
        code=CODE_TASK_RUNTIME_ERROR,
        message=(
            f"Task {task_id} was added to view {view_id} but failed at run time "
            f"(transform_status {status}); its output may be blank or wrong even "
            "though the pipeline reports ready."
        ),
        exit_status=EXIT_API,
        hint=(
            "The API does not expose the failure reason (the server keeps only "
            "transform_status). Likely causes: a GEN_AI step hitting the "
            f"workspace AI quota, or a bad step config. Run `{recovery}` to "
            "confirm the status."
        ),
        details={
            "view_id": view_id,
            "dataset_id": dataset_kwarg,
            "task_id": task_id,
            "transform_status": status,
        },
        recovery_commands=[recovery],
    )


def _profile_name(invocation: Invocation) -> str:
    return invocation.profile or profiles.get_selected()


def _without_resource_context(document: dict[str, Any]) -> dict[str, Any]:
    """Remove target-resource context before binding transform SDK arguments."""
    # ``Invocation.load_input`` now applies the shared contract to the whole
    # S3 family, which materializes positional locators in the returned
    # mapping.  These identifiers select the View receiver and are not method
    # kwargs; strip both parent and receiver identities before the transform
    # adapter forwards the document.
    return {
        key: value
        for key, value in document.items()
        if key not in {"dataset_id", "view_id", TASK_COUNT_FIELD}
    }


def _bind_transform_inputs(invocation: Invocation, document: dict[str, Any]) -> dict[str, Any]:
    """Bind every admitted transform field through its reviewed contract.

    Transform handlers still own domain-specific required-field checks and the
    exact View method they call.  They do not, however, maintain a second
    hand-written allow-list of optional fields: the shared contract is the
    destination ledger used by admission, discovery, and this SDK call.  The
    optional ``dataset_id`` is resource identity context for resolving the
    target view and must never be passed to a View transform method.
    """
    bound = bind_command_inputs(invocation.command_id, _without_resource_context(document))
    direction = str(getattr(bound.get("direction"), "value", bound.get("direction"))).upper()
    if direction in {"LEFT", "RIGHT"} and bound.get("num_char") is not None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="LEFT/RIGHT requires char_position, not num_char.",
            exit_status=EXIT_USAGE,
        )
    if direction in {"START", "END"} and bound.get("char_position") is not None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="START/END requires num_char, not char_position.",
            exit_status=EXIT_USAGE,
        )
    return bound


# --- ViewsResource CRUD (generic ``service.call`` seam) --------------------


def view_create(invocation: Invocation) -> HandlerResult:
    """Create a view from a dataset. Dataset id is positional; name/clone_from optional."""
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs = bind_command_inputs(invocation.command_id, document, dataset_id=dataset_id)
    with open_service(invocation) as (service, auth):
        clone_from = kwargs.get("clone_from")
        if clone_from is not None:
            _require_clone_from_same_dataset(service, int(clone_from), dataset_id)
        data = service.call(_symbol(invocation), **kwargs)
    # The SDK returns a rich ``View``; emit its dataview record like ``view get``.
    return _view_payload(data), _meta(invocation, auth.workspace_id)


def _require_clone_from_same_dataset(service: Any, clone_from: int, dataset_id: int) -> None:
    """Refuse ``clone_from`` when it is a view of a different dataset.

    The backend accepts a cross-dataset clone and produces a broken view (no
    columns; every later data read fails), so this is checked here before the
    request is sent rather than surfaced by the server.
    """
    source_dataset_id = int(service.call(_FIND_DATASET_SYMBOL, dataview_id=clone_from))
    if source_dataset_id != dataset_id:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message="clone_from must be a view of the same dataset.",
            exit_status=EXIT_USAGE,
            hint=(
                f"View {clone_from} belongs to dataset {source_dataset_id}, not "
                f"{dataset_id}. Create a plain view (omit clone_from) instead."
            ),
            details={
                "clone_from": clone_from,
                "source_dataset_id": source_dataset_id,
                "dataset_id": dataset_id,
            },
        )


_DASHBOARDS_LIST_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.list"


def _with_dashboards(service: Any, view_id: int, record: Any) -> Any:
    """Add the dashboards built on this view, so a user on the view's page who
    says "this board" is understood (eval T1-D-22); unchanged when none."""
    if not isinstance(record, dict):
        return record
    try:
        boards = service.call(_DASHBOARDS_LIST_SYMBOL)
    except CliError:
        # A decoration must not fail the read it decorates.
        return record
    built_on = [
        {"id": board.get("id"), "title": board.get("title")}
        for board in (boards if isinstance(boards, list) else [])
        if isinstance(board, dict) and view_id in (board.get("sources") or [])
    ]
    return {**record, "dashboards": built_on} if built_on else record


def view_get(invocation: Invocation) -> HandlerResult:
    """Get one view by id, optionally scoped to an exact dataset parent."""
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(invocation, view_id, document)
    if dataset_id is not None:
        # The release operation is dataset-scoped.  Bypass the rich-object
        # resolver when the caller supplied the exact parent so no discovery
        # probe can escape the requested project/dataset.
        kwargs: dict[str, Any] = {
            "dataset_id": dataset_id,
            "dataview_id": view_id,
            # Server-side projection; the brief set (plus the display
            # properties that carry column renames) unless the caller asks.
            "fields": (
                document.get("fields")
                or ",".join(
                    [key for key in BRIEF_VIEW_FIELDS if key != "dataset_id"]
                    + ["display_properties"]
                )
            ),
        }
        with open_service(invocation) as (service, auth):
            data = service.call("mammoth.api.dataviews.DataviewsAPI.get", **kwargs)
            parents.remember(_profile_name(invocation), auth.workspace_id, {view_id: dataset_id})
            data = apply_column_renames(data) if document.get("fields") else brief_view_record(data)
            data = _with_dashboards(service, view_id, data)
        return data, _meta(invocation, auth.workspace_id)
    context: dict[str, Any] = {"view_id": view_id}
    if dataset_id is not None:
        context["dataset_id"] = dataset_id
    # The generated contract predates the optional parent context; preserve
    # its declared fields, then add the validated SDK parent explicitly.
    # ``fields`` projects the exact-parent route only; the discovery route
    # returns the full record, trimmed below unless ``fields`` was asked for.
    binding_document = {
        key: value for key, value in document.items() if key not in ("dataset_id", "fields")
    }
    kwargs = bind_command_inputs(invocation.command_id, binding_document, view_id=view_id)
    if dataset_id is not None:
        kwargs["dataset_id"] = dataset_id
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        payload = _view_payload(data)
        parents.remember_records(_profile_name(invocation), auth.workspace_id, payload)
        if not document.get("fields"):
            # The discovery path returns the standard record; trim it to the same
            # brief shape the exact path asks the server for.
            payload = brief_view_record(payload)
        else:
            payload = apply_column_renames(payload)
        payload = _with_dashboards(service, view_id, payload)
    return payload, _meta(invocation, auth.workspace_id)


def _view_payload(value: Any) -> Any:
    """Return the dataview record for a resolved rich ``View`` object.

    The discovery path returns the SDK's ``View`` (methods, client handle),
    which the output normaliser rightly refuses to serialise. Its ``raw``
    attribute is the same dataview record the exact-parent path returns, so
    both paths emit one shape; the discovered parent is added because the
    caller did not know it and needs it for every mutating follow-up.
    """
    raw = getattr(value, "raw", None)
    if not isinstance(raw, dict):
        return value
    record = dict(raw)
    # The record's own ``ds_id`` is the parent; the resolver's probed dataset is
    # only a fallback, since the backend serves a view under a dataset that does
    # not own it.
    own_parent = record.get("ds_id")
    probed = getattr(value, "dataset_id", None)
    dataset_id = own_parent if isinstance(own_parent, int) else probed
    if isinstance(dataset_id, int) and "dataset_id" not in record:
        record["dataset_id"] = dataset_id
    return record


def view_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one view by id. Prompt or ``--yes`` required.

    ``dataset_id`` is required: the trailing positional, the structured input
    field, or a typed resource reference must name the exact parent. It is
    forwarded to the SDK so deletion uses exactly that parent endpoint and
    never performs a project-wide parent probe before a destructive call.
    """
    view_id = _view_id(invocation)
    enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete view {view_id}")
    document = invocation.load_input() or {}
    dataset_id = _resolve_exact_dataset_id(invocation, view_id, document, required=True)
    context: dict[str, Any] = {"view_id": view_id, "dataset_id": dataset_id}
    kwargs = bind_command_inputs(invocation.command_id, document, **context)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


# --- Draft commands (``service.call_view`` seam) ---------------------------


def view_draft_enter(invocation: Invocation) -> HandlerResult:
    """Enter draft mode on a view's pipeline."""
    view_id = _view_id(invocation)
    return _dispatch_view(invocation, view_id, "enter_draft_mode")


def view_draft_status(invocation: Invocation) -> HandlerResult:
    """Report whether a view's pipeline is currently in draft mode.

    Draft state is read from the server (``PipelineAPI.get_draft_status``) so it
    is correct across processes, rather than from a process-local flag that a
    freshly resolved view would always report as ``False``.
    """
    view_id = _view_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataview_id=view_id)
    return data, _meta(invocation, auth.workspace_id)


def view_draft_submit(invocation: Invocation) -> HandlerResult:
    """Submit a view's draft pipeline changes."""
    view_id = _view_id(invocation)
    project_id = invocation.project

    def before(service: Any, dataset_id: int) -> dict[str, Any]:
        return _draft_before_submit(service, dataset_id, view_id, project_id)

    def after(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        return _draft_submit_row_check(service, dataset_id, view_id, project_id, state, data)

    return _dispatch_view(invocation, view_id, "submit_draft", before=before, after=after)


def _draft_before_submit(
    service: Any, dataset_id: int, view_id: int, project_id: int | None
) -> dict[str, Any]:
    """The view's row count and data timestamp, and whether its draft has changes to run."""
    info = service.call(
        _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
    )
    draft = service.call(_DRAFT_STATUS_SYMBOL, dataview_id=view_id)
    return {
        "row_count": info.get("row_count"),
        "stamp": info.get("data_updated_at"),
        "pending": bool(draft.get("has_pending_changes")),
    }


def _draft_submit_row_check(
    service: Any,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
    before: dict[str, Any],
    data: Any,
) -> Any:
    """``data`` with the row count read once the submitted steps' data is in.

    The submit returns with the pipeline ``idle`` while its steps still run, so a
    count read at once is the old one (FB-22). A draft with nothing to run is
    read at once; data that never refreshes is reported as unfinished.
    """
    if not isinstance(data, dict):
        return data
    if before["pending"]:
        info = wait_for_refreshed_view(service, dataset_id, view_id, project_id, before["stamp"])
    else:
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
    rows_after = info.get("row_count") if info is not None else None
    out = {**data, "row_check": {"rows_before": before["row_count"], "rows_after": rows_after}}
    if info is None:
        out["pipeline_error"] = {
            "execution_state": UNFINISHED_STATE,
            "wait_error": "the view's data was not refreshed after the submit; read it again",
        }
    return out


def view_draft_discard(invocation: Invocation) -> HandlerResult:
    """Discard a view's draft pipeline changes. Prompt or ``--yes`` required."""
    view_id = _view_id(invocation)
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"discard the draft for view {view_id}"
    )
    return _dispatch_view(invocation, view_id, "discard_draft")


def view_draft_auto_run(invocation: Invocation) -> HandlerResult:
    """Set whether a view's draft pipeline auto-runs. ``enabled`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    enabled = _require_field(document, "enabled")
    return _dispatch_view(invocation, view_id, "set_auto_run", enabled=enabled)


# --- Transform commands (``service.call_view`` seam) -----------------------


def view_transform_add_column(invocation: Invocation) -> HandlerResult:
    """Add a new column. ``name`` is required; ``column_type`` is optional."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "name")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "add_column", **kwargs)


def view_transform_add_sql(invocation: Invocation) -> HandlerResult:
    """Add a column via a raw SQL expression. ``query`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "query")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(
        invocation, view_id, "add_sql", prepare=_sql_binding_check(invocation, view_id), **kwargs
    )


def _sql_binding_check(
    invocation: Invocation, view_id: int
) -> Callable[[Any, int, dict[str, Any]], Any]:
    """A ``prepare`` hook: a dry run fails with ``would_fail`` when the SQL names a column
    the step cannot bind (see :mod:`mammoth_cli.services.sql_check`). A real run is unchanged."""

    def check(service: Any, dataset_id: int, kwargs: dict[str, Any]) -> Any:
        if invocation.dry_run:
            view = service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=view_id,
                project_id=resolved_project(invocation),
            )
            if isinstance(view, dict):
                check_sql_binds(str(kwargs.get("query", "")), view)
        return None

    return check


def view_transform_ai(invocation: Invocation) -> HandlerResult:
    """Generate a column with an AI prompt. ``prompt``/``context_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "prompt")
    _require_field(document, "context_columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "gen_ai", **kwargs)


def view_transform_bulk_replace(invocation: Invocation) -> HandlerResult:
    """Bulk-replace values. ``columns``/``mapping`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    _require_field(document, "mapping")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_bulk_replace)
    return _dispatch_view(invocation, view_id, "bulk_replace", prepare=prepare, **kwargs)


def view_transform_combine_columns(invocation: Invocation) -> HandlerResult:
    """Combine columns into one. ``sources`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "sources")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "combine_columns", **kwargs)


def view_transform_convert_type(invocation: Invocation) -> HandlerResult:
    """Convert column types. ``conversions`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "conversions")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    project_id = invocation.project

    def drop_same_type(service: Any, dataset_id: int, call: dict[str, Any]) -> Any:
        # Converting a column to the type it already has puts the pipeline in
        # ref_error ("type mismatch") and every read of the view fails until
        # the task is removed (release, 2026-09-25). Uploads type numbers and
        # ISO dates on their own, so this is easy to hit: skip those entries.
        conversions = call.get("conversions")
        if not isinstance(conversions, list):
            return None
        current = {
            column.get("display_name"): str(column.get("type") or "").upper()
            for column in _dataview_metadata(service, dataset_id, view_id, project_id)
            if isinstance(column, dict)
        }
        kept, skipped = [], []
        for entry in conversions:
            name = entry.get("column") if isinstance(entry, dict) else None
            target = str(entry.get("to") or "").upper() if isinstance(entry, dict) else ""
            if name is not None and target and current.get(name) == target:
                skipped.append({"column": name, "type": target})
            else:
                kept.append(entry)
        if not skipped:
            return None
        if not kept:
            return {
                "status": "no_change",
                "skipped": skipped,
                "note": "Every column already has the requested type; no task was added.",
            }
        call["conversions"] = kept
        skipped_record.extend(skipped)
        return None

    skipped_record: list[dict[str, Any]] = []

    def note_skipped(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        if skipped_record and isinstance(data, dict):
            data = {**data, "skipped": skipped_record}
        return data

    return _dispatch_view(
        invocation,
        view_id,
        "convert_type",
        prepare=drop_same_type,
        after=note_skipped,
        **kwargs,
    )


def view_transform_copy_columns(invocation: Invocation) -> HandlerResult:
    """Copy columns. ``copies`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "copies")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "copy_columns", **kwargs)


def view_transform_crosstab(invocation: Invocation) -> HandlerResult:
    """Build a crosstab into a new dataset. ``rows``/``pivot_column``/``select``/
    ``dataset_name`` are required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "rows")
    _require_field(document, "pivot_column")
    _require_field(document, "select")
    _require_field(document, "dataset_name")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "crosstab", **kwargs)


def view_transform_date_diff(invocation: Invocation) -> HandlerResult:
    """Compute the difference between two dates. ``component``/``start``/``end`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "component")
    _require_field(document, "start")
    _require_field(document, "end")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "date_diff", **kwargs)


def view_transform_delete_columns(invocation: Invocation) -> HandlerResult:
    """Delete columns. ``columns`` is required. Prompt or ``--yes`` required."""
    view_id = _view_id(invocation)
    enforce_confirmation(
        invocation, policy=POLICY_PROMPT_OR_YES, action=f"delete columns on view {view_id}"
    )
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "delete_columns", **kwargs)


def view_transform_discard_duplicates(invocation: Invocation) -> HandlerResult:
    """Discard duplicate rows. ``ignore_columns`` is optional.

    ``--dry-run`` counts the duplicates first: it reports ``predicted_impact``,
    or fails with ``no_op`` when there are none (nothing to discard).
    """
    view_id = _view_id(invocation)
    document = invocation.load_input() or {}
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_duplicates)
    return _dispatch_view(
        invocation, view_id, "discard_duplicates", prepare=prepare, reduces_rows=True, **kwargs
    )


def _impact_check(
    invocation: Invocation, view_id: int, measure: Measure
) -> Callable[[Any, int, dict[str, Any]], Any]:
    """A ``prepare`` hook: measure what the step would change, by a read.

    A count of zero is a no-op: ``--dry-run`` fails with ``no_op`` and a real run
    adds no task (``status: no_change``, like a same-type convert). Otherwise a
    dry run reports the count as ``predicted_impact``. A keep filter no row matches
    fails a dry run with ``empties_view``. A count that cannot run
    is reported as unchecked in a dry run, never as zero, and never blocks a write.
    """

    def check(service: Any, dataset_id: int, kwargs: dict[str, Any]) -> Any:
        project_id = resolved_project(invocation)
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        read = ImpactRead(
            service,
            dataset_id,
            view_id,
            project_id,
            apply_column_renames(info),
            invocation.load_input() or {},
            invocation.dry_run,
        )
        try:
            measured = measure(read, kwargs)
        except CliError as exc:
            if invocation.dry_run:
                object.__setattr__(
                    invocation, "predicted_impact", {"checked": False, "reason": exc.message}
                )
            return None
        if measured.empties_message and invocation.dry_run:
            raise empties_view_error(measured.empties_message, view_id=view_id)
        if measured.changes == 0:
            if invocation.dry_run:
                raise no_op_error(measured.no_op_message, view_id=view_id)
            return {"status": "no_change", "note": f"{measured.no_op_message} No task was added."}
        if invocation.dry_run:
            object.__setattr__(invocation, "predicted_impact", measured.report)
        return None

    return check


def view_transform_extract_date(invocation: Invocation) -> HandlerResult:
    """Extract a date component into a column. ``column``/``component`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "component")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "extract_date", **kwargs)


def view_transform_fill_missing(invocation: Invocation) -> HandlerResult:
    """Fill missing values. ``column``/``direction`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "direction")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_fill_missing)
    return _dispatch_view(invocation, view_id, "fill_missing", prepare=prepare, **kwargs)


def view_transform_filter(invocation: Invocation) -> HandlerResult:
    """Filter rows. ``condition`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, CONDITION_KWARG)
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_filter)
    return _dispatch_view(
        invocation, view_id, "filter_rows", prepare=prepare, reduces_rows=True, **kwargs
    )


def view_transform_generate_sql(invocation: Invocation) -> HandlerResult:
    """Generate a SQL query from a natural-language intent. ``intent`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "intent")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)

    def describe(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        # The route writes and validates a query but adds no task (release,
        # 2026-09-25); a bare string read as "done" by an agent that expected
        # the view to change. Say so, and give the command that applies it.
        if not isinstance(data, str):
            return data
        spec = json.dumps({"dataset_id": dataset_id, "query": data})
        return {
            "sql": data,
            "applied": False,
            "note": "The view is unchanged. Run 'apply' to add the query as a SQL task.",
            "apply": f"mammoth view transform add-sql {view_id} --input {shlex.quote(spec)}",
        }

    return _dispatch_view(invocation, view_id, "generate_sql", after=describe, **kwargs)


def view_transform_increment_date(invocation: Invocation) -> HandlerResult:
    """Increment a date column. ``column``/``delta`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "delta")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "increment_date", **kwargs)


def view_transform_join(invocation: Invocation) -> HandlerResult:
    """Join another view. ``foreign_view``/``join_type``/``on``/``select`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "foreign_view")
    _require_field(document, "join_type")
    _require_field(document, "on")
    _require_field(document, "select")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    project_id = invocation.project
    preview: dict[str, Any] = {}

    def before(service: Any, dataset_id: int) -> Any:
        if invocation.dry_run:
            preview.update(_join_preview(service, dataset_id, view_id, document, project_id))
        return join_snapshot(service, dataset_id, view_id, project_id)

    def after(service: Any, dataset_id: int, state: Any, data: Any) -> Any:
        # The join runs as a follow-on job; a pipeline read taken before it finishes
        # still shows the old view (no columns added, no rows to check).
        wait_for_followon_job(service, data)
        return with_join_check(
            data,
            state,
            join_after_snapshot(service, dataset_id, view_id, project_id, state),
            document,
            _join_preview(service, dataset_id, view_id, document, project_id),
        )

    try:
        return _dispatch_view(invocation, view_id, "join", before=before, after=after, **kwargs)
    except DryRunStop as stop:
        if preview:
            stop.record["join_preview"] = preview
        raise


def _join_preview(
    service: Any, dataset_id: int, view_id: int, document: dict[str, Any], project_id: int | None
) -> dict[str, Any]:
    """The dry run's key overlap; the other view's dataset is ``foreign_dataset_id``."""
    foreign, foreign_dataset = document.get("foreign_view"), document.get("foreign_dataset_id")
    if isinstance(foreign, dict):
        foreign_dataset = foreign_dataset or foreign.get("dataset_id")
        foreign = foreign.get("view_id", foreign.get("dataview_id", foreign.get("id")))
    if not isinstance(foreign, int) or not isinstance(foreign_dataset, int):
        return {"checked": False, "error": "foreign_view/foreign_dataset_id unknown"}
    return join_dry_run_preview(
        service, (dataset_id, view_id), (foreign_dataset, foreign), document, project_id
    )


def view_transform_json_extract(invocation: Invocation) -> HandlerResult:
    """Extract fields from a JSON column. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "json_extract", **kwargs)


def view_transform_limit_rows(invocation: Invocation) -> HandlerResult:
    """Limit the row count. ``n`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "n")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "limit_rows", **kwargs)


def view_transform_rename_columns(invocation: Invocation) -> HandlerResult:
    """Rename columns (a view display setting, not a task). ``renames`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "renames")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "rename_columns", **kwargs)


def view_transform_sort(invocation: Invocation) -> HandlerResult:
    """Set the view's row order (a display setting, not a task). ``order_by`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "order_by")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "sort_rows", **kwargs)


def view_transform_lookup(invocation: Invocation) -> HandlerResult:
    """Look up values from another view. ``source``/``lookup_view_id``/``key``/
    ``value`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "source")
    _require_field(document, "lookup_view_id")
    _require_field(document, "key")
    _require_field(document, "value")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "lookup", **kwargs)


def view_transform_math(invocation: Invocation) -> HandlerResult:
    """Evaluate a math expression into a column. ``expression`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "expression")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    blanks: dict[str, int] = {}

    def count_blank_inputs(service: Any, dataset_id: int, _kwargs: dict[str, Any]) -> None:
        blanks.update(
            _blank_math_inputs(
                service, dataset_id, view_id, resolved_project(invocation), document["expression"]
            )
        )

    data, meta = _dispatch_view(invocation, view_id, "math", prepare=count_blank_inputs, **kwargs)
    return _with_blank_input_note(data, blanks), meta


def _blank_math_inputs(
    service: Any, dataset_id: int, view_id: int, project_id: int | None, expression: Any
) -> dict[str, int]:
    """Blank cells of each column a math expression names, for the columns that have any.

    Mammoth computes a blank input as 0, so ``qty * unit_price`` gives 0 for an
    unpriced row and a later total counts it with no warning (FB-01).
    """
    info = service.call(
        _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
    )
    read = ImpactRead(service, dataset_id, view_id, project_id, apply_column_renames(info))
    text = str(expression)
    named = [
        name
        for name in read.display_to_internal()
        if re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text)
    ]
    try:
        counts = {
            name: read.count(compile_condition({"column": name, "operator": "IS_EMPTY"}))
            for name in named
        }
    except CliError:
        return {}  # A count that cannot run never blocks the write; it only drops the note.
    return {name: count for name, count in counts.items() if count}


def _with_blank_input_note(data: Any, blanks: dict[str, int]) -> Any:
    """``data`` with a ``blank_inputs`` note when a math input column has blanks."""
    if not blanks or not isinstance(data, dict):
        return data
    listed = ", ".join(f"{name} is blank in {count} row(s)" for name, count in blanks.items())
    note = (
        f"A blank input counts as 0 in this math step: {listed}, so the result there is "
        "computed as if it were 0. Fill or filter those rows first if a blank must not count as 0."
    )
    return {**data, "blank_inputs": {"columns": blanks, "note": note}}


def view_transform_pivot(invocation: Invocation) -> HandlerResult:
    """Pivot with aggregations. ``group_by``/``aggregations`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "group_by")
    _require_field(document, "aggregations")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "pivot", **kwargs)


def view_transform_replace(invocation: Invocation) -> HandlerResult:
    """Find and replace values. ``columns``/``find``/``replace`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    _require_field(document, "find")
    _require_field(document, "replace")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    prepare = _impact_check(invocation, view_id, measure_replace)
    return _dispatch_view(invocation, view_id, "replace_values", prepare=prepare, **kwargs)


def view_transform_set_values(invocation: Invocation) -> HandlerResult:
    """Set values conditionally. ``values`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "values")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "set_values", **kwargs)


def view_transform_small_large(invocation: Invocation) -> HandlerResult:
    """Compute a small/large-N function. ``function``/``columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "function")
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "small_large", **kwargs)


def view_transform_split(invocation: Invocation) -> HandlerResult:
    """Split a column. ``column``/``delimiter``/``new_columns`` required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    _require_field(document, "delimiter")
    _require_field(document, "new_columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "split_column", **kwargs)


def view_transform_substring(invocation: Invocation) -> HandlerResult:
    """Extract a substring. ``column`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "column")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "substring", **kwargs)


def view_transform_text(invocation: Invocation) -> HandlerResult:
    """Apply text transforms. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "text_transform", **kwargs)


def view_transform_unnest(invocation: Invocation) -> HandlerResult:
    """Unnest columns into label/value rows. ``columns`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "columns")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "unnest", **kwargs)


def view_transform_window(invocation: Invocation) -> HandlerResult:
    """Compute a window function. ``function`` is required."""
    view_id = _view_id(invocation)
    document = invocation.load_input()
    _require_field(document, "function")
    assert document is not None
    kwargs = _bind_transform_inputs(invocation, document)
    return _dispatch_view(invocation, view_id, "window", **kwargs)
