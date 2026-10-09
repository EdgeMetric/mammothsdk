"""Automatic write read-back for every real, non-read API-backed command.

A backend write returns whatever shape that particular endpoint returns —
some carry ``has_error``, some a bare ``status``, some a pipeline job with its
own nested ``status``. :func:`with_verify` reads those backend-specific
signals once and adds one small, uniform ``verify`` block to the result, so
the agent that issued the write always has an explicit answer to "did this do
what it should" instead of re-deriving it per command.
"""

from __future__ import annotations

import time
from typing import Any

from mammoth_cli.output.normalize import Revealed
from mammoth_cli.runtime.invocation import Invocation

#: Below this share of matched rows, a join has enough misses to flag before
#: the caller builds anything further on it.
JOIN_MATCH_RATE_THRESHOLD = 0.8

#: The one ``mutation_class`` (see ``spec/manifests/commands/view.yaml``) a
#: view write can carry that runs a pipeline -- the only kind that can leave a
#: downstream export referencing something the write just changed or removed.
_VIEW_PIPELINE_MUTATION_CLASS = "reversible_pipeline"
#: Pipeline writes outside that class that can still drop or rename a column
#: a saved export reads: deleting a step, renaming, editing the pipeline.
_EXPORT_BREAKING_COMMANDS = frozenset(
    {"view.task.delete", "view.transform.rename-columns", "view.pipeline.edit"}
)

_EXPORTS_LIST_SYMBOL = "mammoth.api.exports.ExportsAPI.list"
#: The export list's default representation leaves out ``error_info``, the only
#: place a saved export that can no longer run says why (ISS-225).
_EXPORT_FIELDS_FULL = "__full"
#: The backend re-validates a view's exports after a pipeline write has run, a few
#: seconds later; wait up to this long for that to show before reading them as clean.
_EXPORT_SETTLE_S = 25.0
_EXPORT_SETTLE_POLL_S = 1.0

OUTCOME_SETTLED = "settled"
OUTCOME_PENDING = "pending"
OUTCOME_FAILED = "failed"
_PENDING_STATES = frozenset({"staged", "processing"})

_FAILURE_STATUSES = frozenset({"error", "failed", "failure"})
_FAILURE_PIPELINE_STATES = frozenset({"error", "ref_error"})

#: HTTP status codes that mean "accepted, not finished" when a write's own
#: response carries no other completion signal at all.
_ACCEPTED_STATUS_CODES = frozenset({202})


#: Surfaced in ``warnings`` (and drives ``verified: false``) when a
#: ``row_check``/``join_check`` was attempted but ``rows_after`` never came
#: back readable, even after waiting for the pipeline to settle.
_UNREADABLE_ROW_COUNT_WARNING = (
    "the row count after the change could not be read; read the view before building on it"
)

#: ``reason`` for a write left in a draft: the pipeline never ran, so there is
#: no row count to check yet.
_STAGED_REASON = "staged in draft; not applied until the draft is submitted"

#: ``reason`` for a write whose settle step never ran (its parent dataset
#: could not be resolved) and whose own status is still ``processing`` --
#: never reported as verified just because nothing named a failure.
_UNSETTLED_REASON = (
    "the change was accepted but has not finished; read the view before building on it"
)


def with_verify(data: Any, invocation: Invocation | None = None) -> Any:
    """Return ``data`` with a ``verify`` read-back block added.

    ``data`` that is not a dict (a dry-run report, a bare list, ...) is
    returned unchanged. When ``invocation`` is given, a write whose own
    response is nothing but an unsettled async job (a bare ``job_id``/
    ``future_id``, or an HTTP 202 with no job reference at all) is settled
    first -- see :func:`_settle_unfinished_write` -- so it is never reported
    ``verified: true`` before it has actually finished.
    """
    if not isinstance(data, dict):
        return data
    data = _settle_unfinished_write(data, invocation)
    check = _check_dict(data)
    row_count_attempted = _row_count_attempted(check)
    rows_before, rows_after = _row_counts(check) if row_count_attempted else (None, None)
    state = _state(data)
    verified, reason = _verify_and_reason(
        data,
        state=state,
        check=check,
        row_count_attempted=row_count_attempted,
        rows_before=rows_before,
        rows_after=rows_after,
    )
    verify: dict[str, Any] = {"verified": verified, "state": state}
    if row_count_attempted:
        verify["rows_before"] = rows_before
        verify["rows_after"] = rows_after
        if _removed_nothing(check, rows_before, rows_after):
            verify["changed"] = False
    warnings = _warnings(data)
    if row_count_attempted and rows_after is None:
        warnings.append(_UNREADABLE_ROW_COUNT_WARNING)
    if "card" in data:
        verify["card"] = data["card"]
    verify["warnings"] = warnings
    verify["reason"] = reason
    verify["needs_user"] = _needs_user(
        data, verified=verified, rows_before=rows_before, rows_after=rows_after
    )
    _apply_downstream_export_check(verify, invocation)
    verify["outcome"] = _outcome(data, verify)
    result = {**data, "verify": verify}
    return Revealed(result) if isinstance(data, Revealed) else result


