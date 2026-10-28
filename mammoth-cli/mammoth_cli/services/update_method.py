"""A dataset's update method: whether a new file or pull replaces its rows or adds to them.

The platform stores it as ``data_addition_mode`` (``replace`` or ``combine``) in the
dataset's schema settings; the web app calls it the dataset's "Update Method". Every
upload into the dataset (``file upload`` with ``append_to_ds_id``) and every folder
automation feeding it follows it.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError

GET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.get_update_method"
SET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.set_update_method"

#: The words a caller may use for each stored mode.
_MODES = {"replace": "replace", "add": "combine", "combine": "combine", "append": "combine"}

#: What each stored mode does to the next file, said plainly.
EFFECTS = {
    "replace": "Each new file replaces the dataset's rows.",
    "combine": "Each new file adds its rows to the dataset's rows.",
}


def parse_mode(value: Any) -> str:
    """The stored mode for a caller's ``mode`` (``replace``, ``add`` or ``combine``).

    Args:
        value: The ``mode`` field of the input.

    Returns:
        ``replace`` or ``combine``.

    Raises:
        CliError: ``invalid_argument`` when the value is not one of the accepted words.
    """
    mode = _MODES.get(str(value).strip().lower()) if isinstance(value, str) else None
    if mode is None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"'mode' must be 'replace' or 'add', got {value!r}.",
            exit_status=EXIT_USAGE,
            hint=(
                "'replace' makes each new file replace the dataset's rows; 'add' adds them "
                "to the rows already there."
            ),
            details={"field": "mode", "accepted": ["replace", "add"]},
        )
    return mode


def describe(result: Any, dataset_id: int) -> dict[str, Any]:
    """Shape the SDK's update-method read or write into the command result.

    Args:
        result: What ``get_update_method`` (the stored settings) or ``set_update_method``
            (``{"data_addition_mode", "previous_data_addition_mode", "schema_settings"}``)
            returned.
        dataset_id: The dataset it is for.

    Returns:
        ``{"dataset_id", "mode", "effect", "schema_mapping"}``, plus ``previous_mode``
        after a change. ``mode`` is ``add`` or ``replace``; a dataset with nothing stored
        reads as the platform default, ``add``.
    """
    body = result if isinstance(result, dict) else {}
    settings = body.get("schema_settings", body)
    stored = body.get("data_addition_mode") or "combine"
    shaped: dict[str, Any] = {
        "dataset_id": dataset_id,
        "mode": _word(stored),
        "effect": EFFECTS.get(stored, ""),
        "schema_mapping": settings.get("schema_mapping") if isinstance(settings, dict) else None,
    }
    if "previous_data_addition_mode" in body:
        previous = body.get("previous_data_addition_mode") or "combine"
        shaped["previous_mode"] = _word(previous)
        shaped["changed"] = previous != stored
    return shaped


def _word(stored: str) -> str:
    """The caller's word for a stored mode: ``combine`` reads as ``add``."""
    return "add" if stored == "combine" else stored
