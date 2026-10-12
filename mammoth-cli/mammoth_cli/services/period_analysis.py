"""Calendar periods and measure checks shared by ``view data drivers`` and ``forecast``.

Both commands read a measure per date bucket through ``view data aggregate``'s own
helpers (:func:`mammoth_cli.commands.view.aggregate_on`) and then reason about the
buckets as calendar periods: which period a bucket belongs to, where a period ends,
and whether the data's date coverage reaches that end. That calendar arithmetic and
the input checks the two commands share live here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    CODE_MISSING_FIELD,
    EXIT_USAGE,
    CliError,
)

#: Units a period can be bucketed by, coarsest first (the aggregate ``truncate`` names).
UNITS_COARSEST_FIRST = ("YEAR", "QUARTER", "MONTH", "DAY")

#: The aggregate functions ``view data aggregate`` accepts.
AGGREGATE_FUNCTIONS = ("SUM", "COUNT", "AVG", "MIN", "MAX", "STDDEV", "DISTINCT_COUNT")

_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_QUARTER = re.compile(r"^(\d{4})-[Qq]([1-4])$")
_YEAR = re.compile(r"^(\d{4})$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PERIOD_FORMS = (
    "'YYYY-MM' (a month), 'YYYY-Qn' (a quarter), 'YYYY' (a year) or "
    '{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"} (both days included)'
)
_LABEL_CHARS = 60


@dataclass(frozen=True)
class Period:
    """A calendar period, both ends included."""

    label: str
    start: date
    end: date

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end


def usage(message: str, hint: str | None = None, **details: Any) -> CliError:
    """An ``invalid_arguments`` usage error."""
    return CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=message,
        exit_status=EXIT_USAGE,
        hint=hint,
        details=details,
    )


def _month_end(year: int, month: int) -> date:
    first_next = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return first_next - timedelta(days=1)


def month(year: int, number: int) -> Period:
    return Period(f"{year:04d}-{number:02d}", date(year, number, 1), _month_end(year, number))


def quarter(year: int, number: int) -> Period:
    first = 3 * (number - 1) + 1
    return Period(f"{year:04d}-Q{number}", date(year, first, 1), _month_end(year, first + 2))


def week(start: date) -> Period:
    """The seven days from ``start`` (a WEEK bucket's first day, as the data gives it)."""
    return Period(f"week of {start.isoformat()}", start, start + timedelta(days=6))


def _day(raw: Any, field: str) -> date:
    if not isinstance(raw, str) or not _DAY.match(raw):
        raise usage(
            f"Period '{field}' must be a date as YYYY-MM-DD, got {raw!r}.",
            hint=f"A period is {_PERIOD_FORMS}.",
        )
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise usage(f"Period '{field}' {raw!r} is not a calendar date.") from exc


def parse_period(raw: Any) -> Period:
    """One ``compare`` entry as a calendar period; anything else fails loud."""
    if isinstance(raw, dict):
        if set(raw) != {"from", "to"}:
            raise usage(
                f"A period object takes exactly 'from' and 'to', got {sorted(raw)}.",
                hint=f"A period is {_PERIOD_FORMS}.",
            )
        start, end = _day(raw["from"], "from"), _day(raw["to"], "to")
        if end < start:
            raise usage(f"Period 'to' {raw['to']} is before 'from' {raw['from']}.")
        return Period(f"{start.isoformat()}..{end.isoformat()}", start, end)
    text = raw.strip() if isinstance(raw, str) else None
    if text and (found := _MONTH.match(text)):
        number = int(found.group(2))
        if 1 <= number <= 12:
            return month(int(found.group(1)), number)
    if text and (found := _QUARTER.match(text)):
        return quarter(int(found.group(1)), int(found.group(2)))
    if text and _YEAR.match(text):
        year = int(text)
        return Period(text, date(year, 1, 1), date(year, 12, 31))
    raise usage(f"{raw!r} is not a period.", hint=f"A period is {_PERIOD_FORMS}.")


def _starts_unit(day: date, unit: str) -> bool:
    if unit == "YEAR":
        return (day.month, day.day) == (1, 1)
    if unit == "QUARTER":
        return day.day == 1 and day.month in (1, 4, 7, 10)
    if unit == "MONTH":
        return day.day == 1
    return True


def coarsest_unit(periods: list[Period]) -> str:
    """The coarsest date bucket whose buckets each fall wholly inside or outside every period."""
    for unit in UNITS_COARSEST_FIRST:
        if all(
            _starts_unit(p.start, unit) and _starts_unit(p.end + timedelta(days=1), unit)
            for p in periods
        ):
            return unit
    return "DAY"


def as_date(value: Any) -> date | None:
    """A date bucket or coverage value as a date; None for a blank. Unreadable fails loud."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise usage(f"The date value {value!r} in the result could not be read as a date.") from exc


def number(value: Any) -> float:
    """An aggregate cell as a float; a blank (no rows) is 0."""
    if value is None or value == "":
        return 0.0
    if isinstance(value, bool):
        raise usage(f"Expected a number in the result, got {value!r}.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise usage(f"Expected a number in the result, got {value!r}.") from exc


def group_label(value: Any) -> Any:
    """A group value as the agent should quote it: blanks named, long text cut."""
    if value is None or value == "":
        return "(blank)"
    if isinstance(value, str) and len(value) > _LABEL_CHARS:
        return value[:_LABEL_CHARS] + "…"
    return value


@dataclass(frozen=True)
class Measure:
    """The ``measure`` input: what is summed or counted per period."""

    column: str | None
    function: str
    label: str

    def aggregation(self) -> dict[str, Any]:
        item: dict[str, Any] = {"function": self.function, "as_name": self.label}
        if self.column:
            item["column"] = self.column
        return item


def parse_measure(raw: Any, allowed: tuple[str, ...]) -> Measure:
    """``{"column": C, "function": F}`` (``as_name`` optional) with F one of ``allowed``."""
    if not isinstance(raw, dict):
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="'measure' is required: an object with 'column' and 'function'.",
            exit_status=EXIT_USAGE,
            hint='"measure": {"column": "revenue", "function": "SUM"}',
        )
    function = str(raw.get("function") or "").upper()
    if function not in allowed:
        raise usage(
            f"measure function {raw.get('function')!r} is not one of {', '.join(allowed)}.",
        )
    column = raw.get("column")
    if column is not None and not isinstance(column, str):
        raise usage("measure 'column' must be a column name.")
    if not column and function != "COUNT":
        raise usage(f"measure function {function} needs a 'column'.")
    label = raw.get("as_name") or (f"{function}_{column}" if column else function)
    return Measure(column or None, function, str(label))


def require_text(document: dict[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"'{field}' is required: a column name.",
            exit_status=EXIT_USAGE,
        )
    return value


def optional_condition(document: dict[str, Any]) -> dict[str, Any] | None:
    conditions = document.get("conditions")
    if conditions is not None and not isinstance(conditions, dict):
        raise usage("'conditions' must be one condition object, as view data aggregate takes.")
    return conditions


def require_columns(column_types: dict[str, str], date_column: str, *columns: str | None) -> None:
    """Every named column exists in the view, and ``date_column`` holds dates."""
    known = sorted(column_types)
    for column in (date_column, *columns):
        if column and column not in column_types:
            raise usage(
                f"The view has no column {column!r}.",
                hint="Column names are case-sensitive; `view get VIEW_ID` lists them.",
                columns=known[:40],
            )
    if column_types.get(date_column) not in ("DATE", "TEXT"):
        raise usage(
            f"date_column {date_column!r} is {column_types.get(date_column)}, not a date.",
            hint="Pass the DATE column (or a TEXT column of dates) the periods are read from.",
        )


def range_condition(column: str, period: Period) -> dict[str, Any]:
    """Rows dated within ``period``: from its first day up to, not including, the day after."""
    return {
        "and": [
            {"column": column, "operator": "GTE", "value": period.start.isoformat()},
            {
                "column": column,
                "operator": "LT",
                "value": (period.end + timedelta(days=1)).isoformat(),
            },
        ]
    }


def with_condition(base: dict[str, Any] | None, extra: dict[str, Any] | None) -> dict[str, Any]:
    """A document fragment carrying ``base`` and ``extra`` AND-ed (either may be None)."""
    parts = [c for c in (base, extra) if c]
    if not parts:
        return {}
    return {"condition": parts[0] if len(parts) == 1 else {"and": parts}}


def coverage_dates(data: Any) -> tuple[date | None, date | None]:
    """The first and last day of the data, from an aggregate's ``coverage``."""
    coverage = data.get("coverage") if isinstance(data, dict) else None
    if not isinstance(coverage, dict):
        return None, None
    return as_date(coverage.get("min")), as_date(coverage.get("max"))


def rows(data: Any) -> list[dict[str, Any]]:
    found = data.get("data") if isinstance(data, dict) else None
    return [row for row in found or [] if isinstance(row, dict)]


def money(data: Any) -> dict[str, Any]:
    """``currency`` and ``currency_note`` exactly as the aggregate gave them."""
    if not isinstance(data, dict):
        return {}
    return {key: data[key] for key in ("currency", "currency_note") if key in data}


def r2(value: float) -> float:
    return round(value, 2)