def _outcome(data: dict[str, Any], verify: dict[str, Any]) -> str:
    """One word for what the write came to: ``settled``, ``pending`` or ``failed``.

    ``pending`` is a write that has not taken effect yet (staged in a draft, still
    processing, or a pipeline still running when the wait ended); the caller reads
    the view again before building on it. ``failed`` is any other write that is not
    verified. Everything else is ``settled`` and its ``state`` block is the read-back.
    """
    pipeline_error = data.get("pipeline_error")
    unfinished = (
        isinstance(pipeline_error, dict) and pipeline_error.get("execution_state") == "unfinished"
    )
    if unfinished or verify["state"] in _PENDING_STATES or verify["reason"] == _UNSETTLED_REASON:
        return OUTCOME_PENDING
    return OUTCOME_SETTLED if verify["verified"] else OUTCOME_FAILED


def _removed_nothing(check: dict[str, Any] | None, before: Any, after: Any) -> bool:
    """A write meant to remove rows whose row count did not move."""
    return (
        check is not None
        and bool(check.get("expected_row_decrease"))
        and isinstance(before, int)
        and before == after
    )


def _job_status(data: dict[str, Any]) -> str | None:
    job = data.get("job")
    status = job.get("status") if isinstance(job, dict) else None
    return status if isinstance(status, str) else None


def _settle_unfinished_write(data: dict[str, Any], invocation: Invocation | None) -> dict[str, Any]:
    """Settle a write whose immediate response is an unfinished async job.

    ``wait_if_job`` (every ``MammothService``) already recognizes a bare
    ``{"job_id": N}``/``{"future_id": N}`` job reference and polls it to
    completion -- raising on failure or timeout, exactly like every other
    settle in this codebase -- but only a write handler that explicitly calls
    it gets that settle. A write whose result carries no other completion
    signal (no ``status``/``pipeline_state``/nested ``job.status``) must not
    be reported ``verified: true`` on the strength of an unpolled job
    reference, or of an HTTP 202 with no reference to poll at all.
    """
    if invocation is None or _job_status(data) is not None:
        return data
    if isinstance(data.get("status"), str) or isinstance(data.get("pipeline_state"), str):
        return data
    if _has_bare_job_reference(data):
        from mammoth_cli.runtime.session import open_service

        with open_service(invocation) as (service, _auth):
            settled = service.wait_if_job(data)
        return settled if isinstance(settled, dict) else data
    if data.get("status_code") in _ACCEPTED_STATUS_CODES:
        # Accepted, with nothing at all to poll: still not finished.
        return {**data, "status": "processing"}
    return data


def _has_bare_job_reference(data: dict[str, Any]) -> bool:
    for key in ("job_id", "future_id"):
        value = data.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return True
    return False


def _check_dict(data: dict[str, Any]) -> dict[str, Any] | None:
    """The ``row_check``/``join_check`` dict a command attached, if any."""
    for key in ("row_check", "join_check"):
        check = data.get(key)
        if isinstance(check, dict):
            return check
    return None


def _row_count_attempted(check: dict[str, Any] | None) -> bool:
    """Whether ``check`` actually attempted a row-count read-back.

    A ``join_check`` may carry only ``match_rate``/``notes`` with no row
    count involved at all; only a check that names ``rows_before``/
    ``rows_after`` -- even if the value it got back was ``None`` -- counts.
    """
    return check is not None and ("rows_before" in check or "rows_after" in check)


