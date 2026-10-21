"""Commands added for agent access, the held plan change, plan entitlements, connection overview
and test, task preview cancel, tool claims, dashboard chat attachments and unpublished changes:
argv to request, and the guarded ones.

Each dry run goes through the real CLI parser and handler and stops before the request leaves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import billing as billing_cmd
from mammoth_cli.commands import dashboard as dashboard_cmd
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_AGENTS = "mammoth.api.agents.AgentsAPI"
_BILLING = "mammoth.api.billing.BillingAPI"
_SUPPORT = "mammoth.api.support.SupportAPI"
_CONNECTORS = "mammoth.api.connectors.ConnectorsAPI"
_PIPELINE = "mammoth.api.pipeline.PipelineAPI"
_DATASETS = "mammoth.api.datasets.DatasetsAPI"
_DASHBOARDS = "mammoth.api.dashboards.DashboardsAPI"

# (argv, sdk_symbol, expected SDK arguments)
_DRY_RUNS: list[tuple[list[str], str, dict[str, Any]]] = [
    (["agent", "access", "me"], f"{_AGENTS}.access_me", {}),
    (["agent", "access", "settings", "get"], f"{_AGENTS}.access_settings_get", {}),
    (
        ["agent", "access", "settings", "update", "--input", '{"downloads": true}'],
        f"{_AGENTS}.access_settings_update",
        {"downloads": True},
    ),
    (["agent", "access", "grant", "list"], f"{_AGENTS}.access_grants_list", {}),
    (
        [
            "agent",
            "access",
            "grant",
            "give",
            "--input",
            '{"emails": ["a@example.com"], "level": "ask", "items": [{"project_id": 3}]}',
            "--yes",
        ],
        f"{_AGENTS}.access_grant_give",
        {"emails": ["a@example.com"], "level": "ask", "items": [{"project_id": 3}]},
    ),
    (
        ["agent", "access", "grant", "update", "4", "--input", '{"level": "explore"}'],
        f"{_AGENTS}.access_grant_update",
        {"grant_id": 4, "level": "explore"},
    ),
    (
        ["agent", "access", "people", "--input", '{"search": "ana"}'],
        f"{_AGENTS}.access_people",
        {"search": "ana"},
    ),
    (["agent", "access", "tree"], f"{_AGENTS}.access_tree", {}),
    (["agent", "access", "askers", "12"], f"{_AGENTS}.access_project_askers", {"project_id": 12}),
    (
        ["agent", "access", "reach", "--input", '{"user_id": 5}'],
        f"{_AGENTS}.access_reach",
        {"user_id": 5},
    ),
    (
        ["agent", "access", "request", "list", "--input", '{"status": "open"}'],
        f"{_AGENTS}.access_requests_list",
        {"status": "open"},
    ),
    (
        ["agent", "access", "request", "mine", "sess-1"],
        f"{_AGENTS}.access_requests_mine",
        {"session_id": "sess-1"},
    ),
    (
        [
            "agent",
            "access",
            "request",
            "create",
            "--input",
            '{"kind": "access", "text": "Please share Sales"}',
        ],
        f"{_AGENTS}.access_request_create",
        {"kind": "access", "text": "Please share Sales"},
    ),
    (
        ["agent", "access", "request", "resolve", "8", "--input", '{"status": "done"}'],
        f"{_AGENTS}.access_request_resolve",
        {"request_id": 8, "status": "done"},
    ),
    (
        ["agent", "access", "request", "add-to-context", "8"],
        f"{_AGENTS}.access_request_add_to_context",
        {"request_id": 8},
    ),
    (
        [
            "agent",
            "access",
            "chart",
            "save",
            "sess-1",
            "turn-1",
            "--input",
            '{"new_dashboard_name": "Revenue"}',
        ],
        f"{_AGENTS}.access_chart_save",
        {"session_id": "sess-1", "turn_id": "turn-1", "new_dashboard_name": "Revenue"},
    ),
    (
        ["agent", "session", "feedback", "list", "sess-1"],
        f"{_AGENTS}.turn_feedback_list",
        {"session_id": "sess-1"},
    ),
    (
        ["agent", "turn", "rate", "sess-1", "turn-1", "--input", '{"rating": "down"}'],
        f"{_AGENTS}.turn_rate",
        {"session_id": "sess-1", "turn_id": "turn-1", "rating": "down"},
    ),
    (["billing", "stripe", "held-change", "get"], f"{_BILLING}.stripe_held_change_get", {}),
    (
        ["billing", "stripe", "held-change", "cancel", "--yes", "--confirm", "4"],
        f"{_BILLING}.stripe_held_change_cancel",
        {},
    ),
    (
        [
            "support",
            "plan",
            "update-entitlements",
            "3",
            "--input",
            '{"values": {"sso": true}}',
            "--yes",
            "--confirm",
            "3",
        ],
        f"{_SUPPORT}.plan_update_entitlements",
        {"plan_id": 3, "values": {"sso": True}},
    ),
    (
        ["connector", "connection", "list-all", "--input", '{"limit": 10}'],
        f"{_CONNECTORS}.list_all_connections",
        {"limit": 10},
    ),
    (
        ["connector", "connection", "test", "prod-warehouse"],
        f"{_CONNECTORS}.test_connection",
        {"connection_key": "prod-warehouse"},
    ),
    (
        ["view", "task", "preview-cancel", "12", "44"],
        f"{_PIPELINE}.preview_cancel",
        {"dataview_id": 12, "job_id": 44},
    ),
    (
        ["dataset", "tool-claim", "get", "--input", '{"token": "tok"}'],
        f"{_DATASETS}.tool_claim_get",
        {"token": "***REDACTED***"},
    ),
    (
        ["dataset", "tool-claim", "redeem", "--input", '{"token": "tok"}'],
        f"{_DATASETS}.tool_claim_redeem",
        {"token": "***REDACTED***"},
    ),
    (["dashboard", "unpublished", "12"], f"{_DASHBOARDS}.unpublished", {"dashboard_id": 12}),
]

_COMMAND_IDS = [
    "agent.access.me",
    "agent.access.settings.get",
    "agent.access.settings.update",
    "agent.access.grant.list",
    "agent.access.grant.give",
    "agent.access.grant.update",
    "agent.access.grant.revoke",
    "agent.access.people",
    "agent.access.tree",
    "agent.access.askers",
    "agent.access.reach",
    "agent.access.request.list",
    "agent.access.request.mine",
    "agent.access.request.create",
    "agent.access.request.resolve",
    "agent.access.request.add-to-context",
    "agent.access.chart.save",
    "agent.session.feedback.list",
    "agent.turn.rate",
    "billing.stripe.held-change.get",
    "billing.stripe.held-change.cancel",
    "support.plan.update-entitlements",
    "connector.connection.list-all",
    "connector.connection.test",
    "view.task.preview-cancel",
    "dataset.tool-claim.get",
    "dataset.tool-claim.redeem",
    "dashboard.chat.attachment.upload",
    "dashboard.unpublished",
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


def test_every_command_but_two_has_a_dry_run_case() -> None:
    """The upload reads a local file and the revoke reads the grants: handler tests cover them."""
    assert len(_DRY_RUNS) == len(_COMMAND_IDS) - 2


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


def test_revoke_dry_run_names_the_grant_it_would_remove(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_AGENTS}.access_grants_list"] = [
        {"id": 4, "user": {"email": "ana@example.com"}, "level": "ask", "items": []}
    ]
    result = make_runner().invoke(
        ["agent", "access", "grant", "revoke", "4", "--yes", "--dry-run", "--output", "json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["would_call"]["sdk_symbol"] == f"{_AGENTS}.access_grant_revoke"
    assert data["would_call"]["arguments"] == {"grant_id": 4}
    assert data["targets"][0]["id"] == 4
    assert "ana@example.com" in data["targets"][0]["name"]
    assert all(symbol != f"{_AGENTS}.access_grant_revoke" for symbol, _ in fake_service.call_log)


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_held_change_cancel_refuses_without_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_held_change_cancel(_inv("billing.stripe.held-change.cancel"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_held_change_cancel_needs_the_workspace_as_confirm_target(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        billing_cmd.billing_stripe_held_change_cancel(
            _inv("billing.stripe.held-change.cancel", yes=True)
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_held_change_get_reads_without_confirmation(fake_service: FakeMammothService) -> None:
    fake_service.responses[f"{_BILLING}.stripe_held_change_get"] = {"held": None}
    data, _ = billing_cmd.billing_stripe_held_change_get(_inv("billing.stripe.held-change.get"))
    assert data == {"held": None}
    assert fake_service.call_log[0][0] == f"{_BILLING}.stripe_held_change_get"


def test_attachment_upload_rejects_a_missing_file(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        dashboard_cmd.dashboard_chat_attachment_upload(
            _inv(
                "dashboard.chat.attachment.upload",
                extra_args=["12", str(tmp_path / "missing.pdf")],
            )
        )
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.call_log == []


def test_attachment_upload_sends_the_dashboard_and_file(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")
    fake_service.responses[f"{_DASHBOARDS}.chat_attachment_upload"] = {"ref": "att:abc"}
    data, _ = dashboard_cmd.dashboard_chat_attachment_upload(
        _inv("dashboard.chat.attachment.upload", extra_args=["12", str(path)])
    )
    assert data == {"ref": "att:abc"}
    symbol, kwargs = fake_service.call_log[0]
    assert symbol == f"{_DASHBOARDS}.chat_attachment_upload"
    assert kwargs == {"dashboard_id": 12, "file": str(path)}
