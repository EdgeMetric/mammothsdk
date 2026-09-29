"""Read-only handling of dates stored as TEXT.

The volatile-query route buckets (``truncate``) only a DATE column, and its
condition compares a TEXT column lexically. Neither can answer "by month" or
"since March" over a column of ``"11/8/2017"`` strings, and the only sanctioned
fix (``view transform convert-type``) is a pipeline write. This module reads the
stored strings back, detects their format from the data, and parses them in the
CLI. It never guesses: an ambiguous day/month order, a mix of formats, or a
value that is not a date raises a :class:`CliError` that says why.

Pure functions only -- no service calls -- so the rules are testable directly.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENTS, EXIT_USAGE, CliError

#: Most distinct stored values one text-date read will parse.
MAX_DISTINCT_VALUES = 5000
#: Truncation levels a text date can be bucketed to (a date has no time part here).
LEVELS = ("DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "DECADE")
#: Aggregate functions that can be recombined from per-day groups.
ADDITIVE_FUNCTIONS = frozenset({"SUM", "COUNT", "MIN", "MAX"})

_MAX_EXAMPLES = 5
_MONTHS = {
    name: number
    for number, name in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1
    )
}
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z?)?$")
_NUMERIC_PARTS = re.compile(r"^(\d{1,2})([/.-])(\d{1,2})\2(\d{4})(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?$")
_DAY_MONTH_NAME = re.compile(r"^(\d{1,2})[ -]([A-Za-z]{3,9})[ ,-]+(\d{4})$")
_MONTH_NAME_DAY = re.compile(r"^([A-Za-z]{3,9})\.? (\d{1,2}),? (\d{4})$")


@dataclass(frozen=True)
class TextDateFormat:
    """A stored text-date format and why it was chosen."""

    label: str
    shape: str
    order: str
    reason: str


def _fail(message: str, hint: str, details: dict[str, Any] | None = None) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=message,
        exit_status=EXIT_USAGE,
        hint=hint,
        details=details or {},
    )


def _text(value: Any) -> str:
    return str(value).strip()


def _blank(value: Any) -> bool:
    return value is None or not _text(value)


def _shape_of(text: str) -> str | None:
    """Classify one stored string, or return ``None`` when it is no known date shape."""
    if _ISO.match(text):
        return "iso"
    numeric = _NUMERIC_PARTS.match(text)
    if numeric:
        return f"numeric{numeric.group(2)}"
    if _DAY_MONTH_NAME.match(text):
        return "day-monthname"
    if _MONTH_NAME_DAY.match(text):
        return "monthname-day"
    return None


def _examples(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))[:_MAX_EXAMPLES]


def _numeric_order(texts: list[str], separator: str, forced: str | None) -> tuple[str, str]:
    """Decide month-first (``MDY``) or day-first (``DMY``) from the values themselves."""
    firsts = [int(m.group(1)) for t in texts if (m := _NUMERIC_PARTS.match(t))]
    seconds = [int(m.group(3)) for t in texts if (m := _NUMERIC_PARTS.match(t))]
    day_first = max(firsts) > 12
    month_first = max(seconds) > 12
    if forced:
        return forced, f"given as {forced}"
    if day_first and month_first:
        raise _fail(
            f"The dates use '{separator}' with a value above 12 in both the first and the "
            "second position, so they are not one consistent day/month order.",
            "Filter the stray rows out first or convert the column with "
            "'view transform convert-type'.",
            {"examples": _examples(texts)},
        )
    if day_first:
        return "DMY", f"a value has {max(firsts)} in the first position (a day)"
    if month_first:
        return "MDY", f"a value has {max(seconds)} in the second position (a day)"
    raise _fail(
        f"The dates are day/month ambiguous: every value has 12 or less in both the first and "
        f"the second position (for example {_examples(texts)[0]!r}), so M/D/YYYY and D/M/YYYY "
        "read the same data differently.",
        'State the order with "text_date_format": "M/D/YYYY" or "D/M/YYYY" in --input.',
        {"examples": _examples(texts)},
    )


def _forced_order(requested: str | None) -> str | None:
    if requested is None:
        return None
    normal = re.sub(r"[^A-Za-z]", "", requested).upper()
    if normal in ("MDYYYY", "MMDDYYYY", "MDY"):
        return "MDY"
    if normal in ("DMYYYY", "DDMMYYYY", "DMY"):
        return "DMY"
    raise _fail(
        f"text_date_format {requested!r} is not supported.",
        'Use "M/D/YYYY" or "D/M/YYYY"; other layouts are detected from the data.',
    )


def detect_format(
    values: Iterable[Any], column: str, requested: str | None = None
) -> TextDateFormat:
    """Detect the one date format the stored strings share, or fail loud.

    ``values`` are the column's distinct stored values (blanks ignored). Raises
    when there is nothing to read, when a value is not a date, when the values mix
    layouts, or when day/month order cannot be told apart and ``requested`` does
    not settle it.
    """
    texts = [_text(v) for v in values if not _blank(v)]
    if not texts:
        raise _fail(f"Column '{column}' has no non-blank values to read as dates.", "")
    shapes = {text: _shape_of(text) for text in texts}
    unknown = [t for t, s in shapes.items() if s is None]
    if unknown:
        raise _fail(
            f"Column '{column}' is TEXT and {len(unknown)} of {len(texts)} distinct values are not "
            f"dates I can read (for example {_examples(unknown)!r}).",
            "Filter those rows out with a condition, or convert the column with "
            "'view transform convert-type' (a pipeline write).",
            {"unparseable_examples": _examples(unknown), "unparseable_count": len(unknown)},
        )
    kinds = set(shapes.values())
    if len(kinds) > 1:
        raise _fail(
            f"Column '{column}' mixes date layouts: {sorted(str(k) for k in kinds)}.",
            "Filter to one layout first or convert the column with 'view transform convert-type'.",
            {"examples": _examples(texts)},
        )
    return _format_for(kinds.pop() or "", texts, requested)


def _format_for(shape: str, texts: list[str], requested: str | None) -> TextDateFormat:
    if shape == "iso":
        return TextDateFormat("YYYY-MM-DD", shape, "YMD", "every value is year-first ISO")
    if shape == "day-monthname":
        return TextDateFormat("D-Mon-YYYY", shape, "DMY", "the month is spelled out")
    if shape == "monthname-day":
        return TextDateFormat("Mon D, YYYY", shape, "MDY", "the month is spelled out")
    separator = shape[-1]
    order, reason = _numeric_order(texts, separator, _forced_order(requested))
    label = f"M{separator}D{separator}YYYY" if order == "MDY" else f"D{separator}M{separator}YYYY"
    return TextDateFormat(label, shape, order, reason)


def _month_number(name: str) -> int:
    key = name.lower()[:3]
    if key not in _MONTHS:
        raise ValueError(f"unknown month name {name!r}")
    return _MONTHS[key]


def _ymd(text: str, fmt: TextDateFormat) -> tuple[int, int, int]:
    if fmt.shape == "iso":
        m = _ISO.match(text)
        assert m is not None
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    if fmt.shape == "day-monthname":
        m = _DAY_MONTH_NAME.match(text)
        assert m is not None
        return int(m.group(3)), _month_number(m.group(2)), int(m.group(1))
    if fmt.shape == "monthname-day":
        m = _MONTH_NAME_DAY.match(text)
        assert m is not None
        return int(m.group(3)), _month_number(m.group(1)), int(m.group(2))
    m = _NUMERIC_PARTS.match(text)
    assert m is not None
    first, second, year = int(m.group(1)), int(m.group(3)), int(m.group(4))
    return (year, first, second) if fmt.order == "MDY" else (year, second, first)


def parse_value(text: Any, fmt: TextDateFormat) -> date | None:
    """Parse one stored string in ``fmt``; ``None`` for a blank, an error for a bad date."""
    if _blank(text):
        return None
    cleaned = _text(text)
    try:
        return date(*_ymd(cleaned, fmt))
    except (ValueError, AssertionError) as exc:
        raise _fail(
            f"'{cleaned}' is not a valid date in the detected format {fmt.label}.",
            'If the order is wrong, state it with "text_date_format" in --input.',
            {"value": cleaned, "format": fmt.label},
        ) from exc


def raw_key(value: Any) -> str:
    """The dictionary key a stored value is filed under (blank/None -> empty string)."""
    return "" if value is None else (value if isinstance(value, str) else _text(value))


def parse_all(values: Iterable[Any], fmt: TextDateFormat) -> dict[str, date | None]:
    """Map every distinct stored value to its date (validates them all)."""
    return {raw_key(value): parse_value(value, fmt) for value in values}


def require_level(level: Any) -> str:
    """Return a supported bucket level, or fail loud."""
    name = str(level or "").upper()
    if name not in LEVELS:
        raise _fail(
            f"A TEXT date column can be bucketed by {', '.join(LEVELS)}; got {level!r}.",
            "AUTO and sub-day levels need a real DATE column ('view transform convert-type').",
        )
    return name


def bucket_start(day: date, level: str) -> date:
    """First day of the ``level`` period containing ``day``."""
    if level == "DAY":
        return day
    if level == "WEEK":
        return day - timedelta(days=day.weekday())
    if level == "MONTH":
        return day.replace(day=1)
    if level == "QUARTER":
        return date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)
    if level == "YEAR":
        return date(day.year, 1, 1)
    return date(day.year - day.year % 10, 1, 1)


def _merge(function: str, current: Any, new: Any) -> Any:
    if current is None:
        return new
    if new is None:
        return current
    if function == "MIN":
        return min(current, new)
    if function == "MAX":
        return max(current, new)
    return current + new


def rebucket(
    rows: list[dict[str, Any]],
    *,
    date_key: str,
    other_keys: list[str],
    functions: dict[str, str],
    days: dict[str, date | None],
    level: str,
) -> list[dict[str, Any]]:
    """Regroup per-stored-value rows into ``level`` buckets.

    ``functions`` maps each aggregate result key to SUM/COUNT/MIN/MAX. Each output
    row carries the bucket as its period start (ISO date, or ``None`` for blank).
    """
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        day = days.get(raw_key(row.get(date_key)))
        bucket = bucket_start(day, level).isoformat() if day is not None else None
        key = (bucket, *(row.get(k) for k in other_keys))
        target = merged.setdefault(key, {date_key: bucket, **{k: row.get(k) for k in other_keys}})
        for result_key, function in functions.items():
            target[result_key] = _merge(function, target.get(result_key), row.get(result_key))
    return list(merged.values())


def in_range_values(days: dict[str, date | None], test: Callable[[date], bool]) -> list[str]:
    """The stored strings whose parsed date satisfies ``test`` (blanks never do)."""
    return [raw for raw, day in days.items() if day is not None and test(day)]


def observed_range(days: dict[str, date | None]) -> dict[str, str] | None:
    """Earliest and latest parsed date, or ``None`` when the column has none."""
    real = [d for d in days.values() if d is not None]
    if not real:
        return None
    return {"min": min(real).isoformat(), "max": max(real).isoformat()}
