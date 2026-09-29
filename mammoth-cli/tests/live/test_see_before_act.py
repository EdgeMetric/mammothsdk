"""Live checks that reads show the data and tell the truth (PLAN-021 W4-CLI-SEE).

Run on a server with real credentials; skipped without them. Everything here is
read-only against the configured test project's existing data::

    set -a; . ../.env.plan; set +a
    pytest tests/live/test_see_before_act.py -m live -v

Each test names the fix it proves. The text-date tests need a view whose TEXT
column holds dates; they skip (never pass vacuously) when the project has none.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live

#: The agent tool cap the list summaries are sized for.
_TOOL_CAP = 4000
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _invoke(args: list[str], env: dict[str, str], project: str) -> Any:
    return make_runner().invoke(
        [*args, "--project", project, "--output", "json", "--no-input"], env=env
    )


def _ok(args: list[str], env: dict[str, str], project: str) -> tuple[Any, dict[str, Any]]:
    result = _invoke(args, env, project)
    assert result.exit_code == 0, f"`{' '.join(args)}` failed: {result.output}"
    envelope = json.loads(result.output)
    return envelope["data"], envelope["meta"]


def _err(args: list[str], env: dict[str, str], project: str) -> dict[str, Any]:
    result = _invoke(args, env, project)
    assert result.exit_code != 0, f"`{' '.join(args)}` should have failed: {result.output}"
    error: dict[str, Any] = json.loads(result.output)["error"]
    return error


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def _first_view_with(
    env: dict[str, str], project: str, wanted: Any
) -> tuple[int, dict[str, str]] | None:
    """(view id, {column: type}) of the first project view whose columns satisfy ``wanted``."""
    raw, _ = _ok(["view", "list", *_input({"full": True})], env, project)
    for record in raw.get("dataviews", []):
        types = {
            c["display_name"]: c["type"]
            for c in record.get("metadata") or []
            if "display_name" in c
        }
        if wanted(types):
            return int(record["id"]), types
    return None


def _text_date_column(types: dict[str, str]) -> str | None:
    return next((c for c, t in types.items() if t == "TEXT" and re.search("date", c, re.I)), None)


# -- 1. see: lists carry what tells items apart ------------------------------


def test_dataset_list_items_are_self_describing_and_fit_the_tool_cap(
    live_env: dict[str, str], live_project: str
) -> None:
    result = _invoke(["dataset", "list"], live_env, live_project)
    assert result.exit_code == 0, result.output
    assert len(result.output) < _TOOL_CAP + 1500, "a page must stay near the agent tool cap"
    data = json.loads(result.output)["data"]
    if not data["datasets"]:
        pytest.skip("the project has no datasets")
    for item in data["datasets"]:
        assert {"id", "name", "created", "source"} <= item.keys(), item
        assert "rows" in item or "columns" in item, item
    assert data["order"], "the list must state its order"
    assert "sample_values" in data["note"], "the list must say where sample values are"


def test_view_list_names_the_dataset_of_every_view(
    live_env: dict[str, str], live_project: str
) -> None:
    data, _ = _ok(["view", "list"], live_env, live_project)
    if not data["dataviews"]:
        pytest.skip("the project has no views")
    for item in data["dataviews"]:
        assert item.get("dataset_name"), f"view {item.get('id')} does not name its dataset"
        assert "sample_values" in item, f"view {item.get('id')} carries no stored sample values"
        values = item["sample_values"]
        assert isinstance(values, str) or all(len(v) <= 2 for v in values.values()), item
        assert isinstance(values, str) or len(values) <= 6, item


# -- 2. every read names the dataset and view it read ------------------------


def test_a_read_names_its_dataset_and_view_in_meta(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: bool(t))
    if found is None:
        pytest.skip("no view to read")
    view_id, _ = found
    for args in (
        ["view", "data", "get", str(view_id)],
        ["view", "preview", str(view_id)],
        [
            "view",
            "data",
            "aggregate",
            str(view_id),
            *_input({"aggregations": [{"function": "COUNT"}]}),
        ],
    ):
        _, meta = _ok(args, live_env, live_project)
        assert meta["view"]["id"] == view_id and meta["view"]["name"], (args, meta)
        assert meta["dataset"]["id"] and meta["dataset"]["name"], (args, meta)


# -- 3/4. text dates: bucket, state the format, fail loud --------------------


def test_group_by_month_on_a_text_date_states_its_format_and_returns_months(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: _text_date_column(t) is not None)
    if found is None:
        pytest.skip("no view with a TEXT date column")
    view_id, types = found
    column = _text_date_column(types)
    payload = {
        "aggregations": [{"function": "COUNT", "as_name": "n"}],
        "group_by": [{"column": column, "truncate": "MONTH"}],
    }
    result = _invoke(
        ["view", "data", "aggregate", str(view_id), *_input(payload)], live_env, live_project
    )
    if result.exit_code != 0:
        error = json.loads(result.output).get("error") or {}
        # Loud, with the reason -- never raw rows.
        assert error.get("code") == "invalid_arguments", result.output
        assert error.get("message"), result.output
        return
    data = json.loads(result.output)["data"]
    assert data["text_dates"][0]["assumed_format"], "the assumed format must be stated"
    buckets = [row[column] for row in data["data"]]
    assert buckets and all(b is None or _ISO_DAY.match(b) and b.endswith("-01") for b in buckets)


def test_truncate_on_a_non_date_column_is_refused_not_ignored(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: "NUMERIC" in t.values())
    if found is None:
        pytest.skip("no view with a NUMERIC column")
    view_id, types = found
    column = next(c for c, t in types.items() if t == "NUMERIC")
    payload = {
        "aggregations": [{"function": "COUNT"}],
        "group_by": [{"column": column, "truncate": "MONTH"}],
    }
    error = _err(
        ["view", "data", "aggregate", str(view_id), *_input(payload)], live_env, live_project
    )
    assert "DATE column" in error["message"]


def test_explore_refuses_a_column_type_that_disagrees_with_the_stored_type(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: "NUMERIC" in t.values())
    if found is None:
        pytest.skip("no view with a NUMERIC column")
    view_id, types = found
    column = next(c for c, t in types.items() if t == "NUMERIC")
    error = _err(
        ["view", "data", "explore", str(view_id), column, *_input({"column_type": "DATE"})],
        live_env,
        live_project,
    )
    assert "does not match" in error["message"]


def test_explore_by_year_on_a_text_date_states_its_format(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: _text_date_column(t) is not None)
    if found is None:
        pytest.skip("no view with a TEXT date column")
    view_id, types = found
    column = _text_date_column(types)
    result = _invoke(
        [
            "view",
            "data",
            "explore",
            str(view_id),
            str(column),
            *_input({"column_type": "DATE", "level": "YEAR"}),
        ],
        live_env,
        live_project,
    )
    if result.exit_code != 0:
        error = json.loads(result.output).get("error") or {}
        assert error.get("code") == "invalid_arguments" and error.get("message"), result.output
        return
    data = json.loads(result.output)["data"]
    assert data["text_dates"][0]["assumed_format"]
    years = [row["bucket"] for row in data["data"] if row["bucket"] is not None]
    assert years == sorted(years) and all(y.endswith("-01-01") for y in years)


# -- 5. aggregate: order_by / top, and unordered limit -----------------------


def _category_and_number(types: dict[str, str]) -> tuple[str, str] | None:
    text = next((c for c, t in types.items() if t == "TEXT"), None)
    number = next((c for c, t in types.items() if t == "NUMERIC"), None)
    return (text, number) if text and number else None


def test_top_returns_the_highest_groups_in_order(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: _category_and_number(t) is not None)
    if found is None:
        pytest.skip("no view with a TEXT and a NUMERIC column")
    view_id, types = found
    category, number = _category_and_number(types) or ("", "")
    payload = {
        "group_by": [category],
        "aggregations": [{"column": number, "function": "SUM", "as_name": "Total"}],
        "order_by": ["Total desc"],
        "top": 3,
    }
    data, _ = _ok(
        ["view", "data", "aggregate", str(view_id), *_input(payload)], live_env, live_project
    )
    totals = [row["Total"] for row in data["data"] if row["Total"] is not None]
    assert 0 < len(data["data"]) <= 3
    assert totals == sorted(totals, reverse=True)
    assert "ordered" not in data, "a ranked result must not be flagged unordered"


def test_a_limit_without_order_by_is_flagged_unordered(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(live_env, live_project, lambda t: _category_and_number(t) is not None)
    if found is None:
        pytest.skip("no view with a TEXT and a NUMERIC column")
    view_id, types = found
    category, number = _category_and_number(types) or ("", "")
    payload = {
        "group_by": [category],
        "aggregations": [{"column": number, "function": "SUM", "as_name": "Total"}],
        "limit": 2,
    }
    data, _ = _ok(
        ["view", "data", "aggregate", str(view_id), *_input(payload)], live_env, live_project
    )
    assert data["ordered"] is False
    assert "order_by" in data["note"]


# -- 6. an empty result says what the data covers ----------------------------


def test_an_empty_result_states_the_observed_range_of_the_filtered_column(
    live_env: dict[str, str], live_project: str
) -> None:
    found = _first_view_with(
        live_env,
        live_project,
        lambda t: _text_date_column(t) is not None or "DATE" in t.values(),
    )
    if found is None:
        pytest.skip("no view with a date column")
    view_id, types = found
    column = _text_date_column(types) or next(c for c, t in types.items() if t == "DATE")
    payload = {
        "aggregations": [{"function": "COUNT", "as_name": "n"}],
        "group_by": [{"column": column, "truncate": "YEAR"}],
        "condition": {
            "column": column,
            "operator": "IN_RANGE",
            "value": ["1900-01-01", "1900-01-02"],
        },
    }
    result = _invoke(
        ["view", "data", "aggregate", str(view_id), *_input(payload)], live_env, live_project
    )
    if result.exit_code != 0:
        error = json.loads(result.output).get("error") or {}
        assert error.get("code") == "invalid_arguments" and error.get("message"), result.output
        return
    data = json.loads(result.output)["data"]
    assert data["data"] == []
    (covered,) = [r for r in data["observed_range"] if r["column"] == column]
    assert covered["min"] and covered["max"]
