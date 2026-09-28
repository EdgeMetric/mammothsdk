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
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

#: A share of non-blank values at or above this reads as "meant to be" that type.
_MOSTLY = 0.8
#: Fewer non-blank values than this are too few to call a pattern.
_MIN_VALUES = 3
_MAX_EXAMPLES = 3
#: Most groups of variant spellings to name in one warning.
_MAX_VARIANT_GROUPS = 5

_NUMBER = re.compile(r"^[-+]?[$€£]?\s*\d[\d,]*(\.\d+)?\s*%?$|^[-+]?[$€£]?\s*\.\d+\s*%?$")
#: Punctuation is normalised to a space, not dropped, so "Pepsi,Cola" and
#: "Pepsi Cola" collapse the same way as "Pepsi Cola" itself.
_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")
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


def _bulk_replace_hint(view_id: int | None, column: str, mapping: list[dict[str, Any]]) -> str:
    target = str(view_id) if view_id is not None else "VIEW_ID"
    spec = json.dumps({"columns": [column], "mapping": mapping})
    return f"mammoth view transform bulk-replace {target} --input '{spec}'"


def _spelling_key(text: str) -> str:
    """Case-, whitespace- and punctuation-insensitive grouping key.

    Punctuation is replaced with a space (not dropped) before whitespace is
    collapsed, so inner punctuation ("Pepsi, Co.") normalises the same way
    as a plain space ("Pepsi Co"). This is normalisation, not fuzzy
    matching: different words ("pepsi cola") get a different key than
    ("pepsi") and are never grouped.
    """
    despaced = _WHITESPACE.sub(" ", _PUNCTUATION.sub(" ", text))
    return despaced.strip().lower()


def _variant_spelling_groups(texts: list[str]) -> list[tuple[str, list[str]]]:
    """Group distinct values that share a spelling key, keys sorted for stable output.

    Only keys with more than one distinct raw value are a "group" worth
    reporting; a single spelling of a value is not a finding.
    """
    by_key: dict[str, list[str]] = {}
    for text in dict.fromkeys(texts):  # distinct values, first-seen order
        key = _spelling_key(text)
        if not key:
            continue
        by_key.setdefault(key, []).append(text)
    groups = [(key, values) for key, values in by_key.items() if len(values) > 1]
    return sorted(groups, key=lambda item: item[0])


def _most_used_spelling(values: list[str], counts: Counter[str]) -> str:
    """The group's most frequent real spelling (first seen on a tie), trimmed.

    Never a synthesised form such as ``str.title()``, which would rewrite
    "McDonald's" as "Mcdonald'S".
    """
    return max(values, key=lambda value: counts[value]).strip()


def _variant_spellings_warning(
    column: str,
    texts: list[str],
    view_id: int | None,
    checked: int,
) -> dict[str, Any] | None:
    groups = _variant_spelling_groups(texts)
    if not groups:
        return None
    shown = groups[:_MAX_VARIANT_GROUPS]
    counts = Counter(texts)
    canonical = {key: _most_used_spelling(values, counts) for key, values in shown}
    mapping = [{"search": sorted(values), "replace": canonical[key]} for key, values in shown]
    examples = "; ".join(
        "{" + ", ".join(repr(v) for v in sorted(values)) + "}" + f" -> {canonical[key]!r}"
        for key, values in shown
    )
    detail = (
        f"{len(groups)} group(s) of values in this TEXT column differ only in case, "
        f"whitespace or punctuation and will be counted separately unless unified: {examples}."
    )
    if len(groups) > _MAX_VARIANT_GROUPS:
        detail += f" ({len(groups) - _MAX_VARIANT_GROUPS} more not shown)."
    return {
        "column": column,
        "issue": "variant_spellings",
        "detail": detail,
        "fix": _bulk_replace_hint(view_id, column, mapping),
        "rows_checked": checked,
    }


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
        ``variant_spellings``, ``blank_values`` or the table-level
        ``duplicate_rows``), ``detail`` and, where one command fixes it,
        ``fix``. Counts are over the rows given (``rows_checked`` on each
        record).
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
                    detail += f" Other values: {shown}"
                    if kind == "numbers":
                        # A value that fails this number check truly can't
                        # become NUMERIC. Dates have no such guarantee: the
                        # backend's date parser accepts formats this
                        # whitelist doesn't recognize, so claiming data loss
                        # there would be untrue.
                        detail += " (the conversion makes them empty)"
                    detail += "."
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
            variant_warning = _variant_spellings_warning(column, texts, view_id, checked)
            if variant_warning is not None:
                warnings.append(variant_warning)
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
