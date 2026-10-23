"""``view transform batch``: several steps as one draft, submitted together."""

from __future__ import annotations

import time
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any

from mammoth_cli.commands.view._common import (
    _DATAVIEW_GET_SYMBOL,
)
from mammoth_cli.commands.view.settle import (
    UNFINISHED_STATE,
    wait_for_pipeline_to_settle,
    wait_for_refreshed_view,
    wait_for_view_row_count,
)
from mammoth_cli.commands.view_ops import (
    _RUN_DONE_STATUS,
    _RUN_FAILED_STATUSES,
    _RUN_RETRY_S,
    _RUN_WAIT_S,
    _bind_transform_inputs,
    _is_staged,
    _meta,
    _profile_name,
    _read_before_write,
    _require_field,
    _resolve_exact_dataset_id,
    _task_ids,
    _tasks,
    _view_id,
    _without_resource_context,
    require_expected_task_count,
)
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.runtime.strict import apply_input_aliases, validate_input_fields
from mammoth_cli.services.command_contract import resolve_command_contract
from mammoth_cli.services.field_enums import BATCH_LAST_OPS, BATCH_OPS, allowed_values_text
from mammoth_cli.services.poll import poll_delays
from mammoth_cli.services.suggest import nearest_one

HandlerResult = tuple[Any, dict[str, Any]]


#: The ops a batch takes; one list for the check, the error hint and ``--help``.
_BATCH_OPS = BATCH_OPS
#: A sort is the view's row order (a display setting), not a pipeline task.
_BATCH_SORT_OP = "sort"
_ADD_TASKS_METHOD = "add_tasks"
_BATCH_LIMIT_OP = "limit-rows"
_SORT_METHOD = "sort_rows"
_TASK_DELETE_SYMBOL = "mammoth.api.pipeline.PipelineAPI.delete_task"
CODE_BATCH_STEP_FAILED = "batch_step_failed"
CODE_UNKNOWN_COLUMN = "unknown_column"
_BATCH_COLUMN_HINT = (
    "A batch is built against the view's columns plus the ones the earlier steps of the batch "
    "add (split, copy-columns, and any new_column of substring, extract-date, increment-date). "
    "A column in neither is unknown: check its name, or run the step that creates it first."
)


@dataclass
class _BatchPlan:
    """What a batch will do, built before anything is sent."""

    specs: list[dict[str, Any]] = dataclass_field(default_factory=list)
    #: ``(step index, op)`` of each spec, in order.
    task_steps: list[tuple[int, str]] = dataclass_field(default_factory=list)
    #: The bound ``sort`` inputs, applied after the tasks have run.
    sorts: list[dict[str, Any]] = dataclass_field(default_factory=list)
    #: The columns the tasks add; the sort is built after they ran but on metadata that may not
    #: list them yet.
    created: list[dict[str, str]] = dataclass_field(default_factory=list)


