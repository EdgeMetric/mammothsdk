"""``view data profile`` against a small table whose answers are worked out from the raw rows.

The fake ``aggregate`` runs COUNT / DISTINCT_COUNT / MIN / MAX / AVG / STDDEV, ``group_by`` and an
EQ / NE condition over an in-memory table, the way SQL does (blank cells are left out of a
distinct count, a min, a mean and a ``<>`` comparison). Every expected figure is computed here
from the raw rows with the standard library, not read back from the code under test.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_profile
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime import trace
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_FIND = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"
_STORED = "mammoth.api.ai.AIAPI.generate_profile"
_ARGS = ["--project", "180", "--output", "json", "--no-input"]

_COLUMNS = [
    ("Name", "column_name", "TEXT"),
    ("Segment", "column_seg", "TEXT"),
    ("Amount", "column_amt", "NUMERIC"),
    ("Churned", "column_chu", "TEXT"),
    ("Const", "column_con", "TEXT"),
    ("Blank", "column_bla", "TEXT"),
    ("Sparse", "column_spa", "TEXT"),
    ("Lone", "column_lon", "TEXT"),
]
_META = [{"display_name": d, "internal_name": i, "type": t} for d, i, t in _COLUMNS]


def _row(i: int) -> dict[str, Any]:
    return {
        "column_name": ["Acme Ltd", "ACME Limited", "Zed"][i % 3],
        "column_seg": "A" if i < 24 else "B",
        "column_amt": float(i),
        "column_chu": None if i >= 38 else ("yes" if i % 8 == 0 else "no"),
        "column_con": "same",
        "column_bla": None,
        "column_spa": ("x" if i % 2 else "y") if i < 10 else None,
        "column_lon": "q" if i < 10 else None,
    }


ROWS = [_row(i) for i in range(40)]
_INTERNAL = {d: i for d, i, _ in _COLUMNS}


def _present(column: str, rows: list[dict[str, Any]]) -> list[Any]:
    return [r[column] for r in rows if r[column] is not None]


def _matching(condition: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not condition:
        return ROWS
    ((column, test),) = condition.items()
    ((operator, spec),) = test.items()
    value = spec["VALUE"]
    keeps: dict[str, Callable[[Any], bool]] = {
        "EQ": lambda cell: cell == value,
        "NE": lambda cell: cell != value,
        "IN_LIST": lambda cell: cell in value,
        "NOT_IN_LIST": lambda cell: cell not in value,
    }
    keep = keeps[operator]
    return [r for r in ROWS if r[column] is not None and keep(r[column])]


def _measure(spec: dict[str, Any], rows: list[dict[str, Any]]) -> Any:
    function, column = spec["function"], spec.get("column")
    if function == "COUNT":
        return len(rows)
    assert column is not None
    values = _present(column, rows)
    if function == "DISTINCT_COUNT":
        return len(set(values))
    if not values:
        return None
    measures: dict[str, Callable[[], Any]] = {
        "MIN": lambda: min(values),
        "MAX": lambda: max(values),
        "AVG": lambda: statistics.fmean(values),
        "STDDEV": lambda: statistics.stdev(values) if len(values) > 1 else None,
    }
    return measures[function]()


def _aggregate(call_log: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    kwargs = call_log[-1][1]
    rows = _matching(kwargs.get("condition"))
    group_by = kwargs.get("group_by") or []
    if not group_by:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {(): rows}
    else:
        groups = {}
        for row in rows:
            groups.setdefault(tuple(row[c] for c in group_by), []).append(row)
    out = []
    for key, members in groups.items():
        line = {f"group_{n}": v for n, v in enumerate(key)}
        line.update(
            {f"agg_{n}": _measure(a, members) for n, a in enumerate(kwargs["aggregations"])}
        )
        out.append(line)
    return {"data": out[: kwargs["limit"]] if "limit" in kwargs else out}


def _stored(rows_total: int = 40) -> dict[str, Any]:
    """The backend's stored stats for ``Name`` (3 distinct, no blank), over ``rows_total`` rows."""
    return {
        "profile": {
            "column_name": {
                "schema_analysis": {"num_unique": 3},
                "performance_metadata": {"missing_count": 0, "total_rows": rows_total},
                "quality_metrics": {"empty_string_count": 0},
                "statistical_summary": {"data_sample": ["Zed", "Acme Ltd"]},
            }
        }
    }


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_GET] = {"id": 7, "name": "Sales", "row_count": 40, "metadata": _META}
    fake_service.responses[_FIND] = 9
    fake_service.responses[_AGGREGATE] = _aggregate
    fake_service.responses[_STORED] = CliError(
        code="api_error", message="no stats yet", exit_status=1
    )
    return fake_service


