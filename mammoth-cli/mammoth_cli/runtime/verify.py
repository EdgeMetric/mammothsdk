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
    verified = _verified(
        data,
        check=check,
        row_count_attempted=row_count_attempted,
        rows_before=rows_before,
        rows_after=rows_after,
    )
    state = _state(data)
    verify: dict[str, Any] = {"verified": verified, "state": state}
    if row_count_attempted:
        verify["rows_before"] = rows_before
        verify["rows_after"] = rows_after
    warnings = _warnings(data)
    if row_count_attempted and rows_after is None:
        warnings.append(_UNREADABLE_ROW_COUNT_WARNING)
    verify["warnings"] = warnings
    verify["needs_user"] = _needs_user(
        data,
        verified=verified,
        state=state,
        check=check,
        row_count_attempted=row_count_attempted,
        rows_before=rows_before,
        rows_after=rows_after,
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


def _verified(
    data: dict[str, Any],
    *,
    check: dict[str, Any] | None,
    row_count_attempted: bool,
    rows_before: int | None,
    rows_after: int | None,
) -> bool:
    if data.get("has_error"):
        return False
    for status in (data.get("status"), _job_status(data)):
        if isinstance(status, str) and status.lower() in _FAILURE_STATUSES:
            return False
    pipeline_state = data.get("pipeline_state")
    if isinstance(pipeline_state, str) and pipeline_state.lower() in _FAILURE_PIPELINE_STATES:
        return False
    if data.get("bake_ok") is False:
        return False
    if row_count_attempted:
        # An attempted row count that never came back readable is never
        # reported as a known, verified count -- even when nothing else
        # flagged a failure.
        if rows_after is None:
            return False
        if (
            check is not None
            and check.get("expected_row_increase")
            and isinstance(rows_before, int)
            and isinstance(rows_after, int)
            and rows_after <= rows_before
        ):
            return False
    return True


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
    state: str,
    check: dict[str, Any] | None,
    row_count_attempted: bool,
    rows_before: int | None,
    rows_after: int | None,
) -> str | None:
    if not verified:
        if row_count_attempted and rows_after is None:
            return "The row count after the change could not be read."
        if (
            row_count_attempted
            and check is not None
            and check.get("expected_row_increase")
            and isinstance(rows_before, int)
            and isinstance(rows_after, int)
            and rows_after <= rows_before
        ):
            return f"The append added no rows (was {rows_before}, still {rows_after})."
        return f"The change failed: {state}."
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
