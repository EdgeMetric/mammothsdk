"""What an automation task needs, as Mammoth itself says it."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool

PROJECT = 3
CAPABILITIES = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/automations/capabilities"
ALERT = {
    "task_type": "send_an_alert",
    "summary": "Email recipients with the selected views attached as CSV files.",
    "required_fields": ["alert_type", "recipients", "subject", "attachments"],
    "optional_fields": ["message"],
    "options": {},
}
SCHEDULE = {"condition_type": "schedule", "summary": "At a time.", "fields": ["start_at"]}


def test_a_task_types_schema_is_what_mammoth_says_it_takes() -> None:
    # Mammoth builds this from the schemas it checks a create with, so it
    # cannot go stale the way a written example does.
    with a_fake_api() as api, as_caller():
        api.answer("GET", CAPABILITIES, {"tasks": [ALERT], "conditions": [SCHEDULE]})
        schema = call_tool(
            "get_schema",
            kind="automation",
            of="send_an_alert",
            workspace_id=WORKSPACE,
            project_id=PROJECT,
        )

    assert schema == {"task": ALERT, "conditions": [SCHEDULE]}


def test_an_automation_schema_names_the_project_it_is_for() -> None:
    # Mammoth answers it per project, so the call needs one.
    with (
        a_fake_api() as api,
        as_caller(),
        pytest.raises(ToolError, match="project_id"),
    ):
        call_tool("get_schema", kind="automation", of="send_an_alert", workspace_id=WORKSPACE)

    assert not api.requests


def test_an_unknown_task_type_names_the_ones_there_are() -> None:
    with a_fake_api() as api, as_caller():
        api.answer("GET", CAPABILITIES, {"tasks": [ALERT], "conditions": []})
        with pytest.raises(ToolError, match="send_an_alert"):
            call_tool(
                "get_schema",
                kind="automation",
                of="send_a_fax",
                workspace_id=WORKSPACE,
                project_id=PROJECT,
            )
