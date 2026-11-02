"""MEDIAN for ``view data aggregate``, computed exactly in the CLI.

The backend's volatile aggregate has no MEDIAN. Paging sorted rows to find the
middle one is slow and goes wrong on blanks, which sort last but still count. So
the CLI asks for one COUNT per stored value of the column (per group), drops the
blank values, and takes the middle of what is left. The result says how many
blank rows were skipped.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENTS, EXIT_USAGE, CliError
from mammoth_cli.services.conditions import CONDITION_KWARG
from mammoth_cli.services.read_queries import ReadContext

MEDIAN = "MEDIAN"
#: The backend returns at most this many grouped rows.
BACKEND_ROW_CAP = 40000


def _fail(message: str, hint: str = "") -> CliError:
    return CliError(code=CODE_INVALID_ARGUMENTS, message=message, exit_status=EXIT_USAGE, hint=hint)


def _items(document: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(document.get("metric"), dict):
        return [document["metric"]]
    aggregations = document.get("aggregations")
    return (
        [a for a in aggregations if isinstance(a, dict)] if isinstance(aggregations, list) else []
    )


def requested(document: dict[str, Any]) -> bool:
    """Whether the read asks for a MEDIAN."""
    return any(str(item.get("function") or "").upper() == MEDIAN for item in _items(document))


def check(document: dict[str, Any], column_types: dict[str, str], text_date_groups: bool) -> None:
    """Refuse a MEDIAN read this path cannot answer exactly, before any query."""
    items = _items(document)
    if any(str(item.get("function") or "").upper() != MEDIAN for item in items):
        raise _fail(
            "MEDIAN cannot be mixed with other functions in one read.",
            "Run the MEDIAN aggregations in their own 'view data aggregate' call.",
        )
    if text_date_groups:
        raise _fail(
            "MEDIAN cannot be grouped by a month/year of a TEXT date.",
            "Group by another column, or convert the date with 'view transform convert-type'.",
        )
    for item in items:
        column = item.get("column")
        if not column:
            raise _fail("MEDIAN needs a 'column'.")
        kind = column_types.get(str(column), "")
        if kind not in ("", "NUMERIC"):
            raise _fail(f"MEDIAN needs a NUMERIC column; '{column}' is {kind}.")


def _number(value: Any) -> float | None:
    try:
        return None if value is None or isinstance(value, bool) else float(value)
    except (TypeError, ValueError):
        return None


def weighted_median(counts: list[tuple[float, int]]) -> float | None:
    """The median of values given as (value, how many rows hold it); None when empty."""
    ordered = sorted(counts)
    total = sum(n for _, n in ordered)
    if total == 0:
        return None
    wanted = [(total - 1) // 2, total // 2]
    found: list[float] = []
    seen = 0
    for value, n in ordered:
        found.extend(value for position in wanted if seen <= position < seen + n)
        seen += n
    return (found[0] + found[1]) / 2


def _counts_by_group(
    reads: ReadContext, column: str, group_by: list[Any], condition: Any
) -> tuple[dict[tuple[Any, ...], list[tuple[float, int]]], int]:
    """(value, rows) per group for one column, and how many blank rows were left out."""
    fields: dict[str, Any] = {
        "aggregations": [{"function": "COUNT", "as_name": "n"}],
        "group_by": [*group_by, column],
        "limit": BACKEND_ROW_CAP,
    }
    if condition is not None:
        fields[CONDITION_KWARG] = condition
    rows = reads.query(**fields).get("data") or []
    if len(rows) >= BACKEND_ROW_CAP:
        raise _fail(
            "Too many distinct values to take an exact median "
            f"(the backend returns at most {BACKEND_ROW_CAP} groups).",
            "Narrow the read with a condition.",
        )
    width = len(group_by)
    counts: dict[tuple[Any, ...], list[tuple[float, int]]] = defaultdict(list)
    blank = 0
    for row in rows:
        key = tuple(row.get(f"group_{i}") for i in range(width))
        value, n = _number(row.get(f"group_{width}")), int(row.get("agg_0") or 0)
        bucket = counts[key]  # a group whose values are all blank still gets a row
        if value is None:
            blank += n
        else:
            bucket.append((value, n))
    return counts, blank


def aggregate(reads: ReadContext, fields: dict[str, Any], condition: Any) -> dict[str, Any]:
    """Answer a MEDIAN read with rows shaped like the backend's (``group_N``, ``agg_N``/``metric``).

    ``fields`` holds the resolved SDK kwargs (internal column names).
    """
    group_by = list(fields.get("group_by") or [])
    items = [fields["metric"]] if "metric" in fields else list(fields["aggregations"])
    keys = ["metric"] if "metric" in fields else [f"agg_{i}" for i in range(len(items))]
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    skipped: dict[str, int] = {}
    for key, item in zip(keys, items, strict=True):
        counts, blank = _counts_by_group(reads, item["column"], group_by, condition)
        if not group_by:
            counts.setdefault((), [])
        for group, values in counts.items():
            row = merged.setdefault(group, {f"group_{i}": v for i, v in enumerate(group)})
            row[key] = weighted_median(values)
        if blank:
            skipped[item["as_name"]] = blank
    rows = list(merged.values())
    result: dict[str, Any] = {"data": rows, "row_count": len(rows)}
    if skipped:
        named = ", ".join(f"{label}: {n}" for label, n in skipped.items())
        result["median_note"] = (
            f"MEDIAN is over non-blank values only; blank rows left out ({named})."
        )
    return result
