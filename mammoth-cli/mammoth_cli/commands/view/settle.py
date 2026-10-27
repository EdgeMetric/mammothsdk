"""Waiting for pipelines, follow-on jobs and row counts to settle."""

from __future__ import annotations

import time
from typing import Any

from mammoth_cli.commands.view._common import (
    _DATAVIEW_GET_SYMBOL,
    _DATAVIEW_LIST_SYMBOL,
    _WAIT_FOR_PIPELINE_SYMBOL,
)
from mammoth_cli.errors.envelope import (
    CliError,
)
from mammoth_cli.services.poll import poll_delays
from mammoth_cli.services.read_memo import prefetch


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
#: ``execution_state`` values that mean no run is queued or going (the server's own settle
#: check counts ``idle`` and ``runtime_error`` as quiet). After a pipeline edit the ``state``
#: reads ``ready`` while ``execution_state`` is still ``submitted`` or ``running``, and data
#: read then is the old data.
_IDLE_EXECUTION_STATES = frozenset({"idle", "runtime_error", "ref_error"})
_IDLE_POLL_CAP_S = 2.0


def wait_for_pipeline_to_settle(
    service: Any,
    dataset_id: int,
    view_id: int,
    settle_timeout: float = _ROW_CHECK_SETTLE_TIMEOUT,
    already_ready: bool = False,
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

    ``already_ready`` says the write's own SDK call already waited for this
    pipeline to be ready, so the poll is skipped; the execution error is still read.
    """
    wait_error: str | None = None
    deadline = time.monotonic() + settle_timeout
    try:
        if not already_ready:
            service.call(
                _WAIT_FOR_PIPELINE_SYMBOL,
                dataview_id=view_id,
                dataset_id=dataset_id,
                timeout=settle_timeout,
            )
        if not _wait_until_idle(service, dataset_id, view_id, deadline - time.monotonic()):
            wait_error = f"the pipeline's run was still going after {settle_timeout:g} seconds"
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
    the job succeeded, ``execution_state: "unfinished"`` (with the job id and how to
    resume) when the wait ran out while it was still running, else ``"job_failed"``
    with the job's own error text -- reported, never swallowed.
    """
    if not isinstance(write_result, dict) or not any(
        isinstance(write_result.get(key), int) for key in ("future_id", "job_id")
    ):
        return None
    try:
        service.wait_if_job(write_result)
    except CliError as exc:
        if exc.code == "timeout":
            # Out of time is not a failed job: it is still running, the change was
            # accepted, and replaying it would apply the step twice.
            pending: dict[str, Any] = {
                "execution_state": UNFINISHED_STATE,
                "wait_error": exc.message,
            }
            for key in ("job_id", "resume"):
                if exc.details.get(key) is not None:
                    pending[key] = exc.details[key]
            return pending
        return {"execution_state": JOB_FAILED_STATE, "wait_error": exc.message}
    return None


def _wait_until_idle(service: Any, dataset_id: int, view_id: int, timeout: float) -> bool:
    """Wait up to ``timeout`` seconds for the run the pipeline edit queued to finish.

    Returns True when ``execution_state`` is idle (or a run error, which the caller reports,
    or a value this does not know), False when the run is still going at ``timeout``.
    """
    for gap in (0.0, *poll_delays(max(timeout, 0.0), _IDLE_POLL_CAP_S)):
        time.sleep(gap)
        pipeline = service.call(_PIPELINE_GET_SYMBOL, dataview_id=view_id, dataset_id=dataset_id)
        state = pipeline.get("execution_state") if isinstance(pipeline, dict) else None
        if not isinstance(state, str) or state.lower() in _IDLE_EXECUTION_STATES:
            return True
    return False


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


def sdk_saw_pipeline_ready(write_result: Any) -> bool:
    """Whether the SDK's own wait for this write already saw the pipeline ``ready``."""
    return isinstance(write_result, dict) and write_result.get("pipeline_state") == "ready"


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
    already_ready = sdk_saw_pipeline_ready(write_result)
    if already_ready:
        # The pipeline state and the row count are independent reads: take both at once.
        prefetch(
            service,
            [
                (_PIPELINE_GET_SYMBOL, {"dataview_id": view_id, "dataset_id": dataset_id}),
                (
                    _DATAVIEW_GET_SYMBOL,
                    {"dataset_id": dataset_id, "dataview_id": view_id, "project_id": project_id},
                ),
            ],
        )
    try:
        pipeline_error = wait_for_pipeline_to_settle(
            service,
            dataset_id,
            view_id,
            settle_timeout,
            already_ready=already_ready,
        )
        pipeline_error = job_error or pipeline_error
        try:
            info = service.call(
                _DATAVIEW_GET_SYMBOL,
                dataset_id=dataset_id,
                dataview_id=view_id,
                project_id=project_id,
            )
        except Exception:  # noqa: BLE001 -- best effort; the write already ran
            return None, pipeline_error
    finally:
        # Nothing read ahead outlives this settle.
        memo = getattr(service, "memo", None)
        if memo is not None:
            memo.clear()
    rows_after = info.get("row_count") if isinstance(info, dict) else None
    return rows_after, pipeline_error


#: Bounded wait for a submitted draft's data: its steps run after the submit returns.
_REFRESH_ATTEMPTS = 40
_REFRESH_RETRY_S = 0.5


def wait_for_refreshed_view(
    service: Any, dataset_id: int, view_id: int, project_id: int | None, stamp_before: Any
) -> dict[str, Any] | None:
    """The view's record once its ``data_updated_at`` has moved past ``stamp_before``.

    ``None`` when it never did within the bound; the caller reports that as
    unfinished, never as a row count it did not see refreshed.
    """
    for _ in range(_REFRESH_ATTEMPTS):
        info = service.call(
            _DATAVIEW_GET_SYMBOL, dataset_id=dataset_id, dataview_id=view_id, project_id=project_id
        )
        if isinstance(info, dict) and info.get("data_updated_at") != stamp_before:
            return info
        time.sleep(_REFRESH_RETRY_S)
    return None


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
    # The response names the follow-on job that runs the pipeline; read back
    # before it ends and the view still shows the old row count (FB-05).
    rows_after, pipeline_error = wait_for_view_row_count(
        service, dataset_id, view_id, project_id, write_result=data
    )
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
