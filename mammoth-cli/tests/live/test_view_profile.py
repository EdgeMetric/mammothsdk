"""Live checks for PLAN-021 W4: whole-view profile, scoped check, values after writes.

Runs the real CLI in-process against a real tenant (no doubles). The module
uploads its own sales CSV into a scratch project and deletes the project at the
end. Read tests compare the profile with independent ``view data aggregate``
answers; the two write tests create their own disposable view / dashboard and
remove it.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_view_profile.py -m live -v
"""

from __future__ import annotations

import json
import statistics
import time
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def _count(cli: LiveCli, data: SalesData, condition: dict[str, Any] | None) -> int:
    document: dict[str, Any] = {"aggregations": [{"function": "COUNT", "as_name": "n"}]}
    if condition:
        document["condition"] = condition
    result, _ = cli.ok(
        "view", "data", "aggregate", str(data.view), *_input(document), project=data.project
    )
    return int(result["data"][0]["n"])


def _profile(cli: LiveCli, data: SalesData, document: dict[str, Any]) -> Any:
    result, _ = cli.ok(
        "view", "data", "profile", str(data.view), *_input(document), project=data.project
    )
    return result


def test_profile_covers_the_whole_view_and_agrees_with_aggregate(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """row_count and a column's blank count equal independent whole-view aggregates."""
    profile = _profile(live_cli, sales_data, {})

    assert profile["row_count"] == _count(live_cli, sales_data, None)
    detail = profile["columns_detail"][0]
    blank = _count(live_cli, sales_data, {"column": detail["column"], "operator": "IS_EMPTY"})
    assert detail["nulls"] == blank
    assert detail["distinct"] <= profile["row_count"]


def test_profile_with_target_reports_the_class_share_and_a_ranking(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """The target's positive_rate is its rarest class count over the labelled rows."""
    base = _profile(live_cli, sales_data, {})
    targets = [c for c in base["columns_detail"] if 2 <= c["distinct"] <= 20]
    if not targets:
        pytest.skip("no low-cardinality column to use as a target")
    target = targets[0]["column"]

    profile = _profile(live_cli, sales_data, {"target": target})

    classes = profile["target"]["classes"]
    rarest = min(classes, key=lambda item: item["rows"])
    assert profile["target"]["positive_rate"] == round(
        rarest["rows"] / sum(c["rows"] for c in classes), 4
    )
    association = profile["target"]["association"]
    assert all("cramers_v" in item for item in association["categorical"])
    assert all("standardized_difference" in item for item in association["numeric"])
    sources = profile["sources"]
    assert sources["stored_stats"]["as_of"] == "not recorded by the backend"
    assert sources["queried"]["backend_jobs"] < 3 * len(profile["columns_detail"]) + 10


def test_scoped_project_check_reads_only_the_named_dataset(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    dataset = sales_data.dataset
    checked, _ = live_cli.ok(
        "project", "check", str(sales_data.project), str(dataset), project=sales_data.project
    )

    assert checked["scope"]["dataset_id"] == dataset
    assert {entry["dataset_id"] for entry in checked["views"]} <= {dataset}
    assert checked["dashboards"] == []


def test_async_read_is_not_held_to_a_two_second_poll(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """A small aggregate job finishes in well under the old fixed 2 s poll interval."""
    _count(live_cli, sales_data, None)  # warm the metadata/parent caches
    timings = []
    for _ in range(5):
        started = time.monotonic()
        _count(live_cli, sales_data, None)
        timings.append(time.monotonic() - started)
    assert statistics.median(timings) < 2.0, timings


def test_a_view_edit_returns_the_changed_column_values(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """Rename a column on a disposable view: state.changed_columns lists its values."""
    project, dataset = sales_data.project, sales_data.dataset
    created, _ = live_cli.ok("view", "create", str(dataset), "--yes", project=project)
    view = str(created["id"])
    try:
        info, _ = live_cli.ok("view", "data", "get", view, project=project)
        first = next(iter(info["data"][0]))
        edited, _ = live_cli.ok(
            *("view", "transform", "rename-columns", view),
            *_input({"renames": {first: "W4 renamed"}, "dataset_id": dataset}),
            "--yes",
            project=project,
        )
        changed = edited["state"]["changed_columns"]["W4 renamed"]
        assert isinstance(changed, list) and changed
    finally:
        live_cli.run(
            *("view", "delete", view, str(dataset), "--yes", "--confirm", view), project=project
        )


def test_generate_returns_evaluated_kpi_numbers_and_the_link(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """A generated board carries dashboard_link and a number for its KPI cards."""
    project = sales_data.project
    built, _ = live_cli.ok(
        *("dashboard", "v3", "generate"),
        *_input(
            {
                "body": {
                    "params": {
                        "intent": "Overview of the key totals",
                        "dataview_id": sales_data.view,
                    }
                }
            }
        ),
        project=project,
    )
    board = built.get("id") or built.get("dashboard_id")
    try:
        assert built["dashboard_link"].endswith(f"/publish/{board}")
        cards = [v for v in built["values"]["values"] if v["kind"] == "kpi"]
        assert cards and all("value" in card or "error" in card for card in cards)
    finally:
        if board:
            live_cli.run(
                *("dashboard", "delete", str(board), "--yes", "--confirm", str(board)),
                project=project,
            )