def _profile(payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    argv = ["view", "data", "profile", "7", *_ARGS]
    if payload is not None:
        argv += ["--input", json.dumps(payload)]
    result = make_runner().invoke(argv)
    start = result.output.find("{")
    assert start != -1, result.output
    return result.exit_code, json.loads(result.output[start:])


def _detail(data: dict[str, Any], column: str) -> dict[str, Any]:
    return next(d for d in data["columns_detail"] if d["column"] == column)


def _aggregations(service: FakeMammothService) -> list[dict[str, Any]]:
    return [k for name, k in service.call_log if name == _AGGREGATE]


# ── what each column holds ──


def test_each_column_reports_its_distinct_count_range_blanks_and_top_values(
    service: FakeMammothService,
) -> None:
    code, out = _profile()
    assert code == 0, out
    data = out["data"]
    assert (data["view_id"], data["dataset_id"], data["row_count"]) == (7, 9, 40)

    name = _detail(data, "Name")
    counts = Counter(r["column_name"] for r in ROWS)
    assert name["distinct"] == 3
    assert name["nulls"] == 0
    assert name["top"] == [f"{v} ({n})" for v, n in sorted(counts.items(), key=lambda kv: -kv[1])]
    assert name["from"] == "query"

    amount = _detail(data, "Amount")
    assert (amount["distinct"], amount["min"], amount["max"]) == (40, 0.0, 39.0)
    assert amount["nulls"] == 0  # all 40 values differ, so no row can be blank
    assert amount["note"] == "every value is different"
    assert "top" not in amount  # a number column's values are not tabulated unless asked

    churned = _detail(data, "Churned")
    assert churned["nulls"] == 2
    assert churned["top"] == ["no (33)", "yes (5)"]


def test_the_summary_names_constant_all_blank_and_mostly_blank_columns(
    service: FakeMammothService,
) -> None:
    _, out = _profile()
    summary = out["data"]["summary"]
    assert summary["columns"] == 8
    assert "Const" in summary["constant"]
    assert summary["all_blank"] == ["Blank"]
    assert summary["mostly_blank"] == [{"column": "Sparse", "nulls": 30}]


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: a column with one value and an unknown blank count (nulls is None, 'not guessed') "
        "is listed constant although 30 of its 40 rows are blank"
    ),
)
def test_a_one_value_column_that_is_mostly_blank_is_not_called_constant(
    service: FakeMammothService,
) -> None:
    _, out = _profile()
    assert "Lone" not in out["data"]["summary"]["constant"]


def test_a_named_column_list_profiles_only_those_columns_with_their_value_tables(
    service: FakeMammothService,
) -> None:
    _, out = _profile({"columns": ["Segment", "Amount"], "top": 1})
    data = out["data"]
    assert [d["column"] for d in data["columns_detail"]] == ["Segment", "Amount"]
    assert _detail(data, "Segment")["top"] == ["A (24)"]
    # an explicitly named NUMERIC column is tabulated too: 40 values, each once
    assert len(_detail(data, "Amount")["top"]) == 1  # top=1 of 40 single values
    assert "columns_not_profiled" not in data


def test_columns_beyond_the_default_twenty_are_reported_as_not_profiled(
    service: FakeMammothService,
) -> None:
    wide = [
        {"display_name": f"C{n:02d}", "internal_name": f"column_{n:02d}", "type": "TEXT"}
        for n in range(22)
    ]
    service.responses[_GET] = {"id": 7, "name": "Wide", "row_count": 40, "metadata": wide}
    service.responses[_AGGREGATE] = lambda log: {"data": [{"agg_0": 40}]}
    _, out = _profile()
    data = out["data"]
    assert data["summary"]["columns"] == 20
    assert data["columns_not_profiled"] == ["C20", "C21"]
    assert data["columns_not_profiled_note"] == (
        "Only the first 20 of 22 columns were profiled; "
        "pass input 'columns' (names) to profile others."
    )


