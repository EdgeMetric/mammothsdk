"""``view data forecast``: a measure's next periods from a linear trend, with a 95% range."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_forecast
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(tmp_path: Path, **payload: Any) -> Invocation:
    document = {
        "measure": {"column": "revenue", "function": "SUM"},
        "date_column": "sale_date",
        "unit": "month",
        "periods": 1,
        **payload,
    }
    path = tmp_path / "in.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return Invocation(
        command_id="view.data.forecast", project=180, extra_args=["7", "9"], input_file=str(path)
    )


def _months(count: int, first_year: int = 2026) -> list[str]:
    return [f"{first_year + i // 12}-{i % 12 + 1:02d}-01" for i in range(count)]


def _program(
    fake: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
    series: list[tuple[str, float]],
    data_ends: str,
) -> None:
    """A monthly revenue series, and the date coverage the aggregate's range read returns."""
    fake.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": "column_1", "display_name": "revenue", "type": "NUMERIC"},
            {"internal_name": "column_2", "display_name": "sale_date", "type": "DATE"},
        ]
    }
    record = fake.call

    def call(symbol: str, /, **kwargs: Any) -> Any:
        record(symbol, **kwargs)
        if symbol != _AGGREGATE:
            return fake.responses.get(symbol, {})
        if kwargs.get("group_by"):
            return {"data": [{"group_0": day, "agg_0": value} for day, value in series]}
        return {"data": [{"agg_0": series[0][0], "agg_1": data_ends}]}

    monkeypatch.setattr(fake, "call", call)


def test_a_linear_series_forecasts_the_next_point_inside_its_range(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # 100,000 rising 5,000 a month, Jan-Aug 2026, each month off the line by +/-300.
    series = [
        (day, 100000.0 + 5000 * i + (300 if i % 2 else -300)) for i, day in enumerate(_months(8))
    ]
    _program(fake_service, monkeypatch, series, data_ends="2026-08-31")
    result, meta = view_forecast.view_data_forecast(_inv(tmp_path, periods=2))

    (grouped,) = [kw for s, kw in fake_service.call_log if s == _AGGREGATE and kw.get("group_by")]
    assert grouped["group_by"] == [{"column": "column_2", "truncate": "MONTH"}]
    september, october = result["forecast"]
    assert [september["period"], october["period"]] == ["2026-09", "2026-10"]
    assert abs(september["estimate"] - 140000) < 500
    assert september["low"] < 140000 < september["high"]
    assert october["high"] - october["low"] > september["high"] - september["low"]
    assert result["seasonal"] is False
    assert "excluded_partial" not in result
    assert "t-based" in result["method"] and "least-squares" in result["method"]
    assert result["fit"]["periods_used"] == 8 and result["fit"]["trend_per_month"] > 4900
    assert [h["period"] for h in result["history"]][-1] == "2026-08"
    assert result["currency"] == {"SUM_revenue": None}
    assert "never a certainty" in result["note"] and "never invent" in result["note"]
    assert meta["project_id"] == 180


def test_an_exact_line_is_forecast_exactly(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    series = [(day, 1000.0 + 250 * i) for i, day in enumerate(_months(6))]
    _program(fake_service, monkeypatch, series, data_ends="2026-06-30")
    result, _ = view_forecast.view_data_forecast(_inv(tmp_path))
    assert result["forecast"] == [
        {"period": "2026-07", "estimate": 2500.0, "low": 2500.0, "high": 2500.0}
    ]


def test_a_partial_last_month_is_left_out_and_forecast_first(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """S20: data ends 16 Sep, the question is October."""
    series = [(day, 100000.0 + 5000 * i) for i, day in enumerate(_months(8))]
    series.append(("2026-09-01", 70000.0))
    _program(fake_service, monkeypatch, series, data_ends="2026-09-16")
    result, _ = view_forecast.view_data_forecast(_inv(tmp_path, periods=2))

    assert result["excluded_partial"] == {
        "period": "2026-09",
        "value": 70000.0,
        "data_through": "2026-09-16",
        "period_ends": "2026-09-30",
    }
    # Never scaled up by days: the fit ignores September, so its estimate is the line's.
    assert [f["period"] for f in result["forecast"]] == ["2026-09", "2026-10"]
    assert [f["estimate"] for f in result["forecast"]] == [140000.0, 145000.0]
    assert result["fit"]["to"] == "2026-08"
    assert "2026-09" not in [h["period"] for h in result["history"]]
    assert "Its first period, 2026-09, is the partial one" in result["note"]
    assert "larger 'periods'" in result["note"]


def test_fewer_than_three_complete_periods_is_refused(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    series = [("2026-07-01", 10.0), ("2026-08-01", 12.0), ("2026-09-01", 5.0)]
    _program(fake_service, monkeypatch, series, data_ends="2026-09-16")
    with pytest.raises(CliError) as excinfo:
        view_forecast.view_data_forecast(_inv(tmp_path))
    assert excinfo.value.code == "invalid_arguments"
    assert "at least 3 complete months" in excinfo.value.message
    assert excinfo.value.details["complete_periods"] == ["2026-07", "2026-08"]


def test_no_seasonal_adjustment_under_two_cycles(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    series = [(day, 500.0 + (400 if day[5:7] == "12" else 0)) for day in _months(23, 2024)]
    _program(fake_service, monkeypatch, series, data_ends="2025-11-30")
    result, _ = view_forecast.view_data_forecast(_inv(tmp_path))
    assert result["seasonal"] is False
    assert "needs 24 complete months" in result["seasonal_note"]
    assert "seasonal index" not in result["method"]


def test_two_full_cycles_add_a_seasonal_index(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Flat 500 a month with a December peak of +400, Jan 2024 - Nov 2026 (35 months).
    series = [(day, 500.0 + (400 if day[5:7] == "12" else 0)) for day in _months(35, 2024)]
    _program(fake_service, monkeypatch, series, data_ends="2026-11-30")
    result, _ = view_forecast.view_data_forecast(_inv(tmp_path, periods=2))
    assert result["seasonal"] is True
    assert "seasonal_note" not in result
    december, january = result["forecast"]
    assert december["period"] == "2026-12" and january["period"] == "2027-01"
    assert december["estimate"] - january["estimate"] > 300


@pytest.mark.parametrize(
    "payload",
    [{"unit": "day"}, {"periods": 0}, {"periods": 13}, {"measure": {"column": "revenue"}}],
)
def test_bad_input_is_refused_before_any_read(
    fake_service: FakeMammothService, tmp_path: Path, payload: dict[str, Any]
) -> None:
    with pytest.raises(CliError) as excinfo:
        view_forecast.view_data_forecast(_inv(tmp_path, **payload))
    # 'unit' is an enum in the contract, refused at admission; the rest by the handler.
    assert excinfo.value.code in {"invalid_arguments", "invalid_input_field_type"}
    assert fake_service.call_log == []
