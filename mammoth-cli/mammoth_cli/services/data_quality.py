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


def _duplicate_rows_warning(
    rows: list[Mapping[str, Any]],
    view_id: int | None,
    dataset_id: int | None,
) -> dict[str, Any] | None:
    """Return a table-level warning when the page itself holds exact duplicates.

    Scoped honestly to the rows actually read: an agent must not read this as
    table-wide duplication without separately checking the full table (e.g.
    ``view data aggregate`` COUNT vs a distinct count).
    """
    fingerprints = [json.dumps(row, sort_keys=True, default=str) for row in rows]
    counts: dict[str, int] = {}
    for fingerprint in fingerprints:
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    if not duplicate_count:
        return None
    warning: dict[str, Any] = {
        "issue": "duplicate_rows",
        "detail": (
            f"{duplicate_count} of the {len(rows)} rows read are exact duplicates "
            "of another row in this page (not checked table-wide)."
        ),
        "rows_checked": len(rows),
    }
    if view_id is not None and dataset_id is not None:
        spec = json.dumps({"dataset_id": dataset_id})
        warning["fix"] = f"mammoth view transform discard-duplicates {view_id} --input '{spec}'"
    return warning


def column_warnings(
    rows: Iterable[Mapping[str, Any]],
    column_types: Mapping[str, str],
    view_id: int | None = None,
    dataset_id: int | None = None,
) -> list[dict[str, Any]]:
    """Return warnings for text columns that hold numbers or dates, and for blanks.

    Args:
        rows: Row objects keyed by display name (a data page after relabeling).
        column_types: Display name to Mammoth type (``TEXT``, ``NUMERIC``, ...).
        view_id: The view the rows came from, used in the suggested command.
        dataset_id: The view's dataset, used for the duplicate-rows fix
            command (a mutation, so it needs the exact parent, not discovery).

    Returns:
        One record per finding: ``column``, ``issue``
        (``numbers_stored_as_text``, ``dates_stored_as_text``,
        ``blank_values`` or the table-level ``duplicate_rows``), ``detail``
        and, where one command fixes it, ``fix``. Counts are over the rows
        given (``rows_checked`` on each record).
    """
    materialised = [row for row in rows if isinstance(row, Mapping)]
    if not materialised:
        return []
    checked = len(materialised)
    warnings: list[dict[str, Any]] = []
    duplicate_warning = _duplicate_rows_warning(materialised, view_id, dataset_id)
    if duplicate_warning is not None:
        warnings.append(duplicate_warning)
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