def _batch_steps(document: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The ``steps`` of the input document, each checked to be ``{"op", "input"}``."""
    steps = _require_field(document, "steps")
    if not isinstance(steps, list) or not steps:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message='\'steps\' must be a non-empty list of {"op": ..., "input": {...}}.',
            exit_status=EXIT_USAGE,
        )
    for index, step in enumerate(steps):
        if not (
            isinstance(step, dict)
            and step.get("op") in _BATCH_OPS
            and isinstance(step.get("input"), dict)
        ):
            op = step.get("op") if isinstance(step, dict) else None
            near = nearest_one(op, _BATCH_OPS) if isinstance(op, str) else None
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=(
                    f"steps[{index}] must be {{\"op\": one of {', '.join(_BATCH_OPS)}, "
                    '"input": {...the same input as that `view transform` command}}.'
                    + (f" Did you mean '{near}'?" if near else "")
                ),
                exit_status=EXIT_USAGE,
                hint=(
                    f"Allowed ops: {allowed_values_text(_BATCH_OPS)}. Run any other "
                    "transform (join, math, ...) as its own `view transform` command."
                ),
                details={
                    "step": index,
                    "got": op,
                    "allowed": list(_BATCH_OPS),
                    "did_you_mean": near,
                },
            )
        if step["op"] == _BATCH_SORT_OP and any(
            isinstance(later, dict) and later.get("op") in BATCH_LAST_OPS
            for later in steps[index + 1 :]
        ):
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=(
                    f"steps[{index}] (sort) comes before a step that replaces the view's columns, "
                    "so its columns would no longer exist when the sort is applied."
                ),
                exit_status=EXIT_USAGE,
                hint="Run the sort after the batch, as its own `view transform sort` command.",
                details={"step": index, "op": _BATCH_SORT_OP},
            )
        if step["op"] in BATCH_LAST_OPS and index != len(steps) - 1:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=(
                    f"steps[{index}] ({step['op']}) replaces the view's columns, so it must be "
                    "the last step of a batch."
                ),
                exit_status=EXIT_USAGE,
                hint=f"Move steps[{index}] to the end, or run the steps after it as their own "
                "`view transform` commands.",
                details={"step": index, "op": step["op"]},
            )
    return steps


def _step_error(index: int, op: str, error: CliError) -> CliError:
    """``error`` from building step ``index``, naming the step."""
    hint = error.hint
    if error.code == CODE_UNKNOWN_COLUMN:
        hint = f"{hint} {_BATCH_COLUMN_HINT}" if hint else _BATCH_COLUMN_HINT
    return CliError(
        code=error.code,
        message=f"steps[{index}] ({op}): {error.message}",
        exit_status=error.exit_status,
        hint=hint,
        details={**error.details, "step_index": index, "op": op},
    )


def _created_columns(task_spec: dict[str, Any]) -> list[dict[str, str]]:
    """The ``{COLUMN, TYPE, INTERNAL_NAME}`` columns a built task adds, from its ``AS`` outputs.

    ``AS`` is one column (substring, extract-date, increment-date), a list of them (split) or
    sits on each item of the task's list (copy-columns).
    """
    columns: list[dict[str, str]] = []
    for body in task_spec.values():
        for item in body if isinstance(body, list) else [body]:
            made = item.get("AS") if isinstance(item, dict) else None
            if made is not None:
                columns.extend(made if isinstance(made, list) else [made])
    return columns


def _build_batch(
    invocation: Invocation, service: Any, view_id: int, dataset_id: int, steps: list[dict[str, Any]]
) -> _BatchPlan:
    """Bind and build every step against the view's current columns; send nothing."""
    plan = _BatchPlan()
    created = plan.created
    for index, step in enumerate(steps):
        op = step["op"]
        command_id = f"view.transform.{op}"
        contract = resolve_command_contract(command_id)
        assert contract is not None
        try:
            apply_input_aliases(command_id, step["input"])
            for spec in contract.fields:
                if spec.required:
                    _require_field(step["input"], spec.name)
            # The batch's own --input was admitted whole; check each step's input as
            # its own command would (types, conditions) so the error names the step.
            validate_input_fields(command_id, _without_resource_context(step["input"]))
            kwargs = _bind_transform_inputs(invocation, step["input"], command_id)
        except CliError as exc:
            raise _step_error(index, op, exc) from exc
        if op == _BATCH_LIMIT_OP and plan.sorts and not kwargs.get("order_by"):
            # A sort is only a display order; carry it so the limit keeps the rows it implies.
            kwargs["order_by"] = plan.sorts[-1]["order_by"]
        method = str((command_by_id(command_id) or {})["sdk_symbol"]).rsplit(".", 1)[-1]
        try:
            built = service.call_view(
                view_id,
                method,
                dataset_id=dataset_id,
                build_only=True,
                added_columns=created,
                **kwargs,
            )
        except CliError as exc:
            raise _step_error(index, op, exc) from exc
        if op == _BATCH_SORT_OP:
            plan.sorts.append(kwargs)
        else:
            plan.specs.append(built["task_spec"])
            created.extend(_created_columns(built["task_spec"]))
            plan.task_steps.append((index, op))
    return plan


def wait_for_added_tasks_run(
    service: Any, dataset_id: int, view_id: int, task_ids_before: set[Any], count: int
) -> list[dict[str, Any]]:
    """The runs of the ``count`` tasks a write added, oldest first, once they are over.

    Each run is ``{task_id, transform_status}``. Returns as soon as every task's
    ``transform_status`` is over, or one of them errored (the rest then never run).
    After the bound, the runs read so far: some may not be over, or fewer than
    ``count`` may be listed.
    """
    runs: list[dict[str, Any]] = []
    for delay in poll_delays(_RUN_WAIT_S, _RUN_RETRY_S):
        added = sorted(
            (t for t in _tasks(service, dataset_id, view_id) if t.get("id") not in task_ids_before),
            key=lambda task: task.get("id") or 0,
        )
        runs = [
            {"task_id": task.get("id"), "transform_status": task.get("transform_status")}
            for task in added
        ]
        statuses = [run["transform_status"] for run in runs]
        if any(status in _RUN_FAILED_STATUSES for status in statuses):
            return runs
        if len(runs) >= count and all(status == _RUN_DONE_STATUS for status in statuses):
            return runs
        time.sleep(delay)
    return runs


def _failed_batch_step(
    plan: _BatchPlan, added: list[dict[str, Any]]
) -> tuple[int, str, dict[str, Any]] | None:
    """The step whose task errored or could not bind, with that task; ``None`` if none did."""
    for (index, op), task in zip(plan.task_steps, added, strict=False):
        if task.get("transform_status") in _RUN_FAILED_STATUSES or task.get("reference_errors"):
            return index, op, task
    return None


def _batch_failure(
    service: Any,
    dataset_id: int,
    view_id: int,
    task_ids_before: set[Any],
    plan: _BatchPlan,
    cause: CliError | None,
) -> CliError:
    """Remove the tasks the batch added and report which step failed.

    The server adds a list of tasks one by one and does not undo the ones before a
    failure, so the tasks the batch left are deleted (newest first): the view ends
    as it was before. With no task added, ``cause`` is returned as it is.
    """
    added = sorted(
        (t for t in _tasks(service, dataset_id, view_id) if t.get("id") not in task_ids_before),
        key=lambda task: task.get("id") or 0,
    )
    if cause is not None and not added:
        return cause
    failed = _failed_batch_step(plan, added)
    not_removed = []
    for task in reversed(added):
        try:
            service.call(
                _TASK_DELETE_SYMBOL, dataview_id=view_id, dataset_id=dataset_id, task_id=task["id"]
            )
        except CliError:
            not_removed.append(task["id"])
    wait_for_pipeline_to_settle(service, dataset_id, view_id)
    details: dict[str, Any] = {
        "view_id": view_id,
        "removed_task_ids": [t["id"] for t in added if t["id"] not in not_removed],
        "not_removed_task_ids": not_removed,
    }
    if failed is not None:
        index, op, task = failed
        details.update(
            step_index=index,
            op=op,
            task_id=task.get("id"),
            transform_status=task.get("transform_status"),
        )
        which = (
            f"steps[{index}] ({op}) failed (task {task.get('id')}, {task.get('transform_status')})"
        )
    else:
        which = "A step of the batch failed"
    if cause is not None:
        details["cause"] = {"code": cause.code, "message": cause.message}
    outcome = (
        "none of the batch's tasks were kept."
        if not not_removed
        else f"tasks {not_removed} could not be removed."
    )
    return CliError(
        code=CODE_BATCH_STEP_FAILED,
        message=f"{which}; {outcome}",
        exit_status=EXIT_API,
        hint="Fix that step's input and send the batch again.",
        details=details,
        recovery_commands=[
            f"mammoth view task delete {view_id} {task_id} --yes" for task_id in not_removed
        ],
    )


def _apply_batch(
    invocation: Invocation, service: Any, view_id: int, dataset_id: int, plan: _BatchPlan
) -> dict[str, Any]:
    """Send the batch as one request, wait for every new task's run, then set the sort.

    A failure after the send removes the batch's tasks (see :func:`_batch_failure`).
    """
    info_before = service.call(
        _DATAVIEW_GET_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=invocation.project,
    )
    rows_before = info_before.get("row_count")
    task_ids_before = _task_ids(service, dataset_id, view_id)
    data: dict[str, Any] = {}
    runs: list[dict[str, Any]] = []
    try:
        if plan.specs:
            data = dict(
                service.call_view(
                    view_id, _ADD_TASKS_METHOD, dataset_id=dataset_id, task_specs=plan.specs
                )
            )
            if not _is_staged(data):
                runs = wait_for_added_tasks_run(
                    service, dataset_id, view_id, task_ids_before, len(plan.specs)
                )
    except CliError as exc:
        raise _batch_failure(service, dataset_id, view_id, task_ids_before, plan, exc) from exc
    if any(run["transform_status"] in _RUN_FAILED_STATUSES for run in runs):
        raise _batch_failure(service, dataset_id, view_id, task_ids_before, plan, None)
    try:
        for kwargs in plan.sorts:
            data["sort"] = service.call_view(
                view_id,
                _SORT_METHOD,
                dataset_id=dataset_id,
                added_columns=plan.created,
                **kwargs,
            )["sort"]
    except CliError as exc:
        raise _batch_failure(service, dataset_id, view_id, task_ids_before, plan, exc) from exc
    if runs:
        data["tasks"] = [
            {"step_index": index, "op": op, **run}
            for (index, op), run in zip(plan.task_steps, runs, strict=False)
        ]
    if plan.specs and not _is_staged(data):
        # The add returns with the pipeline ``ready`` and the tasks listed ``DONE`` before
        # the run has started, so a count read now is the old one (as for a draft submit).
        refreshed = wait_for_refreshed_view(
            service, dataset_id, view_id, invocation.project, info_before.get("data_updated_at")
        )
        rows_after, pipeline_error = wait_for_view_row_count(
            service, dataset_id, view_id, invocation.project, write_result=data
        )
        data["row_check"] = {"rows_before": rows_before, "rows_after": rows_after}
        if pipeline_error is None and refreshed is None:
            pipeline_error = {
                "execution_state": UNFINISHED_STATE,
                "wait_error": "the view's data was not refreshed after the batch; read it again",
            }
        if pipeline_error is not None:
            data["pipeline_error"] = pipeline_error
        elif len(runs) < len(plan.specs) or any(
            run["transform_status"] != _RUN_DONE_STATUS for run in runs
        ):
            data["pipeline_error"] = {
                "execution_state": UNFINISHED_STATE,
                "wait_error": (
                    f"{len(plan.specs)} tasks were sent; {len(runs)} were listed and "
                    "not all had finished running"
                ),
            }
    return data


def view_transform_batch(invocation: Invocation) -> HandlerResult:
    """Add several transforms in one request. ``steps`` is required.

    Each step is ``{"op": <a view transform command>, "input": <that command's input>}``.
    Every step is bound and built against the view's current columns before anything is
    sent; the tasks go as one request, so the pipeline runs once. If a task fails, the
    batch's tasks are removed and the failing step is named.
    """
    view_id = _view_id(invocation)
    document = invocation.load_input()
    steps = _batch_steps(document)
    assert document is not None
    dataset_id = _resolve_exact_dataset_id(
        invocation, view_id, document, required=False, allow_missing=True
    )
    with open_service(invocation) as (service, auth):
        if dataset_id is None:
            dataset_id = parents.lookup(_profile_name(invocation), auth.workspace_id, view_id)
        if dataset_id is None:
            raise CliError(
                code="resource_identity_required",
                message="This operation requires the exact parent dataset id.",
                exit_status=EXIT_USAGE,
                hint="Pass DATASET_ID or include dataset_id in --input.",
            )
        object.__setattr__(invocation, "known_dataset_id", int(dataset_id))
        require_expected_task_count(service, view_id, dataset_id, document)
        object.__setattr__(
            invocation,
            "exports_before",
            _read_before_write(service, view_id, int(dataset_id), invocation.project),
        )
        plan = _build_batch(invocation, service, view_id, int(dataset_id), steps)
        data = _apply_batch(invocation, service, view_id, int(dataset_id), plan)
        parents.remember(_profile_name(invocation), auth.workspace_id, {view_id: int(dataset_id)})
    return data, _meta(invocation, auth.workspace_id)
