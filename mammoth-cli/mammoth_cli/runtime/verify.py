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


def with_verify(data: Any) -> Any:
    """Return ``data`` with a ``verify`` read-back block added.

    ``data`` that is not a dict (a dry-run report, a bare list, ...) is
    returned unchanged.
    """
    if not isinstance(data, dict):
        return data
    verified = _verified(data)
    state = _state(data)
    rows_before, rows_after = _row_counts(data)
    verify: dict[str, Any] = {"verified": verified, "state": state}
    if rows_before is not None or rows_after is not None:
        verify["rows_before"] = rows_before
        verify["rows_after"] = rows_after
    verify["warnings"] = _warnings(data)
    verify["needs_user"] = _needs_user(
        data, verified=verified, state=state, rows_before=rows_before, rows_after=rows_after
    )
    return {**data, "verify": verify}


def _job_status(data: dict[str, Any]) -> str | None:
    job = data.get("job")
    status = job.get("status") if isinstance(job, dict) else None
    return status if isinstance(status, str) else None


def _verified(data: dict[str, Any]) -> bool:
    if data.get("has_error"):
        return False
    for status in (data.get("status"), _job_status(data)):
        if isinstance(status, str) and status.lower() in _FAILURE_STATUSES:
            return False
    pipeline_state = data.get("pipeline_state")
    if isinstance(pipeline_state, str) and pipeline_state.lower() in _FAILURE_PIPELINE_STATES:
        return False
    return data.get("bake_ok") is not False


def _state(data: dict[str, Any]) -> str:
    for key in ("pipeline_state", "status"):
        value = data.get(key)
        if value is not None:
            return str(value)
    return "done"


def _row_counts(data: dict[str, Any]) -> tuple[int | None, int | None]:
    for key in ("row_check", "join_check"):
        check = data.get(key)
        if isinstance(check, dict):
            return check.get("rows_before"), check.get("rows_after")
    return None, None


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
    rows_before: int | None,
    rows_after: int | None,
) -> str | None:
    if not verified:
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
