"""Live: each recipe run end to end on a real server; asserts the end state and dry-run counts.

Run on koyal: ``pytest -m live tests/live/test_recipes_live.py``. The module uploads small
CSVs of known content into a scratch project, runs ``mammoth recipe run`` (a ``--dry-run``
first, then the real run) and reads the result back with ordinary commands.

``orders`` has 6 rows: two exact duplicates (o1/Ada/10) and one repeated order id with a
different amount (o2), so 4 rows survive a dedupe on ``Order ID`` and 5 a whole-row dedupe.
``events`` holds TEXT dates; ``sales`` and ``regions`` blend on ``Region``.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli, upload_csv

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live

_ORDERS = """Order ID,Customer,Amount
o1,Ada,10
o1,Ada,10
o2,Bo,20
o2,Bo,25
o3,Cy,30
o4,Dee,40
"""
_EVENTS = """Event,Day,Status
a,2024-01-05,Active
b,2024-02-10,Closed
c,2024-03-15,Active
d,2024-04-20,Closed
"""
_SALES = """Region,Revenue
North,10
North,20
South,30
East,5
"""
_REGIONS = """Region,Manager
North,Ann
South,Sam
"""


def _recipe(
    cli: LiveCli, project: int, recipe_id: str, inputs: dict[str, Any], *flags: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run ``recipe run`` and return the line envelopes and the summary envelope."""
    argv = [
        "recipe",
        "run",
        recipe_id,
        "--input",
        json.dumps({"inputs": inputs}),
        "--yes",
        "--output",
        "json",
        "--no-input",
        "--project",
        str(project),
        *flags,
    ]
    output = make_runner().invoke(argv).output
    envelopes = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    assert envelopes, output
    return envelopes[:-1], envelopes[-1]


def _row_count(cli: LiveCli, project: int, dataset: int, view: int) -> int:
    data, _ = cli.ok("view", "get", str(view), str(dataset), project=project)
    return int(data["row_count"])


