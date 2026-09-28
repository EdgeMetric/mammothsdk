"""Automatic write read-back for every real, non-read API-backed command.

A backend write returns whatever shape that particular endpoint returns —
some carry ``has_error``, some a bare ``status``, some a pipeline job with its
own nested ``status``. :func:`with_verify` reads those backend-specific
signals once and adds one small, uniform ``verify`` block to the result, so
the agent that issued the write always has an explicit answer to "did this do
what it should" instead of re-deriving it per command.
"""

from __future__ import annotations

from typing import Any

#: Below this share of matched rows, a join has enough misses to flag before
#: the caller builds anything further on it.
JOIN_MATCH_RATE_THRESHOLD = 0.8

_FAILURE_STATUSES = frozenset({"error", "failed", "failure"})
_FAILURE_PIPELINE_STATES = frozenset({"error", "ref_error"})


#: Surfaced in ``warnings`` (and drives ``verified: false``) when a
#: ``row_check``/``join_check`` was attempted but ``rows_after`` never came
#: back readable, even after waiting for the pipeline to settle.
_UNREADABLE_ROW_COUNT_WARNING = (
    "the row count after the change could not be read; read the view before building on it"
)

#: ``reason`` for a write left in a draft: the pipeline never ran, so there is
#: no row count to check yet.
_STAGED_REASON = "staged in draft; not applied until the draft is submitted"


def with_verify(data: Any) -> Any:
    """Return ``data`` with a ``verify`` read-back block added.

    ``data`` that is not a dict (a dry-run report, a bare list, ...) is
    returned unchanged.
    """
    if not isinstance(data, dict):
        return data
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
    warnings = _warnings(data)
    if row_count_attempted and rows_after is None:
        warnings.append(_UNREADABLE_ROW_COUNT_WARNING)
    verify["warnings"] = warnings
    verify["reason"] = reason
    verify["needs_user"] = _needs_user(
        data, verified=verified, rows_before=rows_before, rows_after=rows_after
    )
    return {**data, "verify": verify}


def _job_status(data: dict[str, Any]) -> str | None:
    job = data.get("job")
    status = job.get("status") if isinstance(job, dict) else None
    return status if isinstance(status, str) else None


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
    if pipeline_error.get("execution_state") == "unknown":
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
    for status in (data.get("status"), _job_status(data)):
        if isinstance(status, str) and status.lower() in _FAILURE_STATUSES:
            return False, "the operation failed"
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
    instead (see :func:`_verify_and_reason`); it never sets this.
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