def test_the_detail_list_is_paged_by_limit_and_says_how_many_were_left_out(
    service: FakeMammothService,
) -> None:
    _, out = _profile({"limit": 2})
    data = out["data"]
    assert [d["column"] for d in data["columns_detail"]] == ["Name", "Segment"]
    assert data["columns_omitted"] == 6
    assert data["columns_note"] == (
        "Pass input 'columns' (names) or a larger 'limit' to see the rest."
    )


def test_columns_must_be_columns_of_the_view(service: FakeMammothService) -> None:
    code, out = _profile({"columns": ["Nope"]})
    assert code == 2
    assert out["error"]["code"] == "invalid_arguments"
    assert out["error"]["message"] == "columns not in the view: ['Nope']"
    assert out["error"]["hint"].startswith("Columns: Amount, Blank, Churned")


# ── spelling variants ──


def test_spelling_variants_come_with_the_bulk_replace_that_merges_them(
    service: FakeMammothService,
) -> None:
    _, out = _profile()
    data = out["data"]
    assert "Name" in data["spelling_variants_checked"]
    (entry,) = [v for v in data["spelling_variants"] if v["column"] == "Name"]
    # "Acme Ltd" and "ACME Limited" are one company written two ways; "Zed" is another
    assert entry["command"].startswith("mammoth view transform bulk-replace 7 --input ")
    body = entry["bulk_replace"]
    assert body["dataset_id"] == 9
    skipped = {s["column"]: s["reason"] for s in data["spelling_variants_skipped"]}
    assert skipped["Amount"] == "type is NUMERIC, not TEXT"


# ── stored stats ──


def test_current_stored_stats_replace_the_distinct_count_queries(
    service: FakeMammothService,
) -> None:
    service.responses[_STORED] = _stored(40)
    _, out = _profile({"columns": ["Name"]})
    data = out["data"]
    assert _detail(data, "Name")["from"] == "stored"
    block = data["sources"]["stored_stats"]
    assert (block["used"], block["columns"], block["live_rows"]) == (True, 1, 40)
    assert block["row_count_matches"] is True
    assert block["verified_current"] is False  # a matching row count is never called proof
    functions = {
        a["function"] for call in _aggregations(service) for a in call.get("aggregations", [])
    }
    assert "DISTINCT_COUNT" not in functions


def test_stored_stats_over_another_row_count_are_not_used_and_the_reason_says_so(
    service: FakeMammothService,
) -> None:
    service.responses[_STORED] = _stored(39)
    _, out = _profile({"columns": ["Name"]})
    data = out["data"]
    assert _detail(data, "Name")["from"] == "query"
    block = data["sources"]["stored_stats"]
    assert block["used"] is False
    assert block["reason"].startswith("stored stats cover 39 rows, the view has 40 now")
    assert data["sources"]["queried"]["columns_without_stored_stats"] == 1


def test_stored_stats_that_cannot_be_read_fall_back_to_queries_and_say_why(
    service: FakeMammothService,
) -> None:
    code, out = _profile({"columns": ["Name"]})
    assert code == 0
    block = out["data"]["sources"]["stored_stats"]
    assert (block["used"], block["row_count_matches"]) == (False, False)
    assert block["reason"] == "stored stats unavailable: no stats yet"


# ── target comparison ──