@pytest.fixture
def upload(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> Callable[[str], tuple[int, int]]:
    """Upload CSV text as a new dataset of this test only; return (dataset id, view id)."""

    def make(text: str) -> tuple[int, int]:
        return upload_csv(
            live_cli, scratch_project, tmp_path / f"{uuid.uuid4().hex[:10]}.csv", text
        )

    return make


def _rows(cli: LiveCli, project: int, dataset: int, view: int) -> list[dict[str, Any]]:
    data, _ = cli.ok("view", "data", "get", str(view), str(dataset), project=project)
    rows: list[dict[str, Any]] = data["data"]
    return rows


def test_remove_duplicates_by_key_previews_then_edits_the_named_view(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_ORDERS)
    inputs = {"view_id": view, "dataset_id": dataset, "key_columns": ["Order ID"]}

    dry_lines, dry = _recipe(live_cli, scratch_project, "remove-duplicates", inputs, "--dry-run")
    assert dry["data"]["version"] >= 2
    counted = [m for m in dry["data"]["predicted_impact"] if m["impact"] == "counted"]
    assert counted, dry["data"]["predicted_impact"]
    impact = dry_lines[0]["data"]["predicted_impact"]  # the preview line
    assert (impact["rows_removed"], impact["row_count"], impact["exact"]) == (2, 6, True)
    assert _row_count(live_cli, scratch_project, dataset, view) == 6  # a dry run changes nothing

    lines, summary = _recipe(live_cli, scratch_project, "remove-duplicates", inputs)
    assert summary["data"]["failed"] == 0, lines
    kept = _rows(live_cli, scratch_project, dataset, view)
    assert sorted(row["Order ID"] for row in kept) == ["o1", "o2", "o3", "o4"]
    listed, _ = live_cli.ok("view", "list", str(dataset), project=scratch_project)
    assert len(listed["dataviews"]) == 1  # no copy was made


def test_remove_duplicates_with_copy_leaves_the_original_unchanged(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_ORDERS)
    inputs = {
        "view_id": view,
        "dataset_id": dataset,
        "key_columns": ["Order ID", "Customer", "Amount"],
        "copy": True,
    }
    lines, summary = _recipe(live_cli, scratch_project, "remove-duplicates", inputs)
    assert summary["data"]["failed"] == 0, lines
    assert _row_count(live_cli, scratch_project, dataset, view) == 6  # the original is untouched
    copy = next(e for e in lines if e["data"].get("view_id") not in (None, view))
    kept = _rows(live_cli, scratch_project, dataset, int(copy["data"]["view_id"]))
    assert sorted((row["Order ID"], row["Amount"]) for row in kept) == [
        ("o1", "10"),
        ("o2", "20"),
        ("o2", "25"),
        ("o3", "30"),
        ("o4", "40"),
    ]


def test_discard_duplicates_refuses_key_columns_with_ignore_columns_or_in_a_batch(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_ORDERS)
    both = json.dumps(
        {"dataset_id": dataset, "key_columns": ["Order ID"], "ignore_columns": ["Amount"]}
    )
    error = live_cli.err(
        "view", "transform", "discard-duplicates", str(view), "--input", both, "--dry-run",
        project=scratch_project,
    )  # fmt: skip
    assert "not both" in error["message"]
    step = {"op": "discard-duplicates", "input": {"key_columns": ["Order ID"]}}
    error = live_cli.err(
        "view", "transform", "batch", str(view), "--input",
        json.dumps({"dataset_id": dataset, "steps": [step]}), "--dry-run",
        project=scratch_project,
    )  # fmt: skip
    assert "key_columns" in json.dumps(error)
    assert _row_count(live_cli, scratch_project, dataset, view) == 6


def test_remove_duplicates_without_key_columns_compares_whole_rows_in_place(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_ORDERS)
    lines, summary = _recipe(
        live_cli, scratch_project, "remove-duplicates", {"view_id": view, "dataset_id": dataset}
    )
    assert summary["data"]["failed"] == 0, lines
    assert _row_count(live_cli, scratch_project, dataset, view) == 5


def test_remove_duplicates_with_an_unknown_key_fails_loud(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_ORDERS)
    inputs = {"view_id": view, "dataset_id": dataset, "key_columns": ["Nope"]}
    lines, summary = _recipe(live_cli, scratch_project, "remove-duplicates", inputs)
    assert summary["data"]["failed"] == 1
    assert "Nope" in json.dumps(lines)


def test_filter_copy_keeps_matching_rows_on_a_copy_with_text_dates(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_EVENTS)
    inputs = {
        "view_id": view,
        "dataset_id": dataset,
        "column": "Status",
        "operator": "EQ",
        "value": "Active",
    }
    _, dry = _recipe(live_cli, scratch_project, "filter-copy", inputs, "--dry-run")
    assert dry["data"]["dry_run"] is True
    lines, summary = _recipe(live_cli, scratch_project, "filter-copy", inputs)
    assert summary["data"]["failed"] == 0, lines
    copy = int(next(e for e in lines if e["data"].get("view_id"))["data"]["view_id"])
    assert _row_count(live_cli, scratch_project, dataset, copy) == 2
    assert _row_count(live_cli, scratch_project, dataset, view) == 4


def test_filter_copy_that_matches_nothing_fails_and_keeps_the_source(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_EVENTS)
    inputs = {
        "view_id": view,
        "dataset_id": dataset,
        "column": "Status",
        "operator": "EQ",
        "value": "Nothing",
    }
    _, dry = _recipe(live_cli, scratch_project, "filter-copy", inputs, "--dry-run")
    assert dry["data"]["failed"] == 1
    assert _row_count(live_cli, scratch_project, dataset, view) == 4


def test_summarize_by_groups_by_several_columns_and_orders_them(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_SALES)
    inputs = {"view_id": view, "dataset_id": dataset, "group_by": ["Region"], "column": "Revenue"}
    lines, summary = _recipe(live_cli, scratch_project, "summarize-by", inputs)
    assert summary["data"]["failed"] == 0, lines
    rows = next(e for e in lines if e.get("cmd") == "view data aggregate")["data"]["data"]
    totals = [float(row["Result"]) for row in rows]
    assert totals == sorted(totals, reverse=True) == [30.0, 30.0, 5.0]  # ordered, largest first
    assert rows[-1]["Region"] == "East"
    assert _row_count(live_cli, scratch_project, dataset, view) == 4  # read only


def test_create_projects_twice_makes_each_project_once(
    live_cli: LiveCli, scratch_project: int
) -> None:
    suffix = uuid.uuid4().hex[:8]
    names = [f"recipe-live-{suffix}-a", f"recipe-live-{suffix}-b"]
    made: list[int] = []
    try:
        first_lines, first = _recipe(live_cli, scratch_project, "create-projects", {"names": names})
        assert first["data"]["failed"] == 0
        made = [int(e["data"]["project_id"]) for e in first_lines]
        assert [e["data"]["created"] for e in first_lines] == [True, True]
        again_lines, again = _recipe(live_cli, scratch_project, "create-projects", {"names": names})
        assert again["data"]["failed"] == 0
        assert [e["data"]["created"] for e in again_lines] == [False, False]
        assert [int(e["data"]["project_id"]) for e in again_lines] == made
    finally:
        for project_id in made:
            live_cli.run(
                "project", "delete", str(project_id), "--yes", "--confirm", str(project_id)
            )


def test_blend_by_key_reads_both_key_counts_then_joins_in_place(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_SALES)
    foreign_dataset, foreign_view = upload(_REGIONS)
    inputs = {
        "view_id": view,
        "dataset_id": dataset,
        "foreign_view_id": foreign_view,
        "foreign_dataset_id": foreign_dataset,
        "left_key": "Region",
        "right_key": "Region",
        "select": ["Manager"],
    }
    lines, summary = _recipe(live_cli, scratch_project, "blend-by-key", inputs, "--dry-run")
    assert summary["data"]["dry_run"] is True
    keys = [e["data"] for e in lines if e.get("cmd") == "view data aggregate"]
    assert len(keys) == 2  # both sides' key counts are read before the join
    assert _rows(live_cli, scratch_project, dataset, view)[0].get("Manager") is None
    _, real = _recipe(live_cli, scratch_project, "blend-by-key", inputs)
    assert real["data"]["failed"] == 0
    joined = _rows(live_cli, scratch_project, dataset, view)
    assert len(joined) == 4  # a LEFT join keeps every left row
    managers = sorted((row["Region"], row.get("Manager")) for row in joined)
    assert [m for m in managers if m[0] != "East"] == [
        ("North", "Ann"),
        ("North", "Ann"),
        ("South", "Sam"),
    ]
    assert [m[1] for m in managers if m[0] == "East"] in ([None], [""])


def test_email_view_dry_run_sends_nothing_and_marks_the_impact(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_SALES)
    inputs = {
        "view_id": view,
        "dataset_id": dataset,
        "emails": ["recipe-live@example.com"],
    }
    lines, summary = _recipe(live_cli, scratch_project, "email-view", inputs, "--dry-run")
    assert summary["data"]["dry_run"] is True and summary["data"]["failed"] == 0
    assert any(m["cmd"] == "view export email" for m in summary["data"]["predicted_impact"])
    assert [e for e in lines if e.get("cmd") == "view get"]


def test_export_to_s3_writes_one_export_that_the_view_lists(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_SALES)
    file_name = f"recipe-live-{uuid.uuid4().hex[:8]}.csv"
    inputs = {"view_id": view, "dataset_id": dataset, "file_name": file_name}
    before, _ = live_cli.ok(
        "view", "export", "list", str(view), str(dataset), project=scratch_project
    )
    assert before["exports"] == []
    _, summary = _recipe(live_cli, scratch_project, "export-to-s3", inputs)
    assert summary["data"]["failed"] == 0
    after, _ = live_cli.ok(
        "view", "export", "list", str(view), str(dataset), project=scratch_project
    )
    assert len(after["exports"]) == 1
    assert f'"dataview_id": {view}' in json.dumps(after["exports"])  # it belongs to this view


def test_dashboard_from_view_makes_one_dashboard(
    live_cli: LiveCli, scratch_project: int, upload: Callable[[str], tuple[int, int]]
) -> None:
    dataset, view = upload(_SALES)
    inputs = {"view_id": view, "intent": "Revenue by region"}
    lines, summary = _recipe(live_cli, scratch_project, "dashboard-from-view", inputs)
    assert summary["data"]["failed"] == 0, lines
    assert summary["data"]["version"] >= 2
    dashboard = next(e for e in lines if e.get("cmd") == "dashboard get")
    assert dashboard["exit"] == 0
