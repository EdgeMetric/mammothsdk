"""Change a data-refresh automation's schedule (``automation update`` with ``schedule``).

mammothsdk#381 item 7: moving a weekly refresh from Tuesday to Monday was not possible.
A ``details`` patch with only ``conditions`` is answered 200 and dropped (verified on
gorakhpur 11-03); with the tasks sent back beside it the new schedule is applied.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.automation_datasets import (
    CONDITION_SCHEDULE,
    TASK_TYPE_REFRESH,
    current_dataset_ids,
)
from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError

SCHEDULE_FIELD = "schedule"
#: The schedule fields a caller may change; the rest of the stored details is kept.
SCHEDULE_KEYS = ("frequency", "interval", "by_week_day", "by_month_day", "start_at", "until")
_BOUND_FIELDS = ("automation_id",)
_EXAMPLE = '{"schedule": {"by_week_day": ["mo"], "start_at": "2026-11-09T07:00:00"}}'


def wants_schedule_change(document: dict[str, Any]) -> bool:
    """Whether ``document`` asks for a schedule change instead of carrying a ``patch``."""
    return "patch" not in document and SCHEDULE_FIELD in document


def schedule_patch(
    automation: dict[str, Any], document: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The ``details`` patch that changes the schedule, with the refreshed datasets kept.

    Args:
        automation: The automation as ``automation get`` returns it.
        document: The ``--input`` document, ``{"schedule": {...}}``.

    Returns:
        The patch list and the schedule details it writes.

    Raises:
        CliError: ``invalid_argument`` for other input keys, an unknown schedule field, an
            automation that is not a data refresh or has other task types, or one without exactly one timing
            condition.
    """
    stray = sorted(key for key in document if key not in (SCHEDULE_FIELD, *_BOUND_FIELDS))
    if stray:
        raise _refused(f"Give 'schedule' on its own. Got also: {stray}.")
    changes = document[SCHEDULE_FIELD]
    if not isinstance(changes, dict) or not changes:
        raise _refused(f"'schedule' must be an object of the fields to change, e.g. {_EXAMPLE}.")
    unknown = sorted(key for key in changes if key not in SCHEDULE_KEYS)
    if unknown:
        raise _refused(f"'schedule' takes {', '.join(SCHEDULE_KEYS)}; not {unknown}.")
    others = sorted(
        {
            str(task.get("task_type"))
            for task in automation.get("tasks") or []
            if isinstance(task, dict) and task.get("task_type") != TASK_TYPE_REFRESH
        }
    )
    if others:
        raise _refused(
            f"This automation also has {', '.join(others)} task(s). Mammoth applies a details "
            "patch by its first task's type only, so they cannot be sent back with the new "
            "schedule; nothing was changed. Use a 'patch' with the whole tasks and conditions."
        )
    datasets = _refresh_entries(automation)
    if not datasets:
        raise _refused(
            "Only a data-refresh (run_data_retrieval) automation's schedule can be changed "
            "this way: its datasets are written back with the new schedule."
        )
    conditions = [c for c in automation.get("conditions") or [] if isinstance(c, dict)]
    timing = [c for c in conditions if c.get("condition_type") == CONDITION_SCHEDULE]
    if len(timing) != 1:
        raise _refused(
            f"This automation has {len(timing)} timing conditions; a schedule change needs "
            "exactly one. Use a 'patch' with the whole conditions list instead."
        )
    found = timing[0].get("details")
    stored: dict[str, Any] = found if isinstance(found, dict) else {}
    details = {**stored, **changes, "start_now": False}
    written = [
        {
            "condition_type": c.get("condition_type"),
            "details": details if c is timing[0] else _without_start(c.get("details")),
        }
        for c in conditions
    ]
    value: dict[str, Any] = {
        "tasks": [
            {
                "task_type": TASK_TYPE_REFRESH,
                "details": {"ds_details": datasets},
            }
        ],
        "conditions": written,
    }
    mode = automation.get("condition_mode") or next(
        (c["condition_mode"] for c in conditions if c.get("condition_mode")), None
    )
    if mode:
        value["condition_mode"] = mode
    return [{"op": "replace", "path": "details", "value": value}], details


def reject_conditions_without_tasks(patch: Any) -> None:
    """Refuse a ``details`` patch that sets ``conditions`` but no ``tasks``: the server
    answers it with 200 and keeps the old schedule."""
    if not isinstance(patch, list):
        return
    for item in patch:
        value = item.get("value") if isinstance(item, dict) else None
        if (
            isinstance(item, dict)
            and item.get("path") == "details"
            and isinstance(value, dict)
            and "conditions" in value
            and "tasks" not in value
        ):
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=(
                    "A details patch with conditions but no tasks is accepted by Mammoth and "
                    "then ignored: the schedule would not change."
                ),
                exit_status=EXIT_USAGE,
                hint=(
                    "For a data-refresh automation use --input '" + _EXAMPLE + "' (the "
                    "datasets are kept); otherwise send the tasks beside the conditions."
                ),
            )


def _refresh_entries(automation: dict[str, Any]) -> list[dict[str, Any]]:
    """The refreshed datasets as stored, each with all its options, one per dataset id."""
    wanted = current_dataset_ids(automation)
    found: dict[int, dict[str, Any]] = {}
    for task in automation.get("tasks") or []:
        if not isinstance(task, dict) or task.get("task_type") != TASK_TYPE_REFRESH:
            continue
        for entry in task.get("details") or []:
            nested = entry.get("ds_details") if isinstance(entry, dict) else None
            record = nested if isinstance(nested, dict) else entry
            if isinstance(record, dict) and record.get("ds_id") in wanted:
                found.setdefault(record["ds_id"], dict(record))
    return [found[ds_id] for ds_id in wanted]


def _without_start(details: Any) -> Any:
    """Another condition's details, written back so the edit starts no run."""
    return {**details, "start_now": False} if isinstance(details, dict) else details


def _refused(message: str) -> CliError:
    return CliError(code=CODE_INVALID_ARGUMENT, message=message, exit_status=EXIT_USAGE)
