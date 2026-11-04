"""One line per automation for ``automation list``: when it runs, next run, what it touches.

ILG friction 11-03 (#7): the list was a bare JSON dump, the schedule buried in
``conditions[].details``, so a weekly refresh's weekday and dataset count were parsed by hand.
"""

from __future__ import annotations

from typing import Any

_DAYS = {"mo": "Mon", "tu": "Tue", "we": "Wed", "th": "Thu", "fr": "Fri", "sa": "Sat", "su": "Sun"}
_UNITS = {"minutely": "minute", "hourly": "hour", "daily": "day", "weekly": "week"}


def summary(record: dict[str, Any]) -> dict[str, Any]:
    """``{"runs", "next_run", "datasets", "last_run"}`` for one automation, plus ``workflows``
    and ``last_failure`` when there are any."""
    tasks = [task for task in record.get("tasks") or [] if isinstance(task, dict)]
    details = [d for task in tasks for d in task.get("details") or [] if isinstance(d, dict)]
    occurrences = [
        str(r["next_occurrence"])
        for task in tasks
        for r in task.get("recurrence_details") or []
        if isinstance(r, dict) and r.get("next_occurrence")
    ]
    runs = [str(d["last_run"]) for d in details if d.get("last_run")]
    runs += [
        str(r["last_run_at"])
        for task in tasks
        for r in task.get("recurrence_details") or []
        if isinstance(r, dict) and r.get("last_run_at")
    ]
    failures = [
        _failure_text(d.get("last_run_result")) for d in details if d.get("last_run_result")
    ]
    result: dict[str, Any] = {
        "runs": "; ".join(
            _trigger(c) for c in record.get("conditions") or [] if isinstance(c, dict)
        )
        or "manually",
        "next_run": min(occurrences) if occurrences and record.get("status") == "active" else None,
        "datasets": len(_dataset_ids(details)),
        "last_run": max(runs) if runs else None,
    }
    workflows = {d["workflow_id"] for d in details if isinstance(d.get("workflow_id"), int)}
    if workflows:
        result["workflows"] = len(workflows)
    failure = next((text for text in failures if text), None)
    if failure:
        result["last_failure"] = failure
    return result


def _trigger(condition: dict[str, Any]) -> str:
    """One condition in words: "weekly on Tue at 07:00", "when a file lands in its folder"."""
    kind = condition.get("condition_type")
    details = condition.get("details") if isinstance(condition.get("details"), dict) else {}
    assert isinstance(details, dict)
    if kind == "new_data_addition_in_folder":
        return "when a file lands in its folder"
    if kind == "run_config" and details.get("trigger_type") == "manual":
        return "manually"
    if kind != "at_specific_time":
        return str(kind)
    frequency = str(details.get("frequency") or "")
    interval = details.get("interval") or 1
    unit = _UNITS.get(frequency)
    if frequency == "monthly":
        words = "monthly"
        if details.get("by_month_day"):
            words += " on " + ", ".join(_month_day(day) for day in details["by_month_day"])
    elif unit:
        words = (
            f"every {interval} {unit}s"
            if interval != 1
            else ("daily" if unit == "day" else f"every {unit}")
        )
        if unit == "week":
            words = "weekly" if interval == 1 else words
    else:
        words = frequency or "once"
    days = [_DAYS.get(str(day), str(day)) for day in details.get("by_week_day") or []]
    if days:
        words += " on " + ", ".join(days)
    start = str(details.get("start_at") or "")
    if len(start) >= 16 and frequency not in ("minutely", "hourly"):
        words += f" at {start[11:16]}"
    if details.get("until"):
        words += f" until {str(details['until'])[:10]}"
    return words


def _month_day(day: Any) -> str:
    """``1`` -> "day 1"; ``-1`` -> "the last day" (rrule counts negative days from the end)."""
    if day == -1:
        return "the last day"
    if isinstance(day, int) and day < -1:
        return f"day {-day} from the end"
    return f"day {day}"


def _dataset_ids(details: list[dict[str, Any]]) -> set[int]:
    """Datasets a task refreshes or writes into."""
    ids: set[int] = set()
    for entry in details:
        nested = entry.get("ds_details")
        if isinstance(nested, dict) and isinstance(nested.get("ds_id"), int):
            ids.add(nested["ds_id"])
        for key in ("destination_dataset_ids", "dataset_ids"):
            ids.update(i for i in entry.get(key) or [] if isinstance(i, int))
        for key in ("ds_id", "dataset_id"):
            if isinstance(entry.get(key), int):
                ids.add(entry[key])
    return ids


def _failure_text(result: Any) -> str:
    """The failure reason in a task's last result, unwrapped; "" when it did not fail."""
    reason = result.get("failure_reason") if isinstance(result, dict) else None
    while isinstance(reason, dict):
        reason = reason.get("failure_reason") or reason.get("message")
    return str(reason)[:200] if reason else ""
