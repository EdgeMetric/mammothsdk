"""The named opt-in for an append that leaves destination columns blank.

An append only writes the columns its mapping fills; every other destination
column is NULL in each appended row. The caller must name exactly those
columns in ``blank_columns`` -- the same explicit acknowledgement pattern as
``replace_table`` on a database export -- so a partial append is deliberate.
"""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

BLANK_COLUMNS_FIELD = "blank_columns"


def acknowledged_blank_columns(
    destination_id: int, blank: list[str], acknowledged: Any
) -> list[str]:
    """Return the warnings for ``blank`` (empty when none), refusing an unnamed leave-blank.

    ``acknowledged`` is the input's ``blank_columns`` value; it must list
    exactly the ``blank`` names as a set. A blanket ``true`` or a mismatched
    list is refused with the expected list shown.
    """
    if not blank:
        return []
    expected = sorted(blank)
    given = (
        {str(name) for name in acknowledged}
        if isinstance(acknowledged, list) and not isinstance(acknowledged, bool)
        else None
    )
    if given != set(expected):
        listed = ", ".join(expected)
        raise CliError(
            code="append_leaves_columns_blank",
            message=(
                f"Appending into dataset {destination_id} leaves column(s) {listed} "
                "blank (NULL) in every appended row."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                "If that is intended, add "
                f'"{BLANK_COLUMNS_FIELD}": {_json_list(expected)} to the input to confirm; '
                "otherwise map a source column to each of them."
            ),
            details={"blank_columns": expected, "acknowledged": acknowledged},
        )
    return [f"appended rows leave column(s) {', '.join(expected)} blank (NULL), as confirmed"]


def _json_list(names: list[str]) -> str:
    """The names as a JSON array literal, for the hint."""
    return json.dumps(names)
