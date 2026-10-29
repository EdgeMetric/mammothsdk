"""``view data forecast``: the next periods of a measure, with a 95% range.

Read-only. Asked for October's store revenue with data ending mid-September, the
in-product agent divided September's partial total by its days (gap eval 10-10,
S20). This reads the measure per month, quarter or week in one aggregate (through
``view data aggregate``'s own helpers, so names, TEXT dates, coverage and currency
behave the same), leaves a period the data does not cover to its end out of the
fit -- never scaling it up -- and fits an ordinary least-squares linear trend to
the complete periods. With two full cycles of history (24 months, 8 quarters, 104
weeks) it adds an additive seasonal index; otherwise it says it did not. The range
is a t-based 95% prediction interval from the fit's residuals.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view._common import _require_int_positional_at
from mammoth_cli.commands.view.aggregate import aggregate_on, open_aggregate_source
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services import period_analysis as pa
from mammoth_cli.services.listing import LIST_DATA_BUDGET, json_size
from mammoth_cli.services.read_queries import AGGREGATE_SYMBOL

#: Periods in one seasonal cycle, per unit; seasonality needs two full cycles.
_CYCLE = {"MONTH": 12, "QUARTER": 4, "WEEK": 52}
_MIN_COMPLETE = 3
_MAX_PERIODS = 12
_EPOCH_MONDAY = date(1970, 1, 5)
#: Two-sided 95% Student t quantiles (0.975) by degrees of freedom.
_T975 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
    40: 2.021,
    60: 2.000,
    120: 1.980,
}
_Z975 = 1.960

_NOTE = (
    "Give each forecast period's estimate with its 95% range (low to high), name the method "
    "(a linear trend over the complete periods in history, seasonal only when 'seasonal' is "
    "true) and say it is a projection from past periods, never a certainty. If "
    "excluded_partial is present, say that period is incomplete in the data (through "
    "data_through), quote its value as the amount so far, and say it was left out of the fit, "
    "not scaled up. Give amounts in the currency named in 'currency'; when it is null, give "
    "plain numbers and never invent a currency."
)


def view_data_forecast(invocation: Invocation) -> HandlerResult:
    """Forecast a measure's next months, quarters or weeks: linear trend with a 95% range."""
    require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    measure = pa.parse_measure(document.get("measure"), pa.AGGREGATE_FUNCTIONS)
    date_column = pa.require_text(document, "date_column")
    unit = _unit(document.get("unit", "month"))
    horizon = _horizon(document.get("periods", 1))
    conditions = pa.optional_condition(document)
    with open_service(invocation) as (service, auth):
        source = open_aggregate_source(service, invocation, auth.workspace_id, view_id, document)
        pa.require_columns(source.reads.column_types, date_column, measure.column)
        data = aggregate_on(
            source,
            AGGREGATE_SYMBOL,
            {
                "group_by": [{"column": date_column, "truncate": unit}],
                "aggregations": [measure.aggregation()],
                **pa.with_condition(conditions, None),
            },
        )
    return _forecast(data, measure, date_column, unit, horizon), source.meta


def _unit(raw: Any) -> str:
    unit = str(raw or "").upper()
    if unit not in _CYCLE:
        raise pa.usage(f"'unit' {raw!r} is not one of month, quarter or week.")
    return unit


def _horizon(raw: Any) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= _MAX_PERIODS:
        raise pa.usage(f"'periods' takes a whole number from 1 to {_MAX_PERIODS}, got {raw!r}.")
    return raw


