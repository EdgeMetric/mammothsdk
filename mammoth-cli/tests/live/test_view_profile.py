"""Live checks for PLAN-021 W4: whole-view profile, scoped check, values after writes.

Runs the real CLI in-process against a real tenant (no doubles). Read tests
compare the profile with independent ``view data aggregate`` answers; the two
write tests create their own disposable view / dashboard and remove it.

    set -a; . ../.env.plan; set +a
    pytest tests/live/test_view_profile.py -m live -v
"""

from __future__ import annotations

import json
import statistics
import time
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live


def _run(args: list[str], env: dict[str, str], *, input_doc: dict[str, Any] | None = None) -> Any:
    argv = [*args, "--output", "json", "--no-input"]
    if input_doc is not None:
        argv += ["--input", json.dumps(input_doc)]
    result = make_runner().invoke(argv, env=env)
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert not envelope.get("error"), envelope.get("error")
    return envelope["data"]


def _first_view(env: dict[str, str], project: str) -> tuple[str, str]:
    datasets = _run(["dataset", "list", "--project", project], env)
    items = datasets.get("datasets") if isinstance(datasets, dict) else datasets
    if not items:
        pytest.skip("no dataset in the configured project")
    dataset_id = str(items[0]["id"])
    views = _run(["view", "list", dataset_id, "--project", project], env)
    listed = views if isinstance(views, list) else views.get("dataviews") or views.get("views")
    if not listed:
        pytest.skip("no view in the first dataset")
    return dataset_id, str(listed[0]["id"])


def _count(env: dict[str, str], project: str, view: str, condition: dict[str, Any] | None) -> int:
    document: dict[str, Any] = {"aggregations": [{"function": "COUNT", "as_name": "n"}]}
    if condition:
        document["condition"] = condition
    data = _run(["view", "data", "aggregate", view, "--project", project], env, input_doc=document)
    return int(data["data"][0]["n"])


def test_profile_covers_the_whole_view_and_agrees_with_aggregate(
    live_env: dict[str, str], live_project: str
) -> None:
    """row_count and a column's blank count equal independent whole-view aggregates."""
    _, view = _first_view(live_env, live_project)
    profile = _run(
        ["view", "data", "profile", view, "--project", live_project], live_env, input_doc={}
    )

    assert profile["row_count"] == _count(live_env, live_project, view, None)
    detail = profile["columns_detail"][0]
    blank = _count(
        live_env,
        live_project,
        view,
        {"column": detail["column"], "operator": "IS_EMPTY"},
    )
    assert detail["nulls"] == blank
    assert detail["distinct"] <= profile["row_count"]


def test_profile_with_target_reports_the_class_share_and_a_ranking(
    live_env: dict[str, str], live_project: str
) -> None:
    """The target's positive_rate is its rarest class count over the labelled rows."""
    _, view = _first_view(live_env, live_project)
    base = _run(
        ["view", "data", "profile", view, "--project", live_project], live_env, input_doc={}
    )
    targets = [c for c in base["columns_detail"] if 2 <= c["distinct"] <= 20]
    if not targets:
        pytest.skip("no low-cardinality column to use as a target")
    target = targets[0]["column"]

    profile = _run(
        ["view", "data", "profile", view, "--project", live_project],
        live_env,
        input_doc={"target": target},
    )

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
    live_env: dict[str, str], live_project: str
) -> None:
    dataset, _ = _first_view(live_env, live_project)
    checked = _run(["project", "check", live_project, dataset], live_env)

    assert checked["scope"]["dataset_id"] == int(dataset)
    assert {entry["dataset_id"] for entry in checked["views"]} <= {int(dataset)}
    assert checked["dashboards"] == []


def test_async_read_is_not_held_to_a_two_second_poll(
    live_env: dict[str, str], live_project: str
) -> None:
    """A small aggregate job finishes in well under the old fixed 2 s poll interval."""
    _, view = _first_view(live_env, live_project)
    _count(live_env, live_project, view, None)  # warm the metadata/parent caches
    timings = []
    for _ in range(5):
        started = time.monotonic()
        _count(live_env, live_project, view, None)
        timings.append(time.monotonic() - started)
    assert statistics.median(timings) < 2.0, timings


def test_a_view_edit_returns_the_changed_column_values(
    live_env: dict[str, str], live_project: str
) -> None:
    """Rename a column on a disposable view: state.changed_columns lists its values."""
    dataset, _ = _first_view(live_env, live_project)
    created = _run(["view", "create", dataset, "--project", live_project], live_env)
    view = str(created["id"])
    try:
        info = _run(["view", "data", "get", view, "--project", live_project], live_env)
        first = next(iter(info["data"][0]))
        edited = _run(
            ["view", "transform", "rename-columns", view, "--project", live_project],
            live_env,
            input_doc={"renames": {first: "W4 renamed"}, "dataset_id": int(dataset)},
        )
        changed = edited["state"]["changed_columns"]["W4 renamed"]
        assert isinstance(changed, list) and changed
    finally:
        make_runner().invoke(
            [
                "view",
                "delete",
                view,
                dataset,
                "--yes",
                "--confirm",
                view,
                "--project",
                live_project,
                "--no-input",
                "--output",
                "json",
            ],
            env=live_env,
        )


def test_generate_returns_evaluated_kpi_numbers_and_the_link(
    live_env: dict[str, str], live_project: str
) -> None:
    """A generated board carries dashboard_link and a number for its KPI cards."""
    _, view = _first_view(live_env, live_project)
    built = _run(
        ["dashboard", "v3", "generate", "--project", live_project],
        live_env,
        input_doc={
            "body": {"params": {"intent": "Overview of the key totals", "dataview_id": int(view)}}
        },
    )
    board = built.get("id") or built.get("dashboard_id")
    try:
        assert built["dashboard_link"].endswith(f"/publish/{board}")
        cards = [v for v in built["values"]["values"] if v["kind"] == "kpi"]
        assert cards and all("value" in card or "error" in card for card in cards)
    finally:
        if board:
            make_runner().invoke(
                [
                    "dashboard",
                    "delete",
                    str(board),
                    "--yes",
                    "--confirm",
                    str(board),
                    "--project",
                    live_project,
                    "--no-input",
                    "--output",
                    "json",
                ],
                env=live_env,
            )
