"""Live: the shape of the reads an agent acts on, against data the module wrote.

Replaces the fake-socket realcode tests ``test_reads_full_stack``, ``test_reads_next_step``,
``test_call_many`` and ``test_upload_preview_checks``. The scratch project holds:

``wide`` has ten numeric columns; ``dated`` has an ISO date, a number and a label (four rows:
Saturday 300.5 and 200.25, Tuesday 400, Wednesday 50); ``texty`` has day-first text dates
(13/03/2024 10, 20/03/2024 5, 02/01/2023 7).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest
from live_harness import LiveCli, open_live_service, upload_csv

from mammoth_cli.commands.view import upload_preview
from mammoth_cli.errors.envelope import CliError

pytestmark = pytest.mark.live

_WIDE = (
    ",".join(f"Col {n}" for n in range(10))
    + "\n"
    + "\n".join(",".join(str(row * 10 + n) for n in range(10)) for row in range(3))
    + "\n"
)
_DATED = """Order Date,Sales,Label
2024-01-13,300.5,a
2024-01-06,200.25,b
2024-01-09,400,c
2024-01-10,50,d
2019-02-03,1,e
2024-11-30,2,f
"""
_TEXTY = """Order Date,Sales
13/03/2024,10
20/03/2024,5
02/01/2023,7
"""
_VIEW_SYMBOL = "mammoth.api.dataviews.DataviewsAPI.get"


@dataclass(frozen=True)
class Tables:
    project: int
    wide: tuple[int, int]
    dated: tuple[int, int]
    texty: tuple[int, int]


@pytest.fixture(scope="module")
def tables(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> Tables:
    folder = tmp_path_factory.mktemp("shapes")
    made = {
        name: upload_csv(live_cli, scratch_project, folder / f"{name}.csv", text)
        for name, text in (("wide", _WIDE), ("dated", _DATED), ("texty", _TEXTY))
    }
    return Tables(scratch_project, made["wide"], made["dated"], made["texty"])


def _aggregate(
    cli: LiveCli, tables: Tables, target: tuple[int, int], document: dict[str, Any]
) -> dict[str, Any]:
    dataset, view = target
    return cli.run(
        *("view", "data", "aggregate", str(view), str(dataset)),
        *("--input", json.dumps(document)),
        project=tables.project,
    )


# -- view list -------------------------------------------------------------


def test_view_list_lists_every_column_with_its_type_for_one_dataset(
    live_cli: LiveCli, tables: Tables
) -> None:
    dataset = str(tables.wide[0])
    default, _ = live_cli.ok("view", "list", dataset, project=tables.project)
    full, _ = live_cli.ok(
        *("view", "list", dataset, "--input", json.dumps({"all_columns": True})),
        project=tables.project,
    )

    for listed in (default, full):
        columns = listed["dataviews"][0]["columns"]
        assert "more)" not in columns
        assert columns.startswith("Col 0:numeric") and columns.endswith("Col 9:numeric")


def test_view_list_names_what_a_view_is_built_from_and_what_reads_it(
    live_cli: LiveCli, tables: Tables
) -> None:
    project = tables.project
    plain, _ = live_cli.ok("view", "list", str(tables.dated[0]), project=project)
    assert not {"built_from", "feeds", "in_sync"} & set(plain["dataviews"][0])

    joined, _ = live_cli.ok("view", "create", str(tables.texty[0]), "--yes", project=project)
    parent = json.dumps({"dataset_id": tables.texty[0]})
    document = {
        "dataset_id": tables.texty[0],
        "foreign_view": tables.dated[1],
        "foreign_dataset_id": tables.dated[0],
        "join_type": "LEFT",
        "on": [{"left": "Sales", "right": "Sales"}],
        "select": ["Label"],
    }
    try:
        live_cli.ok(
            *("view", "transform", "join", str(joined["id"]), "--input", json.dumps(document)),
            *("--yes",),
            project=project,
        )
        feeder, _ = live_cli.ok("view", "list", str(tables.dated[0]), project=project)
        reader, _ = live_cli.ok("view", "list", str(tables.texty[0]), project=project)
    finally:
        live_cli.run(
            *("view", "delete", str(joined["id"]), "--yes", "--confirm", str(joined["id"])),
            *("--input", parent),
            project=project,
        )

    built = next(v for v in reader["dataviews"] if v["id"] == joined["id"])
    assert built["built_from"] == [tables.dated[1]]
    assert next(v for v in feeder["dataviews"] if v["id"] == tables.dated[1])["feeds"] == [
        joined["id"]
    ]


# -- view analyze ----------------------------------------------------------


def test_view_analyze_returns_the_view_and_its_step_count_with_the_findings(
    live_cli: LiveCli, tables: Tables
) -> None:
    dataset, view = tables.wide
    document = {"dataset_id": dataset, "n": 2}
    live_cli.ok(
        *("view", "transform", "limit-rows", str(view), "--input", json.dumps(document), "--yes"),
        project=tables.project,
    )
    try:
        data, _ = live_cli.ok("view", "analyze", str(view), str(dataset), project=tables.project)
    finally:
        steps, _ = live_cli.ok("view", "task", "list", str(view), project=tables.project)
        for step in steps["tasks"]:
            live_cli.ok(
                *("view", "task", "delete", str(view), str(step["id"]), "--yes"),
                *("--input", json.dumps({"dataset_id": dataset})),
                project=tables.project,
            )

    assert isinstance(data["findings"], list)
    assert data["steps"] == 1
    assert data["view"]["rows"] == 2
    assert data["view"]["columns"].startswith("Col 0:numeric, Col 1:numeric")
    assert data["view"]["dataset_name"]


def test_view_analyze_takes_several_ids_and_reports_each_failure_beside_the_rest(
    live_cli: LiveCli, tables: Tables
) -> None:
    ids = f"{tables.wide[1]},999999999"

    data, _ = live_cli.ok("view", "analyze", ids, str(tables.wide[0]), project=tables.project)

    assert data["requested"] == 2
    assert [a["view_id"] for a in data["analyses"]] == [tables.wide[1]]
    assert [e["view_id"] for e in data["errors"]] == [999999999]
    assert data["errors"][0]["code"]


def test_view_analyze_of_one_missing_view_still_fails_the_command(
    live_cli: LiveCli, tables: Tables
) -> None:
    error = live_cli.err(
        "view", "analyze", "999999999", str(tables.wide[0]), project=tables.project
    )

    assert error["code"]


# -- aggregate over dates --------------------------------------------------


def test_aggregate_over_a_date_column_states_the_dates_the_view_covers(
    live_cli: LiveCli, tables: Tables
) -> None:
    document = {
        "group_by": [{"column": "Order Date", "truncate": "MONTH"}],
        "aggregations": [{"function": "COUNT", "as_name": "orders"}],
    }

    envelope = _aggregate(live_cli, tables, tables.dated, document)

    coverage = envelope["data"]["coverage"]
    assert coverage["column"] == "Order Date"
    assert coverage["min"].startswith("2019-02-03")
    assert coverage["max"].startswith("2024-11-30")


def test_a_zero_metric_under_a_date_condition_reports_the_observed_range(
    live_cli: LiveCli, tables: Tables
) -> None:
    document = {
        "metric": {"column": "Sales", "function": "SUM"},
        "condition": {"column": "Order Date", "operator": "GTE", "value": "2030-01-01"},
    }

    data = _aggregate(live_cli, tables, tables.dated, document)["data"]

    assert "may mean no rows matched" in data["empty_result"]
    assert data["observed_range"][0]["max"].startswith("2024-11-30")


_BY_WEEKDAY: dict[str, Any] = {
    "group_by": [{"column": "Order Date", "part": "weekday"}],
    "aggregations": [{"column": "Sales", "function": "SUM", "as_name": "Total"}],
    "condition": {"column": "Order Date", "operator": "GTE", "value": "2024-01-01"},
}


def test_aggregate_by_weekday_of_a_date_column_names_and_orders_the_days(
    live_cli: LiveCli, tables: Tables
) -> None:
    only_january = {
        **_BY_WEEKDAY,
        "condition": {
            "column": "Order Date",
            "operator": "IN_RANGE",
            "value": ["2024-01-01", "2024-01-31"],
        },
    }

    data = _aggregate(live_cli, tables, tables.dated, only_january)["data"]

    assert data["data"] == [
        {"Order Date": "Tuesday", "Total": 400.0},
        {"Order Date": "Wednesday", "Total": 50.0},
        {"Order Date": "Saturday", "Total": 500.75},
    ]


def test_aggregate_by_weekday_ranks_the_named_days_with_order_by_and_top(
    live_cli: LiveCli, tables: Tables
) -> None:
    document = {
        **_BY_WEEKDAY,
        "condition": {
            "column": "Order Date",
            "operator": "IN_RANGE",
            "value": ["2024-01-01", "2024-01-31"],
        },
        "order_by": ["Total desc"],
        "top": 1,
    }

    data = _aggregate(live_cli, tables, tables.dated, document)["data"]

    assert data["data"] == [{"Order Date": "Saturday", "Total": 500.75}]


def test_a_date_part_on_a_numeric_column_is_refused_with_the_reason(
    live_cli: LiveCli, tables: Tables
) -> None:
    document = {**_BY_WEEKDAY, "group_by": [{"column": "Sales", "part": "weekday"}]}

    error = _aggregate(live_cli, tables, tables.dated, document)["error"]

    assert "'Sales' is NUMERIC" in error["message"]


# -- call_many -------------------------------------------------------------


def _read(tables: Tables, view_id: int) -> tuple[str, dict[str, Any]]:
    dataset = tables.wide[0]
    return _VIEW_SYMBOL, {
        "dataset_id": dataset,
        "dataview_id": view_id,
        "project_id": tables.project,
    }


def test_call_many_returns_a_failed_read_as_the_error_call_raises(tables: Tables) -> None:
    good, missing = _read(tables, tables.wide[1]), _read(tables, 999999999)

    with open_live_service(tables.project) as service:
        results = service.call_many([good, missing, ("mammoth.api.nope.Nothing.at_all", {})])
        with pytest.raises(CliError) as raised:
            service.call(missing[0], **missing[1])

    assert results[0]["id"] == tables.wide[1]
    assert isinstance(results[1], CliError) and isinstance(results[2], CliError)
    assert results[1].code == raised.value.code
    assert results[2].code == "sdk_symbol_unresolved"


def test_call_many_of_nothing_is_empty(tables: Tables) -> None:
    with open_live_service(tables.project) as service:
        assert service.call_many([]) == []


# -- upload preview --------------------------------------------------------


def test_a_clean_preview_carries_checks_and_an_empty_warning_list(tables: Tables) -> None:
    with open_live_service(tables.project) as service:
        preview = upload_preview(service, tables.wide[0], tables.project)

    assert "preview_error" not in preview
    assert preview["column_warnings"] == []
    assert preview["column_checks"]["rows_checked"] == 3
    assert preview["column_checks"]["found"] == 0
    assert "error" not in preview["column_checks"]


def test_a_failed_read_is_an_explicit_preview_error(tables: Tables) -> None:
    with open_live_service(tables.project) as service:
        preview = upload_preview(service, 999999999, tables.project)

    assert set(preview) == {"preview_error"}


def test_project_check_lists_the_datasets_it_checked(live_cli: LiveCli, tables: Tables) -> None:
    dataset, view = tables.dated

    data, _ = live_cli.ok(
        "project", "check", str(tables.project), str(dataset), project=tables.project
    )

    assert data["skipped"] == [], data
    assert data["checked"] == [
        {
            "dataset_id": dataset,
            "view_id": view,
            "view_name": data["checked"][0]["view_name"],
            "rows_checked": 6,
        }
    ]
    assert data["skipped"] == []