def test_a_target_ranks_the_other_columns_against_its_rarest_class(
    service: FakeMammothService,
) -> None:
    code, out = _profile({"target": "Churned", "columns": ["Segment", "Amount", "Name"]})
    assert code == 0, out
    target = out["data"]["target"]
    labeled = [r for r in ROWS if r["column_chu"] is not None]
    yes = [r for r in labeled if r["column_chu"] == "yes"]
    rest = [r for r in labeled if r["column_chu"] != "yes"]
    assert target["column"] == "Churned"
    assert (target["rows_with_target"], target["rows_without_target"]) == (38, 2)
    assert target["classes"] == [
        {"value": "no", "rows": len(rest), "share": round(len(rest) / 38, 4)},
        {"value": "yes", "rows": len(yes), "share": round(len(yes) / 38, 4)},
    ]
    assert target["positive"] == "yes"
    assert target["positive_rate"] == round(len(yes) / 38, 4)
    assert target["positive_rule"] == "the rarest class of the target"

    (numeric,) = target["association"]["numeric"]
    amounts_yes = [r["column_amt"] for r in yes]
    amounts_rest = [r["column_amt"] for r in rest]
    pooled = math.sqrt(
        (
            (len(yes) - 1) * statistics.variance(amounts_yes)
            + (len(rest) - 1) * statistics.variance(amounts_rest)
        )
        / (len(yes) + len(rest) - 2)
    )
    assert numeric["column"] == "Amount"
    assert numeric["mean_positive"] == statistics.fmean(amounts_yes)
    assert numeric["mean_rest"] == statistics.fmean(amounts_rest)
    assert numeric["standardized_difference"] == round(
        (statistics.fmean(amounts_yes) - statistics.fmean(amounts_rest)) / pooled, 4
    )
    categorical = {c["column"] for c in target["association"]["categorical"]}
    assert categorical == {"Segment", "Name"}
    assert target["skipped"] == []


def test_the_target_is_profiled_even_when_columns_leaves_it_out(
    service: FakeMammothService,
) -> None:
    _, out = _profile({"target": "Churned", "columns": ["Segment"]})
    assert out["data"]["target"]["rows_with_target"] == 38
    assert [d["column"] for d in out["data"]["columns_detail"]] == ["Segment"]


def test_a_target_outside_the_view_is_refused_before_any_query(
    service: FakeMammothService,
) -> None:
    code, out = _profile({"target": "Nope"})
    assert code == 2
    assert out["error"]["message"] == "target column 'Nope' is not in the view"
    assert _aggregations(service) == []


def test_a_target_with_a_single_value_is_refused_with_the_class_limits(
    service: FakeMammothService,
) -> None:
    code, out = _profile({"target": "Const"})
    assert code == 2
    assert out["error"]["message"] == (
        "target 'Const' has 1 distinct values; a target needs between 2 and 20."
    )


def test_a_target_with_too_many_values_is_refused(service: FakeMammothService) -> None:
    code, out = _profile({"target": "Amount"})
    assert code == 2
    assert out["error"]["message"] == (
        "target 'Amount' has 40 distinct values; a target needs between 2 and 20."
    )


# ── boundaries of the blank arithmetic ──


def _summary_row(name: str, distinct: int, nulls: int | None) -> dict[str, Any]:
    return {"column": name, "type": "TEXT", "distinct": distinct, "nulls": nulls}


def test_a_column_is_mostly_blank_from_exactly_half_its_rows() -> None:
    """Pins the code's reading of "mostly": half of the rows or more (``nulls * 2 >= rows``)."""
    from mammoth_cli.commands import view_profile as vp

    details = {
        "Under": _summary_row("Under", 3, 49),
        "Half": _summary_row("Half", 3, 50),
        "Over": _summary_row("Over", 3, 51),
        "Unknown": _summary_row("Unknown", 3, None),
        "Empty": _summary_row("Empty", 0, 100),
    }
    summary = vp._summary(details, 100, {})
    assert summary["mostly_blank"] == [
        {"column": "Half", "nulls": 50},
        {"column": "Over", "nulls": 51},
    ]
    # an all-blank column is reported as all_blank only
    assert summary["all_blank"] == ["Empty"]


def test_blanks_are_known_without_a_query_only_from_stats_or_all_rows_distinct() -> None:
    from mammoth_cli.commands import view_profile as vp

    nulls = vp._nulls
    # stored stats win
    assert nulls(None, "C", {"nulls": "7"}, 3, 10) == 7  # type: ignore[arg-type]
    # no value at all: every row is blank
    assert nulls(None, "C", {}, 0, 10) == 10  # type: ignore[arg-type]
    # as many distinct values as rows leaves no room for a blank; one fewer might hide one
    assert nulls(None, "C", {}, 10, 10) == 0  # type: ignore[arg-type]
    assert nulls(None, "C", {}, 9, 10) is None  # type: ignore[arg-type]


def test_profile_workers_run_in_the_trace_of_the_command() -> None:
    with trace.begin("view.data.profile") as traced:
        seen = view_profile._map_all(3, lambda _item: trace.current(), [1, 2, 3])
    assert [worker.invocation_id for worker in seen if worker] == [traced.invocation_id] * 3
