"""``view data drivers``: a measure's change between two periods and what drove it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_drivers
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"

_COLUMNS = {
    "column_1": ("store", "TEXT"),
    "column_2": ("category", "TEXT"),
    "column_3": ("revenue", "NUMERIC"),
    "column_4": ("sale_date", "DATE"),
}

# S03 (gap eval 10-10): store revenue 301,984.11 in July 2026, 171,253.76 in August,
# from 22 sales then 14. Per (group, month): (revenue, sales).
_BY_STORE = {
    ("Pune", "2026-07-01"): (150000.00, 10),
    ("Pune", "2026-08-01"): (60000.00, 5),
    ("Mumbai", "2026-07-01"): (100000.00, 8),
    ("Mumbai", "2026-08-01"): (80000.00, 6),
    ("Delhi", "2026-07-01"): (51984.11, 4),
    ("Delhi", "2026-08-01"): (31253.76, 3),
}
_BY_CATEGORY = {
    ("Electronics", "2026-07-01"): (201984.11, 12),
    ("Electronics", "2026-08-01"): (101253.76, 7),
    ("Grocery", "2026-07-01"): (100000.00, 10),
    ("Grocery", "2026-08-01"): (70000.00, 7),
}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _inv(**overrides: object) -> Invocation:
    return Invocation(command_id="view.data.drivers", **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, Any]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


def _input(**overrides: Any) -> dict[str, Any]:
    return {
        "measure": {"column": "revenue", "function": "SUM"},
        "date_column": "sale_date",
        "compare": ["2026-07", "2026-08"],
        "by": ["store", "category"],
        **overrides,
    }


def _rows(table: dict[tuple[str, str], tuple[float, int]]) -> list[dict[str, Any]]:
    return [
        {"group_0": group, "group_1": month, "agg_0": value, "agg_1": count}
        for (group, month), (value, count) in table.items()
    ]


def _program(
    fake: FakeMammothService,
    monkeypatch: pytest.MonkeyPatch,
    data_ends: str = "2026-09-16",
    by_store: dict[tuple[str, str], tuple[float, int]] | None = None,
) -> None:
    """Answer each aggregate like the backend: by its first group column, or the date range."""
    fake.responses[_DATAVIEW_GET] = {
        "metadata": [
            {"internal_name": internal, "display_name": name, "type": kind}
            for internal, (name, kind) in _COLUMNS.items()
        ]
    }
    tables = {"column_1": by_store or _BY_STORE, "column_2": _BY_CATEGORY}
    record = fake.call

    def call(symbol: str, /, **kwargs: Any) -> Any:
        record(symbol, **kwargs)
        if symbol != _AGGREGATE:
            return fake.responses.get(symbol, {})
        group_by = kwargs.get("group_by")
        if group_by:
            return {"data": _rows(tables[group_by[0]])}
        return {"data": [{"agg_0": "2026-01-01", "agg_1": data_ends}]}

    monkeypatch.setattr(fake, "call", call)


def _grouped_calls(fake: FakeMammothService) -> list[dict[str, Any]]:
    return [kw for symbol, kw in fake.call_log if symbol == _AGGREGATE and kw.get("group_by")]


def test_drivers_totals_and_ranked_contributors(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _program(fake_service, monkeypatch)
    result, meta = view_drivers.view_data_drivers(
        _inv(project=180, extra_args=["7", "9"], input_file=_doc(tmp_path, _input()))
    )

    # One aggregate per 'by' column, never one per period, each bucketed by month.
    grouped = _grouped_calls(fake_service)
    assert [kw["group_by"] for kw in grouped] == [
        ["column_1", {"column": "column_4", "truncate": "MONTH"}],
        ["column_2", {"column": "column_4", "truncate": "MONTH"}],
    ]
    assert all(kw["condition"] is not None for kw in grouped)
    assert [a["as_name"] for a in grouped[0]["aggregations"]] == ["SUM_revenue", "__rows"]

    assert result["totals"] == {
        "a": {"value": 301984.11, "count": 22},
        "b": {"value": 171253.76, "count": 14},
        "delta": -130730.35,
        "delta_pct": -43.3,
        "count_delta": -8,
        "count_delta_pct": -36.4,
    }
    stores = result["contributors"]["store"]
    assert [c["group"] for c in stores["top"]] == ["Pune", "Delhi", "Mumbai"]
    assert stores["top"][0] == {
        "group": "Pune",
        "value_a": 150000.0,
        "value_b": 60000.0,
        "delta": -90000.0,
        "share_of_change": 68.8,
    }
    assert [c["share_of_change"] for c in stores["top"]] == [68.8, 15.9, 15.3]
    assert "more" not in stores
    assert [c["group"] for c in result["contributors"]["category"]["top"]] == [
        "Electronics",
        "Grocery",
    ]
    # Fewer sales carried most of the fall; value per sale moved less.
    assert result["volume_vs_value"]["driven_by"] == "volume"
    assert result["volume_vs_value"]["count_delta_pct"] == -36.4
    assert "partial_period" not in result
    assert result["currency"] == {"SUM_revenue": None}
    assert "plain numbers" in result["currency_note"]
    assert "never invent a currency" in result["note"]
    assert "share_of_change" in result["note"] and "volume" in result["note"]
    assert meta["project_id"] == 180
    assert len(json.dumps(result)) < 3500


def test_drivers_cuts_each_list_to_five_and_counts_the_rest(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    many = {(f"Store {i}", "2026-07-01"): (100.0 * (i + 1), 1) for i in range(8)}
    _program(fake_service, monkeypatch, by_store=many)
    result, _ = view_drivers.view_data_drivers(
        _inv(project=180, extra_args=["7", "9"], input_file=_doc(tmp_path, _input()))
    )

    stores = result["contributors"]["store"]
    assert [c["group"] for c in stores["top"]] == [f"Store {i}" for i in (7, 6, 5, 4, 3)]
    assert stores["more"] == 3 and stores["others_delta"] == -600.0
    assert stores["groups"] == 8


def test_drivers_flags_a_period_the_data_does_not_cover_to_its_end(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _program(fake_service, monkeypatch, data_ends="2026-08-16")
    result, _ = view_drivers.view_data_drivers(
        _inv(project=180, extra_args=["7", "9"], input_file=_doc(tmp_path, _input()))
    )

    assert result["partial_period"] == [
        {"period": "2026-08", "data_through": "2026-08-16", "period_ends": "2026-08-31"}
    ]
    assert "2026-08 is partial: the data ends 2026-08-16." in result["note"]


def test_drivers_buckets_a_quarter_against_a_month_by_month(
    fake_service: FakeMammothService, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _program(fake_service, monkeypatch)
    payload = _input(compare=["2026-Q2", "2026-08"], by=["store"])
    result, _ = view_drivers.view_data_drivers(
        _inv(project=180, extra_args=["7", "9"], input_file=_doc(tmp_path, payload))
    )
    (grouped,) = _grouped_calls(fake_service)
    assert grouped["group_by"][1] == {"column": "column_4", "truncate": "MONTH"}
    # No July row falls in Q2: everything in A is zero.
    assert result["totals"]["a"] == {"value": 0.0, "count": 0}
    assert result["totals"]["delta_pct"] is None


@pytest.mark.parametrize(
    "compare",
    [
        ["July", "August"],
        ["2026-13", "2026-08"],
        ["2026-07"],
        ["2026-07", {"from": "2026-08-01"}],
        ["2026-07", {"from": "2026-08-31", "to": "2026-08-01"}],
        ["2026-Q5", "2026-Q3"],
    ],
)
def test_drivers_refuses_a_period_it_cannot_read(
    fake_service: FakeMammothService, tmp_path: Path, compare: list[Any]
) -> None:
    with pytest.raises(CliError) as excinfo:
        view_drivers.view_data_drivers(
            _inv(
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, _input(compare=compare)),
            )
        )
    assert excinfo.value.code == "invalid_arguments"
    assert fake_service.call_log == []


def test_drivers_refuses_a_measure_that_does_not_add_up(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    payload = _input(measure={"column": "revenue", "function": "AVG"})
    with pytest.raises(CliError) as excinfo:
        view_drivers.view_data_drivers(
            _inv(project=180, extra_args=["7", "9"], input_file=_doc(tmp_path, payload))
        )
    assert excinfo.value.code == "invalid_arguments"
