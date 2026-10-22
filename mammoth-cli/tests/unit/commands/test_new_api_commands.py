"""Commands added for export runs, REST fill, export hosts, view summary, workflow undo and
duplicate, email updates, live charts and oEmbed: argv to request, and the guarded ones.

Each dry run goes through the real CLI parser and handler and stops before the request leaves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands import workflow as workflow_cmd
from mammoth_cli.commands import workspace as workspace_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_EXPORTS = "mammoth.api.exports.ExportsAPI"
_WORKFLOWS = "mammoth.api.workflows.WorkflowsAPI"
_COLLECTIONS = "mammoth.api.collections.CollectionsAPI"
_DASHBOARDS = "mammoth.api.dashboards.DashboardsAPI"

# (argv, sdk_symbol, expected SDK arguments)
_DRY_RUNS: list[tuple[list[str], str, dict[str, Any]]] = [
    (
        ["view", "export", "runs", "12", "34", "456", "--input", '{"limit": 5}'],
        f"{_EXPORTS}.runs",
        {"dataview_id": 12, "export_id": 34, "dataset_id": 456, "limit": 5, "project_id": 25654},
    ),
    (
        [
            "view",
            "export",
            "rest-fill",
            "12",
            "456",
            "--input",
            '{"docs_url": "https://api.example.com/docs", "notes": "bearer auth"}',
            "--yes",
        ],
        f"{_EXPORTS}.rest_fill",
        {
            "dataview_id": 12,
            "docs_url": "https://api.example.com/docs",
            "notes": "bearer auth",
            "dataset_id": 456,
            "project_id": 25654,
        },
    ),
    (
        ["view", "summary", "12", "456"],
        "mammoth.api.dataviews.DataviewsAPI.summary",
        {"dataset_id": 456, "dataview_id": 12, "project_id": 25654},
    ),
    (["workspace", "export-hosts", "get"], f"{_EXPORTS}.export_hosts", {}),
    (
        [
            "workspace",
            "export-hosts",
            "set",
            "--input",
            '{"restricted": true, "hosts": ["api.example.com"]}',
            "--yes",
        ],
        f"{_EXPORTS}.set_export_hosts",
        {"restricted": True, "hosts": ["api.example.com"]},
    ),
    (
        [
            "workflow",
            "duplicate",
            "7",
            "--input",
            '{"name": "Copy", "dataset_ids": [1, 2]}',
        ],
        f"{_WORKFLOWS}.duplicate",
        {
            "name": "Copy",
            "dataset_ids": [1, 2],
            "source_workflow_id": 7,
            "project_id": 25654,
        },
    ),
    (
        ["workflow", "save-cancel-step", "7", "run-1", "3"],
        f"{_WORKFLOWS}.cancel_save_step",
        {"workflow_id": 7, "run_id": "run-1", "step": 3, "project_id": 25654},
    ),
    (
        ["collection", "email-updates", "get", "9"],
        f"{_COLLECTIONS}.email_updates",
        {"collection_id": 9},
    ),
    (
        [
            "collection",
            "email-updates",
            "set",
            "9",
            "--input",
            '{"enabled": true, "timezone": "UTC"}',
            "--yes",
        ],
        f"{_COLLECTIONS}.set_email_updates",
        {"collection_id": 9, "enabled": True, "timezone": "UTC"},
    ),
    (
        ["collection", "email-updates", "me", "get", "9"],
        f"{_COLLECTIONS}.my_email_updates",
        {"collection_id": 9},
    ),
    (
        ["collection", "email-updates", "me", "set", "9", "--input", '{"subscribed": false}'],
        f"{_COLLECTIONS}.set_my_email_updates",
        {"collection_id": 9, "subscribed": False},
    ),
    (
        ["collection", "email-updates", "test", "9", "--yes"],
        f"{_COLLECTIONS}.send_test_email_update",
        {"collection_id": 9},
    ),
    (["dashboard", "email-updates", "list"], f"{_DASHBOARDS}.email_updates_list", {}),
    (
        ["dashboard", "email-updates", "get", "5"],
        f"{_DASHBOARDS}.email_updates_get",
        {"dashboard_id": 5},
    ),
    (
        [
            "dashboard",
            "email-updates",
            "set",
            "5",
            "--input",
            '{"body": {"enabled": true, "timezone": "UTC"}}',
            "--yes",
        ],
        f"{_DASHBOARDS}.email_updates_set",
        {"dashboard_id": 5, "body": {"enabled": True, "timezone": "UTC"}},
    ),
    (
        ["dashboard", "email-updates", "me", "get", "5"],
        f"{_DASHBOARDS}.email_updates_me_get",
        {"dashboard_id": 5},
    ),
    (
        [
            "dashboard",
            "email-updates",
            "me",
            "set",
            "5",
            "--input",
            '{"body": {"subscribed": true}}',
        ],
        f"{_DASHBOARDS}.email_updates_me_set",
        {"dashboard_id": 5, "body": {"subscribed": True}},
    ),
    (
        ["dashboard", "email-updates", "test", "5", "--yes"],
        f"{_DASHBOARDS}.email_updates_test",
        {"dashboard_id": 5},
    ),
    (
        ["dashboard", "live-chart", "list", "sess-1"],
        f"{_DASHBOARDS}.live_chart_list",
        {"session_id": "sess-1"},
    ),
    (
        [
            "dashboard",
            "live-chart",
            "create",
            "--input",
            '{"body": {"params": {"view_id": 12, "title": "Revenue", "figure": {}}}}',
        ],
        f"{_DASHBOARDS}.live_chart_create",
        # #280: --project reaches the request (it was dropped).
        {
            "body": {"params": {"view_id": 12, "title": "Revenue", "figure": {}}},
            "project_id": 25654,
        },
    ),
    (
        ["dashboard", "live-chart", "get", "5"],
        f"{_DASHBOARDS}.live_chart_get",
        {"dashboard_id": 5},
    ),
    (
        [
            "dashboard",
            "live-chart",
            "audience",
            "5",
            "--input",
            '{"body": {"params": {"audience": "workspace"}}}',
            "--yes",
            "--confirm",
            "5",
        ],
        f"{_DASHBOARDS}.live_chart_audience",
        {"dashboard_id": 5, "body": {"params": {"audience": "workspace"}}},
    ),
    (
        ["dashboard", "live-chart", "usage", "5"],
        f"{_DASHBOARDS}.live_chart_usage",
        {"dashboard_id": 5},
    ),
    (
        [
            "dashboard",
            "live-chart",
            "placement",
            "5",
            "--input",
            '{"body": {"params": {"dashboard_id": 6, "figure_id": "fig1"}}}',
        ],
        f"{_DASHBOARDS}.live_chart_placement",
        {"dashboard_id": 5, "body": {"params": {"dashboard_id": 6, "figure_id": "fig1"}}},
    ),
    (
        ["dashboard", "oembed", "--input", '{"url": "https://app.mammoth.io/d/x"}'],
        f"{_DASHBOARDS}.oembed",
        {"url": "https://app.mammoth.io/d/x"},
    ),
]

_COMMAND_IDS = [
    "view.export.runs",
    "view.export.rest-fill",
    "view.summary",
    "workspace.export-hosts.get",
    "workspace.export-hosts.set",
    "workflow.duplicate",
    "workflow.save-undo",
    "workflow.save-cancel-step",
    "collection.email-updates.get",
    "collection.email-updates.set",
    "collection.email-updates.me.get",
    "collection.email-updates.me.set",
    "collection.email-updates.test",
    "dashboard.email-updates.list",
    "dashboard.email-updates.get",
    "dashboard.email-updates.set",
    "dashboard.email-updates.me.get",
    "dashboard.email-updates.me.set",
    "dashboard.email-updates.test",
    "dashboard.live-chart.list",
    "dashboard.live-chart.create",
    "dashboard.live-chart.get",
    "dashboard.live-chart.audience",
    "dashboard.live-chart.usage",
    "dashboard.live-chart.placement",
    "dashboard.oembed",
]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.mark.parametrize("command_id", _COMMAND_IDS)
def test_the_command_is_registered_and_reachable_from_the_cli(command_id: str) -> None:
    assert command_id in HANDLERS
    record = command_by_id(command_id)
    assert record is not None
    result = make_runner().invoke([*record["command_path"].split(), "--help"])
    assert result.exit_code == 0


def test_every_new_command_but_save_undo_has_a_dry_run_case() -> None:
    """Save undo is destructive: its dry run reads the workflow, so a handler test covers it."""
    assert len(_DRY_RUNS) == len(_COMMAND_IDS) - 1


@pytest.mark.parametrize(("argv", "symbol", "arguments"), _DRY_RUNS, ids=lambda v: str(v)[:40])
def test_dry_run_sends_the_expected_sdk_call(
    argv: list[str], symbol: str, arguments: dict[str, Any]
) -> None:
    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["dry_run"] is True and data["ran"] is False
    call = data["would_call"]
    assert call["sdk_symbol"] == symbol
    assert {k: v for k, v in call["arguments"].items() if k in arguments} == arguments


# -- handlers against the fake service ----------------------------------------------------


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, object]) -> str:
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_rest_fill_refuses_without_yes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_rest_fill(
            _inv(
                "view.export.rest-fill",
                project=180,
                extra_args=["12", "456"],
                input_file=_doc(tmp_path, {"docs_url": "https://api.example.com/docs"}),
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_rest_fill_returns_the_suggestion(fake_service: FakeMammothService, tmp_path: Path) -> None:
    symbol = f"{_EXPORTS}.rest_fill"
    fake_service.responses[symbol] = {"status": "completed", "response": {"suggestion": {"a": 1}}}
    data, _ = view_cmd.view_export_rest_fill(
        _inv(
            "view.export.rest-fill",
            project=180,
            yes=True,
            extra_args=["12", "456"],
            input_file=_doc(tmp_path, {"docs_url": "https://api.example.com/docs"}),
        )
    )
    assert data["suggestion"] == {"a": 1}


def test_export_hosts_set_refuses_without_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_export_hosts_set(
            _inv(
                "workspace.export-hosts.set",
                input_file=_doc(tmp_path, {"restricted": False}),
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_export_hosts_set_requires_restricted(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        workspace_cmd.workspace_export_hosts_set(
            _inv("workspace.export-hosts.set", yes=True, input_file=_doc(tmp_path, {"hosts": []}))
        )
    assert excinfo.value.code == "missing_field"


def test_save_undo_refuses_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_save_undo(
            _inv("workflow.save-undo", project=180, extra_args=["7", "run-1"])
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_save_cancel_step_rejects_a_negative_step(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_save_cancel_step(
            _inv("workflow.save-cancel-step", project=180, extra_args=["7", "run-1", "-1"])
        )
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_duplicate_surfaces_the_new_workflow_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[f"{_WORKFLOWS}.duplicate"] = {
        "status": "completed",
        "response": {"workflow_id": 99},
    }
    data, _ = workflow_cmd.workflow_duplicate(
        _inv(
            "workflow.duplicate",
            project=180,
            extra_args=["7"],
            input_file=_doc(tmp_path, {"name": "Copy", "dataset_ids": [1]}),
        )
    )
    assert data["workflow_id"] == 99
    assert fake_service.call_log[0][1]["source_workflow_id"] == 7


def test_duplicate_requires_name_and_datasets(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        workflow_cmd.workflow_duplicate(
            _inv("workflow.duplicate", project=180, input_file=_doc(tmp_path, {"name": "Copy"}))
        )
    assert excinfo.value.code == "missing_field"


def test_export_runs_forwards_limit_and_parent(fake_service: FakeMammothService) -> None:
    view_cmd.view_export_runs(_inv("view.export.runs", project=180, extra_args=["12", "34", "456"]))
    symbol, kwargs = fake_service.call_log[0]
    assert symbol == f"{_EXPORTS}.runs"
    assert kwargs["dataview_id"] == 12 and kwargs["export_id"] == 34
    assert kwargs["dataset_id"] == 456


def test_save_undo_waits_for_the_undo_run(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_WORKFLOWS}.undo_save"] = {"status": "undone"}
    data, _ = workflow_cmd.workflow_save_undo(
        _inv("workflow.save-undo", project=180, yes=True, extra_args=["7", "run-1"])
    )
    assert data["status"] == "undone"
    assert fake_service.call_log[0] == (
        f"{_WORKFLOWS}.undo_save",
        {"workflow_id": 7, "run_id": "run-1", "project_id": 180},
    )


def test_live_chart_create_waits_for_its_bake_and_keeps_the_dashboard_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # #281: a 202 with a bake job was returned raw: no wait, no readback.
    from mammoth.models.dashboard_generated import CreateLiveChartResponse

    from mammoth_cli.commands import dashboard as dashboard_cmd

    fake_service.responses[f"{_DASHBOARDS}.live_chart_create"] = CreateLiveChartResponse(
        dashboard_id=99, job_id=12
    )
    fake_service.job_result = {"status": "success"}
    doc = _doc(tmp_path, {"body": {"params": {"view_id": 12, "title": "Revenue", "figure": {}}}})
    data, _ = dashboard_cmd.generated_dashboard(_inv("dashboard.live-chart.create", input_file=doc))
    assert fake_service.wait_log == [{"dashboard_id": 99, "job_id": 12}]
    assert data == {"dashboard_id": 99, "job_id": 12, "status": "success"}
