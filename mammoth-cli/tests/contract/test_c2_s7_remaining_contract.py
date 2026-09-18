"""Independent C2/S7 controls for the remaining command families.

The route ledger and representative values are authored outside the shared
resolver.  These tests prove that S7 handlers cross the shared binding
boundary, preserve distinctive optional values at the service seam, and reject
an unknown field before opening a service.  No network calls are made.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from mammoth_cli.commands import activity as activity_cmd
from mammoth_cli.commands import agent as agent_cmd
from mammoth_cli.commands import ai as ai_cmd
from mammoth_cli.commands import automation as automation_cmd
from mammoth_cli.commands import billing as billing_cmd
from mammoth_cli.commands import client_app as client_app_cmd
from mammoth_cli.commands import schedule as schedule_cmd
from mammoth_cli.commands import support as support_cmd
from mammoth_cli.commands import user as user_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.command_contract import S7_COMMANDS
from mammoth_cli.services.testing import FakeMammothService

LEDGER = Path(__file__).with_name("fixtures") / "C2-S7-ROUTES.json"

S7_ROUTE_INVENTORY = frozenset(
    {
        "activity.export",
        "activity.list",
        "agent.chat",
        "agent.session.delete",
        "agent.session.list",
        "agent.session.messages",
        "agent.session.set-visibility",
        "ai.condition.generate",
        "ai.expression.generate",
        "ai.sql.generate",
        "ai.suggestion.list",
        "automation.create",
        "automation.delete",
        "automation.get",
        "automation.list",
        "automation.restore",
        "automation.trash",
        "automation.update",
        "billing.chargebee-plan",
        "billing.hosted-page",
        "billing.invoice.charge",
        "billing.invoice.get",
        "billing.invoice.list",
        "billing.stripe.cancel",
        "billing.stripe.checkout-url",
        "billing.stripe.create",
        "billing.stripe.end-trial",
        "billing.stripe.get",
        "billing.stripe.history",
        "billing.stripe.payment-method.delete",
        "billing.stripe.payment-method.list",
        "billing.stripe.payment-method.set-default",
        "billing.stripe.portal-url",
        "billing.stripe.preview-invoice",
        "billing.stripe.retry-payment",
        "billing.stripe.status",
        "billing.stripe.sync",
        "billing.stripe.upcoming-invoice",
        "billing.stripe.usage",
        "billing.subscription.get",
        "billing.subscription.update",
        "client-app.create",
        "client-app.delete",
        "client-app.get",
        "client-app.list",
        "client-app.update",
        "schedule.create",
        "schedule.delete",
        "schedule.get",
        "schedule.list",
        "schedule.update",
        "support.connector-profile.add-connector",
        "support.connector-profile.create",
        "support.connector-profile.delete",
        "support.connector-profile.list",
        "support.connector-profile.update",
        "support.connector.create",
        "support.connector.delete",
        "support.connector.list",
        "support.connector.update",
        "support.feature-profile.add-feature",
        "support.feature-profile.create",
        "support.feature-profile.delete",
        "support.feature-profile.list",
        "support.feature-profile.update",
        "support.feature.create",
        "support.feature.delete",
        "support.feature.list",
        "support.feature.update",
        "support.ownership.transfer",
        "support.plan.archive",
        "support.plan.chargebee-list",
        "support.plan.create",
        "support.plan.delete",
        "support.plan.get",
        "support.plan.list",
        "support.plan.self-serve-list",
        "support.plan.update",
        "support.plan.update-storage-tiers",
        "support.subscription.create",
        "support.subscription.get",
        "support.subscription.update",
        "support.user.list-all",
        "support.user.register",
        "support.user.update",
        "support.workspace.create",
        "support.workspace.delete",
        "support.workspace.get",
        "support.workspace.list",
        "support.workspace.restore-access",
        "support.workspace.suspend-access",
        "support.workspace.update",
        "support.workspace.user.add",
        "support.workspace.user.list",
        "support.workspace.user.remove",
        "support.workspace.user.transfer",
        "user.avatar.delete",
        "user.avatar.upload",
        "user.change-password",
        "user.delete-account",
        "user.get",
        "user.preference.get",
        "user.preference.update",
        "user.update",
    }
)


def _inv(command_id: str, **overrides: Any) -> Invocation:
    return Invocation(command_id=command_id, **overrides)


def _write(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "s7-input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


@pytest.fixture
def fake_family_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    service = FakeMammothService()

    class _Context:
        def __enter__(self) -> tuple[FakeMammothService, SimpleNamespace]:
            return service, SimpleNamespace(workspace_id=4)

        def __exit__(self, *_args: object) -> None:
            return None

    def _open(_invocation: Invocation) -> _Context:
        return _Context()

    for module in (
        activity_cmd,
        agent_cmd,
        ai_cmd,
        automation_cmd,
        billing_cmd,
        client_app_cmd,
        schedule_cmd,
        support_cmd,
        user_cmd,
    ):
        monkeypatch.setattr(module, "open_service", _open)
    return service


def test_s7_inventory_and_ledger_are_exact() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert S7_COMMANDS == S7_ROUTE_INVENTORY
    assert ledger["route_count"] == 104
    assert ledger["families"] == {
        "activity": 2,
        "agent": 5,
        "ai": 4,
        "automation": 7,
        "billing": 23,
        "client-app": 5,
        "schedule": 5,
        "support": 45,
        "user": 8,
    }
    assert {route["command_id"] for route in ledger["routes"]} == S7_ROUTE_INVENTORY
    for route in ledger["routes"]:
        record = command_by_id(route["command_id"])
        assert record is not None
        assert route["sdk_symbol"] == record["sdk_symbol"]
        assert route["wire"]["method"] in {"GET", "POST", "PUT", "PATCH", "DELETE"}
        assert route["wire"]["path"].startswith("/")
        assert route["wire_verification"]["status"] == "unverified"
        assert route["wire_verification"]["executed_controls"] == []
        assert route["dropped_field_sentinel"] == "__s7_dropped_field__"
        for destination in route["field_destinations"].values():
            assert destination["destination"]


def test_unknown_s7_field_is_rejected_before_service_dispatch(
    fake_family_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as error:
        activity_cmd.activity_list(
            _inv(
                "activity.list",
                input_file=_write(tmp_path, {"limit": 913, "__s7_dropped_field__": "x"}),
            )
        )
    assert error.value.code == "unknown_input_field"
    assert fake_family_service.call_log == []


@pytest.mark.parametrize(
    (
        "handler",
        "command_id",
        "payload",
        "expected_symbol",
        "expected_kwargs",
        "extra_args",
        "extra",
    ),
    [
        (
            activity_cmd.activity_list,
            "activity.list",
            {
                "limit": 913,
                "offset": 17,
                "sort": "S7-ACTIVITY-SORT",
                "project_id": 42,
                "workspace_id": 99,
                "categories": ["S7-CATEGORY"],
                "activities": ["S7-ACTIVITY"],
                "resource_id": "S7-RESOURCE",
                "result": "S7-RESULT",
                "start_time": "S7-START",
                "end_time": "S7-END",
                "origin": "S7-ORIGIN",
                "user_ids": [73],
                "parent_id": 81,
                "search_text": "S7-SEARCH",
            },
            "mammoth.api.activity_logs.ActivityLogsAPI.list",
            {
                "limit": 913,
                "offset": 17,
                "sort": "S7-ACTIVITY-SORT",
                "project_id": 42,
                "categories": ["S7-CATEGORY"],
                "activities": ["S7-ACTIVITY"],
                "resource_id": "S7-RESOURCE",
                "result": "S7-RESULT",
                "start_time": "S7-START",
                "end_time": "S7-END",
                "origin": "S7-ORIGIN",
                "user_ids": [73],
                "parent_id": 81,
                "search_text": "S7-SEARCH",
            },
            [],
            {},
        ),
        (
            activity_cmd.activity_export,
            "activity.export",
            {
                "format": "S7-FORMAT",
                "workspace_id": 99,
                "start_time": "S7-START",
                "end_time": "S7-END",
                "categories": ["S7-CATEGORY"],
                "activities": ["S7-ACTIVITY"],
                "user_ids": [73],
            },
            "mammoth.api.activity_logs.ActivityLogsAPI.export",
            {
                "format": "S7-FORMAT",
                "start_time": "S7-START",
                "end_time": "S7-END",
                "categories": ["S7-CATEGORY"],
                "activities": ["S7-ACTIVITY"],
                "user_ids": [73],
            },
            [],
            {},
        ),
        (
            agent_cmd.agent_chat,
            "agent.chat",
            {
                "message": "S7-MESSAGE",
                "scope": {"project_id": 42},
                "agent_key": "S7-AGENT",
                "session_id": "S7-SESSION",
                "client_context": {"marker": "S7-CONTEXT"},
                "selection": {"marker": "S7-SELECTION"},
            },
            "mammoth.api.agents.AgentsAPI.chat",
            {
                "message": "S7-MESSAGE",
                "scope": {"project_id": 42},
                "agent_key": "S7-AGENT",
                "session_id": "S7-SESSION",
                "client_context": {"marker": "S7-CONTEXT"},
                    "selection": {"marker": "S7-SELECTION"},
            },
            [],
            {},
        ),
        (
            ai_cmd.ai_condition_generate,
            "ai.condition.generate",
            {"intent": "S7-INTENT", "dataview_id": 733, "sequence_number": 19},
            "mammoth.api.ai.AIAPI.condition_generate",
            {
                "intent": "S7-INTENT",
                "dataset_id": 931,
                "project_id": 42,
                "dataview_id": 733,
                "sequence_number": 19,
            },
            ["931"],
            {"project": 42},
        ),
        (
            automation_cmd.automation_create,
            "automation.create",
            {
                "name": "S7-AUTOMATION",
                "description": "S7-DESCRIPTION",
                    "tasks": [{"task_type": "send_an_alert"}],
                    "conditions": [{"condition_type": "run_config", "details": {}}],
                    "condition_mode": "and",
            },
            "mammoth.api.automations.AutomationsAPI.create",
            {
                "name": "S7-AUTOMATION",
                "description": "S7-DESCRIPTION",
                    "tasks": [{"task_type": "send_an_alert"}],
                    "conditions": [{"condition_type": "run_config", "details": {}}],
                    "condition_mode": "and",
            },
            [],
            {"yes": True},
        ),
        (
            billing_cmd.billing_stripe_preview_invoice,
            "billing.stripe.preview-invoice",
            {
                "connector_ids": "S7-CONNECTORS",
                "additional_storage_gb": 37,
                "additional_user_seats": 5,
            },
            "mammoth.api.billing.BillingAPI.stripe_preview_invoice",
            {
                "connector_ids": "S7-CONNECTORS",
                "additional_storage_gb": 37,
                "additional_user_seats": 5,
            },
            [],
            {"yes": True, "confirm": "4"},
        ),
        (
            client_app_cmd.client_app_list,
            "client-app.list",
            {"limit": 17, "offset": 3, "fields": "S7-FIELDS", "sort": "S7-SORT"},
            "mammoth.api.clientapps.ClientAppsAPI.list",
            {"limit": 17, "offset": 3, "fields": "S7-FIELDS", "sort": "S7-SORT"},
            [],
            {},
        ),
        (
            schedule_cmd.schedule_list,
            "schedule.list",
            {"limit": 23, "offset": 7},
            "mammoth.api.schedules.SchedulesAPI.list",
            {"project_id": 42, "limit": 23, "offset": 7},
            [],
            {"project": 42},
        ),
        (
            support_cmd.support_connector_update,
            "support.connector.update",
            {
                "name": "S7-CONNECTOR",
                "description": "S7-DESCRIPTION",
                "price_per_month": 17,
                "enabled": False,
            },
            "mammoth.api.support.SupportAPI.connector_update",
            {
                "connector_id": 941,
                "name": "S7-CONNECTOR",
                "description": "S7-DESCRIPTION",
                "price_per_month": 17,
                "enabled": False,
            },
            ["941"],
            {"yes": True, "confirm": "941"},
        ),
        (
            support_cmd.support_connector_create,
            "support.connector.create",
            {
                "name": "S7-DOCUMENT-NAME",
                "description": "S7-DESCRIPTION",
                "price_per_month": 17,
                "enabled": False,
            },
            "mammoth.api.support.SupportAPI.connector_create",
            {
                "name": "S7-POSITIONAL-NAME",
                "description": "S7-DESCRIPTION",
                "price_per_month": 17,
                "enabled": False,
            },
            ["S7-POSITIONAL-NAME"],
            {"yes": True, "confirm": "S7-POSITIONAL-NAME"},
        ),
        (
            user_cmd.user_preference_update,
            "user.preference.update",
            {"patch": [{"op": "replace", "path": "GLOBAL.PREFERENCES.S7", "value": "S7"}]},
            "mammoth.api.user_profile.UserProfileAPI.update_preferences",
            {"patch": [{"op": "replace", "path": "GLOBAL.PREFERENCES.S7", "value": "S7"}]},
            [],
            {},
        ),
        (
            user_cmd.user_update,
            "user.update",
            {"name": "S7-NAME", "email": "s7@example.com"},
            "mammoth.api.user_profile.UserProfileAPI.update",
            {"name": "S7-NAME", "email": "s7@example.com"},
            [],
            {"yes": True, "confirm": "4"},
        ),
    ],
)
def test_s7_distinctive_fields_reach_the_reviewed_sdk_destination(
    handler: Any,
    command_id: str,
    payload: dict[str, Any],
    expected_symbol: str,
    expected_kwargs: dict[str, Any],
    extra_args: list[str],
    extra: dict[str, Any],
    fake_family_service: FakeMammothService,
    tmp_path: Path,
) -> None:
    invocation = _inv(
        command_id,
        input_file=_write(tmp_path, payload),
        extra_args=extra_args,
        **extra,
    )
    handler(invocation)
    assert fake_family_service.call_log == [(expected_symbol, expected_kwargs)]
