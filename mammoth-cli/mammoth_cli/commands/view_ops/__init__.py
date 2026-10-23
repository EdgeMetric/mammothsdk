"""The shared write path for the ``view`` draft, transform and CRUD commands.

The handlers live in the submodules: :mod:`.crud` (``view create``/``get``/``delete``),
:mod:`.draft` (``view draft *``), :mod:`.transforms` (``view transform *``) and
:mod:`.batch` (``view transform batch``). Draft and transform commands dispatch through
:meth:`~mammoth_cli.services.protocol.MammothService.call_view`, which resolves the
dataview into a rich ``View`` and calls the named public method. A ``condition`` field,
when the underlying method accepts one, is forwarded unchanged as a plain spec; the
service layer compiles it.

Command modules never import the SDK's condition builder or any enum type;
enum-typed fields are forwarded as the plain string given on ``--input``.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from mammoth_cli.commands.view._common import _DATAVIEW_GET_SYMBOL, _require_discovery_allowed
from mammoth_cli.commands.view.settle import (
    UNFINISHED_STATE,
    sdk_saw_pipeline_ready,
    wait_for_pipeline_to_settle,
    wait_for_view_row_count,
)
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_INVALID_ARGUMENTS,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_OUTCOME_UNKNOWN,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.runtime.verify import export_stamps, export_stamps_read
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.input_fields import TASK_COUNT_FIELD
from mammoth_cli.services.poll import poll_delays
from mammoth_cli.services.read_memo import prefetch
from mammoth_cli.services.write_impact import STANDING_NOTE

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


def _require_one_destination(document: dict[str, Any], command_id: str) -> None:
    """Refuse a transform that names both ``new_column`` and ``existing_column``, or neither.

    The SDK silently keeps only ``new_column`` when both are given, and a step
    with neither is saved and then fails in the worker ("No destination for
    operation") after the pipeline has already been changed.
    """
    given = [name for name in ("new_column", "existing_column") if document.get(name) is not None]
    if len(given) == 1:
        return
    command = command_id.replace(".", " ")
    raise CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=(
            f"'{command}' needs exactly one of new_column or existing_column, "
            + ("not both: existing_column would be ignored." if given else "but got neither.")
        ),
        exit_status=EXIT_USAGE,
        hint=(
            "Set new_column to write a new column, or existing_column to overwrite "
            "one that is already in the view."
        ),
        details={"given": given},
    )


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


def _read_before_write(
    service: Any, view_id: int, dataset_id: int, project_id: int | None
) -> dict[int, str] | None:
    """The view's export stamps, fetched together with its record.

    The record is kept (see :mod:`mammoth_cli.services.read_memo`) for the checks that read
    it ahead of the write, so they do not each fetch it again; the write itself drops it.
    Returns ``None`` when the exports cannot be read, like ``read_export_stamps``.
    """
    exports_read = export_stamps_read(view_id, dataset_id)
    view_read = (
        _DATAVIEW_GET_SYMBOL,
        {"dataset_id": dataset_id, "dataview_id": view_id, "project_id": project_id},
    )
    exports, _view = prefetch(service, [exports_read, view_read])
    return None if isinstance(exports, CliError) else export_stamps(exports)


def _dispatch_view(
    invocation: Invocation,
    view_id: int,
    method: str,
    *,
    before: Callable[[Any, int], Any] | None = None,
    after: Callable[[Any, int, Any, Any], Any] | None = None,
    prepare: Callable[[Any, int, dict[str, Any]], Any] | None = None,
    reduces_rows: bool = False,
    waits_for_run: bool = False,
    **kwargs: Any,
) -> HandlerResult:
    """Open the service, dispatch a View method call, and build the envelope.

    ``waits_for_run`` marks a write that adds a task to this view. Its result
    then waits for that task's own run to finish (see
    :func:`wait_for_added_task_run`) before ``after`` and the read-back, and
    carries that run as ``run``; a pipeline definition reading ``ready`` is not
    proof the task ran. A step staged in draft mode is never submitted here and has
    no run to wait on: the draft stays the user's to submit.

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
        if dataset_id is not None:
            # The checks below read the view and the write's exports; fetch both at once.
            object.__setattr__(
                invocation,
                "exports_before",
                _read_before_write(service, view_id, int(dataset_id), invocation.project),
            )
        if prepare is not None and dataset_id is not None:
            early = prepare(service, int(dataset_id), kwargs)
            if early is not None:
                return early, _meta(invocation, auth.workspace_id)
        state = before(service, int(dataset_id)) if before and dataset_id is not None else None
        task_ids_before = (
            _task_ids(service, int(dataset_id), view_id)
            if waits_for_run and dataset_id is not None
            else None
        )
        rows_before = (
            _view_row_count(service, int(dataset_id), view_id, invocation.project)
            if auto_row_check and dataset_id is not None
            else None
        )
        guard_ids = (
            task_ids_before
            if task_ids_before is not None
            else (
                _task_ids(service, int(dataset_id), view_id)
                if method == "add_sql" and dataset_id is not None
                else None
            )
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
            applied = (
                _applied_despite_unreadable(service, view_id, dataset_id, guard_ids)
                if exc.code == CODE_OUTCOME_UNKNOWN and method == "add_sql"
                else None
            )
            if applied is None:
                raise
            data = applied
        reject_pipeline_reference_errors(service, view_id, dataset_id, data)
        if dataset_id is not None:
            data = _mark_staged_in_draft(service, dataset_id, view_id, data)
            # Later commands that know only the view (a dashboard's check) use it.
            parents.remember(
                _profile_name(invocation), auth.workspace_id, {view_id: int(dataset_id)}
            )
        settled = _settled_write(service, data) if dataset_id is not None else None
        if settled is not None:
            _forget_reads(service)  # the state read-back must see the view as the write left it
        if after is not None and dataset_id is not None:
            if settled is not None:
                run: dict[str, Any] | None = {
                    "task_id": settled["task_id"],
                    "transform_status": settled["task_run_status"],
                }
                run_error = None
            else:
                run, run_error = (
                    wait_for_added_task_run(service, int(dataset_id), view_id, task_ids_before)
                    if task_ids_before is not None and not _is_staged(data)
                    else (None, None)
                )
            reject_unrun_task_with_reference_errors(service, view_id, dataset_id, run_error)
            sdk_ready = sdk_saw_pipeline_ready(data)
            data = after(service, int(dataset_id), state, data)
            if settled is None:
                _flag_unsettled_pipeline(service, int(dataset_id), view_id, data, sdk_ready)
            if isinstance(data, dict) and run is not None:
                data["run"] = run
                if run_error is not None:
                    data.setdefault("pipeline_error", run_error)
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
            rows_after, pipeline_error = (
                (settled["row_count"], None)
                if settled is not None
                else wait_for_view_row_count(
                    service, int(dataset_id), view_id, invocation.project, write_result=data
                )
            )
            data["row_check"] = {"rows_before": rows_before, "rows_after": rows_after}
            if reduces_rows and not invocation.standing_noop:
                data["row_check"]["expected_row_decrease"] = True
            if pipeline_error is not None:
                data["pipeline_error"] = pipeline_error
    if invocation.standing_noop and isinstance(data, dict):
        data["standing_rule"] = {"removed_now": 0, "note": STANDING_NOTE}
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


#: A task's own ``transform_status`` once its run is over; ``DONE`` is the only success.
_RUN_DONE_STATUS = "DONE"
_RUN_OVER_STATUSES = frozenset({_RUN_DONE_STATUS, "ERROR", "REFERROR", "EXCEPTION"})
_RUN_FAILED_STATUSES = _RUN_OVER_STATUSES - {_RUN_DONE_STATUS}
#: Bounded wait for the run of a task just added: it starts after the add returns.
_RUN_ATTEMPTS = 40
_RUN_RETRY_S = 0.5
#: Most seconds the wait for a task's run sleeps in all.
_RUN_WAIT_S = _RUN_ATTEMPTS * _RUN_RETRY_S


def _tasks(service: Any, dataset_id: int, view_id: int) -> list[dict[str, Any]]:
    listing = service.call(_TASK_LIST_SYMBOL, dataview_id=view_id, dataset_id=dataset_id)
    tasks = listing.get("tasks") if isinstance(listing, dict) else None
    return [task for task in tasks or [] if isinstance(task, dict)]


def _applied_despite_unreadable(
    service: Any, view_id: int, dataset_id: Any, task_ids_before: set[Any] | None
) -> dict[str, Any] | None:
    """The result for a write whose own read-back failed after the task was stored.

    ``add-sql`` can finish its job and then fail reading the view back (the new
    query's response is not valid yet). The task list says whether the step was
    stored: a task that was not there before means it was, so the write is
    reported as applied with a warning instead of "outcome unknown".
    """
    if task_ids_before is None or dataset_id is None:
        return None
    try:
        added = sorted(_task_ids(service, int(dataset_id), view_id) - task_ids_before, key=str)
    except Exception:  # noqa: BLE001 -- an unreadable task list leaves the outcome unknown
        return None
    if not added:
        return None
    return {
        "status": "done",
        "task_ids": added,
        "warnings": [
            "the step was stored (confirmed in the task list) but reading the view back "
            "failed right after; run `mammoth view pipeline wait VIEW_ID`, then read the view "
            "before building on it"
        ],
    }


def _task_ids(service: Any, dataset_id: int, view_id: int) -> set[Any]:
    return {task.get("id") for task in _tasks(service, dataset_id, view_id)}


def wait_for_added_task_run(
    service: Any, dataset_id: int, view_id: int, task_ids_before: set[Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The run of the task this write added, once its own ``transform_status`` says it is over.

    The add's response names no task (the SDK has already waited out the job that
    modified the pipeline), and the pipeline's definition ``state`` reads ``ready``
    before the task's run has started. The task is the one id not in
    ``task_ids_before``; its run is over when its ``transform_status`` is
    ``DONE`` or an error. Returns ``(run, error)``: ``run`` is the handle the
    read-back came from (``task_id``, ``transform_status``), or
    ``None`` when the write added no task; ``error`` is ``None`` for ``DONE``,
    else the pipeline_error that keeps the write from reading verified.
    """
    run: dict[str, Any] = {}
    for delay in poll_delays(_RUN_WAIT_S, _RUN_RETRY_S):
        added = [
            task
            for task in _tasks(service, dataset_id, view_id)
            if task.get("id") not in task_ids_before
        ]
        if not added:
            return None, None
        status = added[-1].get("transform_status")
        run.update(task_id=added[-1].get("id"), transform_status=status)
        if status in _RUN_OVER_STATUSES:
            if status == _RUN_DONE_STATUS:
                return run, None
            return run, {
                "execution_state": "runtime_error",
                "task_id": run["task_id"],
                "transform_status": status,
            }
        time.sleep(delay)
    return run, {
        "execution_state": UNFINISHED_STATE,
        "task_id": run.get("task_id"),
        "wait_error": (
            f"task {run.get('task_id')} had not finished running "
            f"(transform_status {run.get('transform_status')})"
        ),
    }


def clean_write_result(job_response: Any) -> dict[str, Any] | None:
    """The ``write_result`` of a run job when it says the write ran and settled cleanly.

    A newer server adds it to the run job's response. ``None`` (read the task, the
    pipeline and the row count as before) when it is absent, or says anything but a
    finished task on a ``ready`` pipeline with a row count: those reads name the failure.
    """
    result = job_response.get("write_result") if isinstance(job_response, dict) else None
    if (
        isinstance(result, dict)
        and result.get("task_id") is not None
        and result.get("task_run_status") == _RUN_DONE_STATUS
        and result.get("pipeline_state") == "ready"
        and result.get("row_count") is not None
    ):
        return result
    return None


def _settled_write(service: Any, data: Any) -> dict[str, Any] | None:
    """The clean ``write_result`` of the run job a write names (``future_id``), read once."""
    future_id = data.get("future_id") if isinstance(data, dict) else None
    if not isinstance(future_id, int) or _is_staged(data):
        return None
    try:
        job = service.wait_if_job({"future_id": future_id})
    except CliError:
        return None  # the reads that follow report the failed or unfinished job
    return clean_write_result(job)


def _forget_reads(service: Any) -> None:
    """Drop the reads made ahead of a write (see :mod:`mammoth_cli.services.read_memo`)."""
    memo = getattr(service, "memo", None)
    if memo is not None:
        memo.clear()


def _is_staged(data: Any) -> bool:
    """Whether a write only staged its step in a draft, so no run is to be waited on."""
    return isinstance(data, dict) and data.get("status") == "staged"


def _mark_staged_in_draft(service: Any, dataset_id: int, view_id: int, data: Any) -> Any:
    """Answer ``status: staged`` for a write the SDK did not already stage.

    The SDK stages the tasks it adds in draft mode, but a write that is not a
    task (a sort) comes back without a status. In a draft pipeline nothing
    runs, so every wait that follows the write would only burn its timeout.
    """
    if not isinstance(data, dict) or data.get("status") is not None:
        return data
    draft = service.call(_DRAFT_STATUS_SYMBOL, dataview_id=view_id, dataset_id=dataset_id)
    if not (isinstance(draft, dict) and draft.get("is_draft") is True):
        return data
    return {
        **data,
        "status": "staged",
        "message": (
            f"The view is in draft mode; this step is staged, not run. Run "
            f"'mammoth view draft submit {view_id}' to run staged steps."
        ),
    }


def _flag_unsettled_pipeline(
    service: Any, dataset_id: int, view_id: int, data: Any, sdk_ready: bool = False
) -> None:
    """Wait for the pipeline after a write with no row check, and record what it finds.

    A ``pipeline_error`` (an execution error, or a wait that ended unfinished)
    keeps the write from reading ``done`` and verified. A staged draft ran nothing.
    ``sdk_ready`` skips the poll when the write's own SDK call already saw it ready.
    """
    if not isinstance(data, dict) or data.get("status") == "staged":
        return
    error = wait_for_pipeline_to_settle(service, dataset_id, view_id, already_ready=sdk_ready)
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
    kwargs = _pipeline_kwargs(view_id, dataset_id)
    pipeline, broken = _read_broken_items(service, kwargs)
    raise _reference_error(view_id, kwargs, pipeline, broken, data)


def _pipeline_kwargs(view_id: int, dataset_id: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"dataview_id": view_id}
    if dataset_id is not None:
        kwargs["dataset_id"] = int(dataset_id)
    return kwargs


def _read_broken_items(
    service: Any, kwargs: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The pipeline and its items that carry reference errors; a failed read gives what was read."""
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
    return pipeline, broken


def reject_unrun_task_with_reference_errors(
    service: Any, view_id: int, dataset_id: Any, run_error: dict[str, Any] | None
) -> None:
    """Fail a write whose added task never ran because a step of the view no longer binds.

    The backend validates a new task after it answers, so a convert-type that
    breaks a step reading the column as a number answers without ``has_error``
    and the task then stays ``added`` for good. When the wait for the task's run
    ended unfinished and the pipeline holds reference errors, that is the cause:
    raise the same envelope a task refused at once gets, with the recovery command.
    """
    if run_error is None or run_error.get("execution_state") != UNFINISHED_STATE:
        return
    kwargs = _pipeline_kwargs(view_id, dataset_id)
    pipeline, broken = _read_broken_items(service, kwargs)
    if broken:
        raise _reference_error(view_id, kwargs, pipeline, broken, run_error)


def _reference_error(
    view_id: int,
    kwargs: dict[str, Any],
    pipeline: dict[str, Any],
    broken: list[dict[str, Any]],
    response: dict[str, Any],
) -> CliError:
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
    return CliError(
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
            "response": response,
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


def _bind_transform_inputs(
    invocation: Invocation, document: dict[str, Any], command_id: str | None = None
) -> dict[str, Any]:
    """Bind every admitted transform field through its reviewed contract.

    Transform handlers still own domain-specific required-field checks and the
    exact View method they call.  They do not, however, maintain a second
    hand-written allow-list of optional fields: the shared contract is the
    destination ledger used by admission, discovery, and this SDK call.  The
    optional ``dataset_id`` is resource identity context for resolving the
    target view and must never be passed to a View transform method.
    """
    bound = bind_command_inputs(
        command_id or invocation.command_id, _without_resource_context(document)
    )
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
