"""Add or remove datasets on a data-refresh automation (``automation update``)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    EXIT_USAGE,
    CliError,
)

TASK_TYPE_REFRESH = "run_data_retrieval"
ADD_FIELD = "add_datasets"
REMOVE_FIELD = "remove_datasets"
DATASET_FIELDS = (ADD_FIELD, REMOVE_FIELD)
#: Keys the CLI itself binds from the positional argument; they are not the caller's.
_BOUND_FIELDS = ("automation_id",)


def wants_dataset_change(document: dict[str, Any]) -> bool:
    """Whether ``document`` asks for a dataset change instead of carrying a ``patch``.

    Args:
        document: The parsed ``--input`` document.

    Returns:
        True when it has ``add_datasets`` or ``remove_datasets`` and no ``patch``.
    """
    return "patch" not in document and any(field in document for field in DATASET_FIELDS)


def requested_ids(document: dict[str, Any], field: str) -> list[int]:
    """The dataset ids under ``field`` in ``document``.

    Args:
        document: The parsed ``--input`` document.
        field: ``add_datasets`` or ``remove_datasets``.

    Returns:
        The ids, in the order given (empty when the field is absent).

    Raises:
        CliError: ``invalid_argument`` when the field is not a list of integers.
    """
    value = document.get(field, [])
    if not isinstance(value, list) or any(
        isinstance(item, bool) or not isinstance(item, int) for item in value
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The '{field}' input field must be a list of dataset ids.",
            exit_status=EXIT_USAGE,
            hint=f"For example: --input '{{\"{field}\": [123, 456]}}'.",
        )
    return list(value)


def unknown_dataset_fields(document: dict[str, Any]) -> list[str]:
    """Input keys that do not belong with a dataset change.

    Args:
        document: The parsed ``--input`` document.

    Returns:
        The keys other than ``add_datasets``, ``remove_datasets`` and the bound automation id.
    """
    return sorted(key for key in document if key not in (*DATASET_FIELDS, *_BOUND_FIELDS))


def current_dataset_ids(automation: dict[str, Any]) -> list[int]:
    """The datasets a data-refresh automation refreshes now.

    Args:
        automation: The automation as ``automation get`` returns it.

    Returns:
        The dataset ids, in order and without repeats.
    """
    ids: list[int] = []
    for task in automation.get("tasks") or []:
        if not isinstance(task, dict) or task.get("task_type") != TASK_TYPE_REFRESH:
            continue
        for entry in task.get("details") or []:
            ds_id = _entry_dataset_id(entry)
            if ds_id is not None and ds_id not in ids:
                ids.append(ds_id)
    return ids


def dataset_patch(
    automation: dict[str, Any], add: list[int], remove: list[int]
) -> tuple[list[dict[str, Any]], list[int]]:
    """The ``details`` patch that adds and removes datasets, with the schedule kept.

    The backend applies a task change only together with the automation's conditions, so
    those are sent back as read. ``start_now`` is set to false so the edit does not start
    a refresh run by itself.

    Args:
        automation: The automation as ``automation get`` returns it.
        add: Dataset ids to add.
        remove: Dataset ids to remove.

    Returns:
        The patch list and the dataset ids the automation will refresh.

    Raises:
        CliError: ``invalid_argument`` when the automation has no data-refresh task, the
            change asks for nothing, or it would leave no dataset.
    """
    current = current_dataset_ids(automation)
    if not any(
        isinstance(task, dict) and task.get("task_type") == TASK_TYPE_REFRESH
        for task in automation.get("tasks") or []
    ):
        raise _refused("This automation has no data-refresh (run_data_retrieval) task.")
    if not add and not remove:
        raise _refused("Give at least one dataset id in add_datasets or remove_datasets.")
    overlap = sorted(set(add) & set(remove))
    if overlap:
        raise _refused(f"Dataset(s) {overlap} are in both add_datasets and remove_datasets.")
    result = [ds_id for ds_id in current if ds_id not in remove]
    result += [ds_id for ds_id in dict.fromkeys(add) if ds_id not in result]
    if not result:
        raise _refused("An automation must refresh at least one dataset; delete it instead.")
    value: dict[str, Any] = {
        "tasks": [
            {
                "task_type": TASK_TYPE_REFRESH,
                "details": {"ds_details": [{"ds_id": ds_id} for ds_id in result]},
            }
        ],
        "conditions": [_condition(item) for item in automation.get("conditions") or []],
    }
    if automation.get("condition_mode"):
        value["condition_mode"] = automation["condition_mode"]
    return [{"op": "replace", "path": "details", "value": value}], result


def _condition(item: Any) -> Any:
    """One condition as read, written back without starting a run."""
    if not isinstance(item, dict):
        return item
    details = item.get("details")
    return {
        "condition_type": item.get("condition_type"),
        "details": {**details, "start_now": False} if isinstance(details, dict) else details,
    }


def _entry_dataset_id(entry: Any) -> int | None:
    """The dataset id of one task entry (``ds_details.ds_id`` or ``ds_id``)."""
    if not isinstance(entry, dict):
        return None
    nested = entry.get("ds_details")
    value = nested.get("ds_id") if isinstance(nested, dict) else entry.get("ds_id")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _refused(message: str) -> CliError:
    """An ``invalid_argument`` usage error for a dataset change."""
    return CliError(code=CODE_INVALID_ARGUMENT, message=message, exit_status=EXIT_USAGE)
