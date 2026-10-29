"""A dataset's update method: whether a new file or pull replaces its rows or adds to them.

The platform stores it as ``data_addition_mode`` (``replace`` or ``combine``) in the
dataset's schema settings; the web app calls it the dataset's "Update Method". Every
upload into the dataset (``file upload`` with ``append_to_ds_id``) and every folder
automation feeding it follows it. The words, their effects and the reading of the stored
value are the SDK's (``mammoth.appends``); this module only turns them into CLI results
and errors.
"""

from __future__ import annotations

from typing import Any

from mammoth.appends import (
    UnknownUpdateMethodError,
    describe_update_method,
    stored_mode,
    unknown_update_method,
)

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError

SET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.set_update_method"


def parse_mode(value: Any) -> str:
    """The stored mode for a caller's ``mode`` (``replace``, ``add`` or ``combine``).

    Args:
        value: The ``mode`` field of the input.

    Returns:
        ``replace`` or ``combine``.

    Raises:
        CliError: ``invalid_argument`` when the value is not one of the accepted words.
    """
    try:
        return stored_mode(value)
    except UnknownUpdateMethodError:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"'mode' must be 'replace' or 'add', got {value!r}.",
            exit_status=EXIT_USAGE,
            hint=(
                "'replace' makes each new file replace the dataset's rows; 'add' adds them "
                "to the rows already there."
            ),
            details={"field": "mode", "accepted": ["replace", "add"]},
        ) from None


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
        reads as the platform default, ``add``. A stored mode this CLI does not know reads
        as ``mode: null`` with the reason in ``error``: it is reported, never guessed.
    """
    try:
        shaped = describe_update_method(result)
    except UnknownUpdateMethodError as unknown:
        shaped = unknown_update_method(str(unknown))
    return {"dataset_id": dataset_id, **shaped}
