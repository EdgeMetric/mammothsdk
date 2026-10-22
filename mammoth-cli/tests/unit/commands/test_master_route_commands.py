"""Commands for the server-master routes: dashboard drill, rows, describe-a-chart and chart
types; automation watched folders, file routing and run history; connector drafts.

Each dry run goes through the real CLI parser and handler and stops before the request leaves;
the handler tests run against the fake service.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DASHBOARDS = "mammoth.api.dashboards.DashboardsAPI"
_AUTOMATIONS = "mammoth.api.automations.AutomationsAPI"
_DRAFTS = "mammoth.api.connector_drafts.ConnectorDraftsAPI"
_ROWS = {"params": {"figure": "p1:add:t-1", "key": "West"}}
_DRILL = {"params": {"figure": "p1:add:t-1", "path": [{"key": "West"}]}}

# (argv, sdk_symbol, expected SDK arguments)
_DRY_RUNS: list[tuple[list[str], str, dict[str, Any]]] = [
    (
        ["dashboard", "figure", "drill", "7", "--input", json.dumps({"body": _DRILL})],
        f"{_DASHBOARDS}.figure_drill",
        {"dashboard_id": 7, "body": _DRILL},
    ),
    (
        ["dashboard", "published", "drill", "abc", "--input", json.dumps({"body": _DRILL})],
        f"{_DASHBOARDS}.published_drill",
        {"url": "abc", "body": _DRILL},
    ),
    (
        ["dashboard", "figure", "rows", "7", "--input", json.dumps({"body": _ROWS})],
        f"{_DASHBOARDS}.figure_rows",
        {"dashboard_id": 7, "body": _ROWS},
    ),
    (
        ["dashboard", "published", "rows", "abc", "--input", json.dumps({"body": _ROWS})],
        f"{_DASHBOARDS}.published_rows",
        {"url": "abc", "body": _ROWS},
    ),
    (
        [
            "dashboard",
            "figure",
            "recipe",
            "7",
            "--input",
            '{"body": {"params": {"describe": "Sales by region"}}}',
        ],
        f"{_DASHBOARDS}.figure_recipe",
        {"dashboard_id": 7, "body": {"params": {"describe": "Sales by region"}}},
    ),
    (["dashboard", "chart-type", "list"], f"{_DASHBOARDS}.chart_type_list", {}),
    (
        [
            "dashboard",
            "chart-type",
            "create",
            "--input",
            '{"body": {"params": {"name": "Bullet", "recipe": {"mark": "bar"}, "needs": []}}}',
        ],
        f"{_DASHBOARDS}.chart_type_create",
        {"body": {"params": {"name": "Bullet", "recipe": {"mark": "bar"}, "needs": []}}},
    ),
    (
        ["dashboard", "chart-type", "delete", "4", "--yes"],
        f"{_DASHBOARDS}.chart_type_delete",
        {"chart_type_id": "4"},
    ),
    (["automation", "folders"], f"{_AUTOMATIONS}.watched_folders", {}),
    (
        ["automation", "runs", "12", "--input", '{"limit": 5}'],
        f"{_AUTOMATIONS}.runs",
        {"automation_id": 12, "limit": 5},
    ),
    (
        ["automation", "route", "preview", "30", "--input", '{"names": ["a.csv"]}'],
        f"{_AUTOMATIONS}.preview_routes",
        {"folder_resource_id": 30, "names": ["a.csv"]},
    ),
    (
        ["automation", "route", "order", "30", "--input", '{"automation_ids": [12, 11]}'],
        f"{_AUTOMATIONS}.set_route_order",
        {"folder_resource_id": 30, "automation_ids": [12, 11]},
    ),
    (
        ["automation", "run-file", "add-anyway", "44", "--yes"],
        f"{_AUTOMATIONS}.add_run_file_anyway",
        {"run_file_id": 44},
    ),
    (
        ["connector", "draft", "list", "--input", '{"status": "all"}'],
        f"{_DRAFTS}.list",
        {"status": "all"},
    ),
    (
        ["connector", "draft", "create", "--input", '{"connector_key": "hubspot"}'],
        f"{_DRAFTS}.create",
        {"connector_key": "hubspot"},
    ),
    (["connector", "draft", "known-sources"], f"{_DRAFTS}.known_sources", {}),
    (["connector", "draft", "get", "9"], f"{_DRAFTS}.get", {"draft_id": 9}),
    (
        ["connector", "draft", "update", "9", "--input", '{"title": "Deals"}'],
        f"{_DRAFTS}.update",
        {"draft_id": 9, "title": "Deals"},
    ),
    (["connector", "draft", "discard", "9", "--yes"], f"{_DRAFTS}.discard", {"draft_id": 9}),
    (
        ["connector", "draft", "browse", "9", "--input", '{"folder": "root"}'],
        f"{_DRAFTS}.browse",
        {"draft_id": 9, "folder": "root"},
    ),
    (
        ["connector", "draft", "fill", "9", "--input", '{"column": "region", "dataset_id": 5}'],
        f"{_DRAFTS}.fill",
        {"draft_id": 9, "column": "region", "dataset_id": 5},
    ),
    (
        ["connector", "draft", "open", "9", "--input", '{"ref": "r1", "name": "Sales"}'],
        f"{_DRAFTS}.open",
        {"draft_id": 9, "ref": "r1", "name": "Sales"},
    ),
    (["connector", "draft", "read-tables", "9"], f"{_DRAFTS}.read_tables", {"draft_id": 9}),
    (
        ["connector", "draft", "sample", "9", "wanted.csv"],
        f"{_DRAFTS}.sample",
        {"draft_id": 9, "path": "wanted.csv"},
    ),
    (
        ["connector", "draft", "save", "9", "--input", '{"refresh": "daily"}'],
        f"{_DRAFTS}.save",
        {"draft_id": 9, "refresh": "daily"},
    ),
    (["connector", "draft", "source", "list", "9"], f"{_DRAFTS}.sources", {"draft_id": 9}),
    (
        ["connector", "draft", "source", "join-candidates", "9", "s2"],
        f"{_DRAFTS}.join_candidates",
        {"draft_id": 9, "source_id": "s2"},
    ),
    (
        ["connector", "draft", "source", "preview", "9", "s1", "--input", '{"limit": 3}'],
        f"{_DRAFTS}.preview_source",
        {"draft_id": 9, "source_id": "s1", "limit": 3},
    ),
]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture(autouse=True)
def _offline(fake_service: FakeMammothService, block_real_network: None) -> FakeMammothService:
    return fake_service


def test_every_one_of_the_28_routes_has_a_command() -> None:
    assert len(_DRY_RUNS) == 28


@pytest.mark.parametrize(("argv", "symbol", "arguments"), _DRY_RUNS, ids=lambda v: str(v)[:48])
def test_the_command_is_registered_and_its_dry_run_sends_the_expected_sdk_call(
    fake_service: FakeMammothService, argv: list[str], symbol: str, arguments: dict[str, Any]
) -> None:
    fake_service.responses[f"{_DASHBOARDS}.chart_type_list"] = {
        "chart_types": [{"id": "4", "name": "Lollipop"}]
    }
    record = next(
        r for r in (command_by_id(cid) for cid in HANDLERS) if r and r.get("sdk_symbol") == symbol
    )
    assert record["command_id"] in HANDLERS

    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])

    assert result.exit_code == 0, result.output
    call = json.loads(result.output)["data"]["would_call"]
    assert call["sdk_symbol"] == symbol
    assert {k: v for k, v in call["arguments"].items() if k in arguments} == arguments


@pytest.mark.parametrize(
    ("argv", "response", "named"),
    [
        (
            ["connector", "draft", "discard", "9"],
            ("connector_drafts.ConnectorDraftsAPI.get", {"id": 9, "title": "HubSpot deals"}),
            "connector draft \u201cHubSpot deals\u201d",
        ),
        (
            ["dashboard", "chart-type", "delete", "4"],
            (
                "dashboards.DashboardsAPI.chart_type_list",
                {"chart_types": [{"id": "4", "name": "Lollipop"}]},
            ),
            "chart type \u201cLollipop\u201d",
        ),
    ],
)
def test_a_delete_dry_run_names_what_it_would_remove(
    fake_service: FakeMammothService,
    argv: list[str],
    response: tuple[str, dict[str, Any]],
    named: str,
) -> None:
    fake_service.responses[f"mammoth.api.{response[0]}"] = response[1]

    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])

    assert result.exit_code == 0, result.output
    assert [t["name"] for t in json.loads(result.output)["data"]["targets"]] == [named]


def test_a_chart_type_that_is_not_listed_is_refused_with_the_list_command_to_check(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[f"{_DASHBOARDS}.chart_type_list"] = {"chart_types": []}

    result = make_runner().invoke(
        ["dashboard", "chart-type", "delete", "4", "--dry-run", "--output", "json"]
    )

    error = json.loads(result.output)["error"]
    assert error["code"] == "resource_not_found"
    assert "`mammoth dashboard chart-type list`" in error["hint"]


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "command_id",
    ["connector.draft.discard", "dashboard.chart-type.delete", "automation.run-file.add-anyway"],
)
def test_a_destructive_or_data_adding_command_refuses_without_yes(
    fake_service: FakeMammothService, command_id: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.generated_dashboard(_inv(command_id, extra_args=["9"], no_input=True))

    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_rows_keeps_the_handle_that_says_which_result_is_which(
    fake_service: FakeMammothService,
) -> None:
    handle = {
        "job_id": 35699,
        "descriptor_ids": {"rows": "r", "count": "c", "total": "t"},
        "columns": ["sales"],
        "applied_filters": [],
    }
    fake_service.responses[f"{_DASHBOARDS}.figure_rows"] = handle
    fake_service.job_result = {
        "completed": 3,
        "expected": 3,
        "results": {"r": {"data": [{"sales": 10.0}]}, "c": {"value": 1}, "t": {"value": 10.0}},
    }

    data, _ = dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.figure.rows",
            extra_args=["7"],
            input_file=json.dumps({"body": _ROWS}),
        )
    )

    assert fake_service.wait_log == [handle]
    assert data["descriptor_ids"] == handle["descriptor_ids"]
    assert data["columns"] == ["sales"]
    assert data["results"]["c"] == {"value": 1}


def test_a_published_rows_wait_reads_the_job_through_the_board_url(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[f"{_DASHBOARDS}.published_rows"] = {"job_id": 5}
    fake_service.job_result = {"results": {}}

    dashboard_cmd.generated_dashboard(
        _inv(
            "dashboard.published.rows",
            extra_args=["abc"],
            input_file=json.dumps({"body": _ROWS}),
        )
    )

    assert fake_service.wait_scopes == ["abc"]


def test_save_waits_for_its_job(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_DRAFTS}.save"] = {"job_id": 8}
    fake_service.job_result = {"status": "success"}

    data, _ = dashboard_cmd.generated_dashboard(
        _inv("connector.draft.save", extra_args=["9"], input_file='{"refresh": "manual"}')
    )

    assert fake_service.wait_log == [{"job_id": 8}]
    assert data == {"status": "success"}