def _row_counts(check: dict[str, Any] | None) -> tuple[int | None, int | None]:
    if check is None:
        return None, None
    return check.get("rows_before"), check.get("rows_after")


def _pipeline_error_reason(pipeline_error: dict[str, Any]) -> str:
    """Reason text for a settled pipeline whose own ``execution_state`` errored.

    The write's own envelope can say ``status: done`` / ``pipeline_state:
    ready`` -- ``execution_state`` is a separate, more trustworthy field the
    settle step reads afresh (see ``view.py``'s ``_pipeline_execution_error``).
    An ``execution_state`` of "unknown" means that read itself failed (or
    came back malformed) -- fail loud: this is never reported as verified,
    just because nothing came back that named an error.
    """
    state = pipeline_error.get("execution_state")
    if state == "unfinished":
        return (
            f"not finished: the pipeline was still running when checked "
            f"({pipeline_error.get('wait_error')}); read the view before building on it"
        )
    if state == "job_failed":
        return f"the follow-on pipeline run failed: {pipeline_error.get('wait_error')}"
    if state == "unknown":
        return (
            "the pipeline state after this change could not be read; read the "
            "view before building on it"
        )
    reason = (
        "the pipeline hit a runtime error after this change; the view may be "
        "empty -- remove or fix the failing task"
    )
    detail_bits = []
    task_id = pipeline_error.get("task_id")
    if task_id is not None:
        detail_bits.append(f"task {task_id}")
    error_code = pipeline_error.get("error_code")
    if error_code is not None:
        detail_bits.append(f"error {error_code}")
    if detail_bits:
        reason += " (" + ", ".join(detail_bits) + ")"
    return reason


def _verify_and_reason(
    data: dict[str, Any],
    *,
    state: str,
    check: dict[str, Any] | None,
    row_count_attempted: bool,
    rows_before: int | None,
    rows_after: int | None,
) -> tuple[bool, str | None]:
    """Whether the write is verified, plus a human-readable ``reason`` for it.

    ``reason`` is set whenever ``verified`` is ``False`` (a failure or a
    no-op) and for a staged draft; it is ``None`` for an ordinary success.
    A failure never sets ``needs_user`` -- see :func:`_needs_user`, which
    covers only the two outcomes serious enough to interrupt the caller.
    """
    if data.get("changed") is False:
        message = data.get("message")
        text = message if isinstance(message, str) else ""
        return False, f"nothing changed: {text[:200]}"
    pipeline_error = data.get("pipeline_error")
    if isinstance(pipeline_error, dict):
        return False, _pipeline_error_reason(pipeline_error)
    if data.get("has_error"):
        return False, "the operation reported an error"
    if data.get("refused_files"):
        return False, "the server refused some of the files"
    for status in (data.get("status"), _job_status(data)):
        if isinstance(status, str) and status.lower() in _FAILURE_STATUSES:
            return False, "the operation failed"
        if isinstance(status, str) and status.lower() == "processing":
            return False, _UNSETTLED_REASON
    pipeline_state = data.get("pipeline_state")
    if isinstance(pipeline_state, str) and pipeline_state.lower() in _FAILURE_PIPELINE_STATES:
        return False, "the pipeline reported an error"
    if data.get("bake_ok") is False:
        return False, "the dashboard did not bake"
    if row_count_attempted:
        # An attempted row count that never came back readable is never
        # reported as a known, verified count -- even when nothing else
        # flagged a failure.
        if rows_after is None:
            return False, _UNREADABLE_ROW_COUNT_WARNING
        if check is not None and check.get("expected_row_decrease"):
            if rows_before is None:
                return False, "the row count before the change could not be read"
            if rows_before == rows_after:
                return False, f"no rows removed ({rows_before} -> {rows_after})"
        if (
            check is not None
            and check.get("expected_row_increase")
            and isinstance(rows_before, int)
            and isinstance(rows_after, int)
            and rows_after <= rows_before
        ):
            return False, "the append did not add rows"
    if state == "staged":
        return True, _STAGED_REASON
    return True, None


def _state(data: dict[str, Any]) -> str:
    for key in ("pipeline_state", "status"):
        value = data.get(key)
        if value is not None:
            return str(value)
    return "done"


