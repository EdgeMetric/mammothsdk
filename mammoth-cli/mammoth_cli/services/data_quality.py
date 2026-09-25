"""Column warnings computed from a page of view rows.

An agent that reads a view before building on it sees rows, not problems: a
``price`` column of numbers with a few ``"N/A"`` values is TEXT, so a chart
cannot sum it, and blanks drop out of totals. These checks name the problem
and the command that fixes it, in the output the agent is already reading.
They run on the rows a command already fetched and never make a request.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

#: A share of non-blank values at or above this reads as "meant to be" that type.
_MOSTLY = 0.8
#: Fewer non-blank values than this are too few to call a pattern.
_MIN_VALUES = 3
_MAX_EXAMPLES = 3

_NUMBER = re.compile(r"^[-+]?[$€£]?\s*\d[\d,]*(\.\d+)?\s*%?$|^[-+]?[$€£]?\s*\.\d+\s*%?$")
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d %b %Y",
    "%b %d, %Y",
)


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _is_number(text: str) -> bool:
    return bool(_NUMBER.match(text.strip()))


def _is_date(text: str) -> bool:
    candidate = text.strip()
    for fmt in _DATE_FORMATS:
        try:
            datetime.strptime(candidate, fmt)
        except ValueError:
            continue
        return True
    return False


def _convert_hint(view_id: int | None, column: str, to: str) -> str:
    target = str(view_id) if view_id is not None else "VIEW_ID"
    spec = json.dumps({"conversions": [{"column": column, "to": to}]})
    return f"mammoth view transform convert-type {target} --input '{spec}'"


def column_warnings(
    rows: Iterable[Mapping[str, Any]],
    column_types: Mapping[str, str],
    view_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return warnings for text columns that hold numbers or dates, and for blanks.

    Args:
        rows: Row objects keyed by display name (a data page after relabeling).
        column_types: Display name to Mammoth type (``TEXT``, ``NUMERIC``, ...).
        view_id: The view the rows came from, used in the suggested command.

    Returns:
        One record per finding: ``column``, ``issue``
        (``numbers_stored_as_text``, ``dates_stored_as_text`` or
        ``blank_values``), ``detail`` and, where one command fixes it, ``fix``.
        Counts are over the rows given (``rows_checked`` on each record).
    """
    materialised = [row for row in rows if isinstance(row, Mapping)]
    if not materialised:
        return []
    checked = len(materialised)
    warnings: list[dict[str, Any]] = []
    for column, col_type in column_types.items():
        values = [row.get(column) for row in materialised if column in row]
        if not values:
            continue
        present = [v for v in values if not _blank(v)]
        blanks = len(values) - len(present)
        if str(col_type).upper() == "TEXT" and len(present) >= _MIN_VALUES:
            texts = [str(v) for v in present]
            numbers = [t for t in texts if _is_number(t)]
            dates = [t for t in texts if _is_date(t)]
            for matched, issue, to, kind in (
                (numbers, "numbers_stored_as_text", "NUMERIC", "numbers"),
                (dates, "dates_stored_as_text", "DATE", "dates"),
            ):
                if len(matched) / len(texts) < _MOSTLY:
                    continue
                others = sorted({t for t in texts if t not in set(matched)})
                detail = (
                    f"{len(matched)} of {len(texts)} non-blank values are {kind}, "
                    "but the column is TEXT: charts and totals cannot use it as a "
                    f"{'number' if to == 'NUMERIC' else 'date'}."
                )
                if others:
                    shown = ", ".join(repr(o) for o in others[:_MAX_EXAMPLES])
                    detail += f" Other values: {shown} (the conversion makes them empty)."
                warnings.append(
                    {
                        "column": column,
                        "issue": issue,
                        "detail": detail,
                        "fix": _convert_hint(view_id, column, to),
                        "rows_checked": checked,
                    }
                )
                break
        if blanks:
            warnings.append(
                {
                    "column": column,
                    "issue": "blank_values",
                    "detail": (
                        f"{blanks} of {len(values)} rows are blank. Decide before you "
                        "summarise: fill them (view transform set-values with "
                        "IS_EMPTY, or fill-missing), remove the rows (view transform "
                        "filter), or keep them and say so."
                    ),
                    "rows_checked": checked,
                }
            )
    return warnings