def _period(unit: str, start: date) -> pa.Period:
    """The month, quarter or week a date bucket starts."""
    if unit == "MONTH":
        return pa.month(start.year, start.month)
    if unit == "QUARTER":
        return pa.quarter(start.year, (start.month - 1) // 3 + 1)
    return pa.week(start)


def _next(unit: str, period: pa.Period) -> pa.Period:
    return _period(unit, period.end + timedelta(days=1))


def _x(unit: str, period: pa.Period) -> int:
    """The period's position on one evenly spaced axis (a gap in the data stays a gap)."""
    if unit == "MONTH":
        return period.start.year * 12 + period.start.month - 1
    if unit == "QUARTER":
        return period.start.year * 4 + (period.start.month - 1) // 3
    return (period.start - _EPOCH_MONDAY).days // 7


def _t975(dof: int) -> float:
    """The 0.975 Student t quantile, interpolated in 1/dof between table rows."""
    if dof in _T975:
        return _T975[dof]
    rows = sorted(_T975)
    upper = next((d for d in rows if d > dof), None)
    if upper is None:
        low_d, low_t = rows[-1], _T975[rows[-1]]
        weight = (1 / dof) / (1 / low_d)
        return _Z975 + (low_t - _Z975) * weight
    lower = max(d for d in rows if d < dof)
    weight = (1 / dof - 1 / upper) / (1 / lower - 1 / upper)
    return _T975[upper] + (_T975[lower] - _T975[upper]) * weight


def _series(
    data: Any, measure: pa.Measure, date_column: str, unit: str
) -> list[tuple[pa.Period, float]]:
    found: dict[date, tuple[pa.Period, float]] = {}
    for row in pa.rows(data):
        day = pa.as_date(row.get(date_column))
        if day is None:
            continue
        period = _period(unit, day)
        value = pa.number(row.get(measure.label))
        previous = found.get(period.start, (period, 0.0))[1]
        found[period.start] = (period, previous + value)
    return [found[start] for start in sorted(found)]


class _Fit:
    """An OLS line through (x, y), with an additive seasonal index when asked."""

    def __init__(self, xs: list[int], ys: list[float], cycle: int | None) -> None:
        n = len(xs)
        self.n = n
        self.x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        self.sxx = sum((x - self.x_mean) ** 2 for x in xs)
        sxy = sum((x - self.x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
        self.slope = sxy / self.sxx
        self.intercept = y_mean - self.slope * self.x_mean
        residuals = [y - self._line(x) for x, y in zip(xs, ys, strict=True)]
        self.cycle = cycle
        self.season: dict[int, float] = {}
        dof = n - 2
        if cycle:
            by_season: dict[int, list[float]] = {}
            for x, e in zip(xs, residuals, strict=True):
                by_season.setdefault(x % cycle, []).append(e)
            means = {k: sum(v) / len(v) for k, v in by_season.items()}
            centre = sum(means.values()) / len(means)
            self.season = {k: m - centre for k, m in means.items()}
            residuals = [e - self.season[x % cycle] for x, e in zip(xs, residuals, strict=True)]
            dof -= len(self.season) - 1
        self.dof = dof
        self.sigma = math.sqrt(sum(e * e for e in residuals) / dof)

    def _line(self, x: float) -> float:
        return self.intercept + self.slope * x

    def predict(self, x: int) -> tuple[float, float]:
        """The estimate at ``x`` and the half-width of its 95% prediction interval."""
        seasonal = self.season.get(x % self.cycle, 0.0) if self.cycle else 0.0
        spread = math.sqrt(1 + 1 / self.n + (x - self.x_mean) ** 2 / self.sxx)
        return self._line(x) + seasonal, _t975(self.dof) * self.sigma * spread


def _forecast(
    data: Any, measure: pa.Measure, date_column: str, unit: str, horizon: int
) -> dict[str, Any]:
    series = _series(data, measure, date_column, unit)
    first_day, last_day = pa.coverage_dates(data)
    word = unit.lower()
    partial_end = None
    if series and last_day is not None and last_day < series[-1][0].end:
        partial_end = series.pop()
    partial_start = None
    if series and first_day is not None and first_day > series[0][0].start:
        partial_start = series.pop(0)
    if len(series) < _MIN_COMPLETE:
        raise pa.usage(
            f"A forecast needs at least {_MIN_COMPLETE} complete {word}s of history; the data "
            f"has {len(series)}.",
            hint=f"Use a finer unit (quarter -> month -> week) or quote the {word}s there are.",
            complete_periods=[p.label for p, _ in series],
        )
    xs = [_x(unit, p) for p, _ in series]
    ys = [v for _, v in series]
    cycle = _CYCLE[unit]
    seasonal = len(series) >= 2 * cycle
    fit = _Fit(xs, ys, cycle if seasonal else None)
    floor = all(y >= 0 for y in ys)
    start = partial_end[0] if partial_end else _next(unit, series[-1][0])
    forecast = []
    period = start
    for _ in range(horizon):
        estimate, half = fit.predict(_x(unit, period))
        low = estimate - half
        forecast.append(
            {
                "period": period.label,
                "estimate": pa.r2(estimate),
                "low": pa.r2(max(low, 0.0) if floor else low),
                "high": pa.r2(estimate + half),
            }
        )
        period = _next(unit, period)
    method = (
        f"Ordinary least-squares linear trend over {len(series)} complete {word}s"
        + (f", plus an additive seasonal index per {word} of the year" if seasonal else "")
        + f"; 95% prediction interval, t-based (t 0.975 with {fit.dof} degrees of freedom): "
        "estimate +/- t * s * sqrt(1 + 1/n + (x - mean x)^2 / Sxx), s from the residuals"
        + ("; low floored at 0 as the history is never negative" if floor else "")
        + "."
    )
    result: dict[str, Any] = {
        "measure": measure.label,
        "date_column": date_column,
        "unit": word,
        "forecast": forecast,
        "method": method,
        "seasonal": seasonal,
        "fit": {
            "periods_used": len(series),
            "from": series[0][0].label,
            "to": series[-1][0].label,
            f"trend_per_{word}": pa.r2(fit.slope),
        },
    }
    if not seasonal:
        result["seasonal_note"] = (
            f"No seasonal adjustment: it needs {2 * cycle} complete {word}s (two full "
            f"cycles); the history has {len(series)}."
        )
    if partial_end:
        period_, value = partial_end
        result["excluded_partial"] = {
            "period": period_.label,
            "value": pa.r2(value),
            "data_through": last_day.isoformat() if last_day else None,
            "period_ends": period_.end.isoformat(),
        }
    if partial_start:
        period_, value = partial_start
        result["excluded_partial_start"] = {
            "period": period_.label,
            "value": pa.r2(value),
            "data_from": first_day.isoformat() if first_day else None,
        }
    for key in ("coverage", "text_dates"):
        if isinstance(data, dict) and key in data:
            result[key] = data[key]
    result.update(pa.money(data))
    note = _note(forecast, partial_end, last_day)
    history = [{"period": p.label, "value": pa.r2(v)} for p, v in series]
    room = LIST_DATA_BUDGET - json_size(result) - len(note) - 80
    kept: list[dict[str, Any]] = []
    for item in reversed(history):
        if json_size(kept) + json_size(item) + 1 > room and kept:
            break
        kept.insert(0, item)
    result["history"] = kept
    if len(kept) < len(history):
        result["history_omitted"] = len(history) - len(kept)
    result["note"] = note
    return result


def _note(
    forecast: list[dict[str, Any]],
    partial_end: tuple[pa.Period, float] | None,
    last_day: date | None,
) -> str:
    covers = forecast[0]["period"] + (f" to {forecast[-1]['period']}" if len(forecast) > 1 else "")
    extra = [f"The forecast covers {covers}."]
    if partial_end and last_day:
        extra.append(
            f"Its first period, {partial_end[0].label}, is the partial one: the data ends "
            f"{last_day.isoformat()}, so the estimate is for the whole {partial_end[0].label}. "
            "If the user asked for a later period, run again with a larger 'periods' and quote "
            "that period."
        )
    else:
        extra.append(
            "If the user asked for a later period, run again with a larger 'periods' and quote "
            "that period."
        )
    return " ".join([_NOTE, *extra])