def _warnings(data: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    for key, value in data.items():
        if not key.endswith("_check") or not isinstance(value, dict):
            continue
        for list_key in ("notes", "warnings"):
            items = value.get(list_key)
            if isinstance(items, list):
                notes.extend(item if isinstance(item, str) else str(item) for item in items)
    return notes


def _needs_user(
    data: dict[str, Any],
    *,
    verified: bool,
    rows_before: int | None,
    rows_after: int | None,
) -> str | None:
    """The only two outcomes worth interrupting the caller for.

    ``needs_user`` means "a serious outcome the user must hear about before
    anything is built on it" -- never "something went wrong that you can
    retry". A failed write is reported through ``verified``/``reason``
    instead (see :func:`_verify_and_reason`); it never sets this -- except a
    downstream export broken by this very write (see
    :func:`_apply_downstream_export_check`), which is serious enough to set
    both.
    """
    if not verified:
        return None
    if rows_after == 0 and isinstance(rows_before, int) and rows_before > 0:
        return f"The change left the view with no rows (was {rows_before})."
    join_check = data.get("join_check")
    match_rate = join_check.get("match_rate") if isinstance(join_check, dict) else None
    if isinstance(match_rate, (int, float)) and match_rate < JOIN_MATCH_RATE_THRESHOLD:
        percent = round(match_rate * 100)
        return (
            f"Only {percent}% of rows found a match in the join; the user should "
            "confirm before building on it."
        )
    return None


# ---------------------------------------------------------------------------
# A pipeline write can succeed on the view itself while leaving a saved
# export broken -- its target_properties still reference a column the write
# just deleted or renamed. The write's own response never carries that; only
# a fresh read of the view's exports does (T2-WPP-W2: `view export dataset`
# then `view transform delete-columns` left the export in error_info 7001,
# but the delete's own verify said verified: true with no warnings).
# ---------------------------------------------------------------------------


def _apply_downstream_export_check(verify: dict[str, Any], invocation: Invocation | None) -> None:
    """Flag a view-pipeline write that left one of its exports in error.

    Runs at most once per write, and only when the write's own signals
    already say a clean, settled success -- a write already reported
    unverified for its own reason spends no extra read here.
    """
    if invocation is None or not verify["verified"] or verify["reason"] is not None:
        return
    view_id = _pipeline_view_id(invocation)
    if view_id is None:
        return
    broken = _broken_downstream_exports(invocation, view_id, _known_dataset_id(invocation))
    if isinstance(broken, str):
        verify["warnings"] = [*verify["warnings"], broken]
        return
    if not broken:
        return
    details = [_export_error_detail(item) for item in broken]
    verify["verified"] = False
    verify["reason"] = "a saved export on this view is in error: " + "; ".join(details)
    verify["warnings"] = [*verify["warnings"], *details]
    verify["needs_user"] = (
        "A saved export on this view is in error after this change; its data will "
        "not reach its destination until this is fixed: " + "; ".join(details)
    )


def _pipeline_view_id(invocation: Invocation) -> int | None:
    """The view id a write that can break an export acted on, or None otherwise."""
    from mammoth_cli.manifest.loader import command_by_id

    record = command_by_id(invocation.command_id) or {}
    if (
        record.get("mutation_class") != _VIEW_PIPELINE_MUTATION_CLASS
        and invocation.command_id not in _EXPORT_BREAKING_COMMANDS
    ):
        return None
    for name in ("view_id", "dataview_id"):
        value = invocation.positional(name)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
    return None


def _known_dataset_id(invocation: Invocation) -> int | None:
    """The parent dataset id the write itself already carried, or None.

    From the parent the write handler resolved, else the DATASET_ID positional
    or the ``dataset_id`` input field. When it is absent the read falls back to
    the local parent memory, never a scan.
    """
    if invocation.known_dataset_id is not None:
        return invocation.known_dataset_id
    value = invocation.positional("dataset_id")
    if value is None:
        try:
            document = invocation.load_input() or {}
        except Exception:  # noqa: BLE001 -- the write already ran on this input
            document = {}
        value = document.get("dataset_id")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.strip().isdigit():
        return int(value) or None
    return None


def _broken_downstream_exports(
    invocation: Invocation, view_id: int, dataset_id: int | None = None
) -> list[dict[str, Any]] | str:
    """Exports on ``view_id`` now in error, read at ``__full`` (the default omits ``error_info``).

    Each export the backend hands back already carries its own ``error_info``
    when it can no longer run (see ``mammoth.models.exports.ItemExportInfo``);
    this is the one read that surfaces it. A read that itself fails returns
    the warning to show instead: it must not hide the write's own,
    already-settled success, nor pass silently.
    """
    # Imported here: the session and parent memory pull in the command layer.
    from mammoth_cli.context import profiles
    from mammoth_cli.runtime import parents
    from mammoth_cli.runtime.session import open_service

    kwargs: dict[str, Any] = {"dataview_id": view_id, "fields": _EXPORT_FIELDS_FULL}
    try:
        with open_service(invocation) as (service, auth):
            if dataset_id is None:
                dataset_id = parents.lookup(
                    invocation.profile or profiles.get_selected(), auth.workspace_id, view_id
                )
            if dataset_id is not None:
                kwargs["dataset_id"] = dataset_id
            read_data = service.call(_EXPORTS_LIST_SYMBOL, **kwargs)
            deadline = time.monotonic() + _EXPORT_SETTLE_S
            while (
                invocation.exports_before is not None
                and export_stamps(read_data) == invocation.exports_before
                and export_stamps(read_data)
                and time.monotonic() < deadline
            ):
                time.sleep(_EXPORT_SETTLE_POLL_S)
                read_data = service.call(_EXPORTS_LIST_SYMBOL, **kwargs)
    except Exception as exc:  # noqa: BLE001 -- the write already succeeded
        return f"could not check this view's saved exports: {exc}"
    return [
        item
        for item in _listing_exports(read_data)
        if isinstance(item, dict) and item.get("error_info")
    ]


def _listing_exports(listing: Any) -> list[Any]:
    """The ``exports`` of a listing the SDK answered (a model, or a dict)."""
    plain = listing.model_dump(mode="json") if hasattr(listing, "model_dump") else listing
    exports = plain.get("exports") if isinstance(plain, dict) else None
    return exports if isinstance(exports, list) else []


def export_stamps(listing: Any) -> dict[int, str]:
    """Each export's ``last_modified_time`` by id, from an exports listing."""
    exports = _listing_exports(listing)
    return {
        int(item["id"]): str(item.get("last_modified_time"))
        for item in exports
        if isinstance(item, dict) and item.get("id") is not None
    }


def read_export_stamps(service: Any, view_id: int, dataset_id: int) -> dict[int, str] | None:
    """The view's exports' stamps, read before a pipeline write (see ``exports_before``).

    ``None`` when the read fails: the check after the write reads the exports again and
    reports a failure there, so this one only loses the wait for the backend's re-validation.
    """
    try:
        listing = service.call(
            _EXPORTS_LIST_SYMBOL, dataview_id=view_id, dataset_id=dataset_id, fields="__standard"
        )
    except Exception:  # noqa: BLE001 -- see the docstring
        return None
    return export_stamps(listing)


def _export_error_detail(item: dict[str, Any]) -> str:
    """Human-readable ``"export <id> (<handler>): ..."`` line for one broken export."""
    error_info = item.get("error_info")
    error_info = error_info if isinstance(error_info, dict) else {}
    # the backend nests the details: error_info.additional_info.{error_code,
    # reference_errors} (live `view export get`, T2-WPP-W2)
    nested = error_info.get("additional_info")
    error_info = {**error_info, **nested} if isinstance(nested, dict) else error_info
    what = f"export {item.get('id')}"
    handler_type = item.get("handler_type")
    if handler_type:
        what += f" ({handler_type})"
    error_code = error_info.get("error_code")
    detail = f"error {error_code}" if error_code is not None else "an error"
    columns = _export_error_columns(error_info)
    if columns:
        detail += f", column(s) {', '.join(columns)}"
    return f"{what} is in error: {detail}"


def _export_error_columns(error_info: dict[str, Any]) -> list[str]:
    """Column display names named by an export's ``error_info.reference_errors``."""
    reference_errors = error_info.get("reference_errors")
    if isinstance(reference_errors, dict):
        entries = reference_errors.get("reference_errors") or []
    elif isinstance(reference_errors, list):
        entries = reference_errors
    else:
        entries = []
    names: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        column = entry.get("column")
        name = column.get("display_name") if isinstance(column, dict) else column
        if isinstance(name, str):
            names.append(name)
    return names
