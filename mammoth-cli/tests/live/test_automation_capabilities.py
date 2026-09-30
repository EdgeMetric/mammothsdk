"""Live check: the CLI says what automations support, PDF included.

An agent once told a user that automations do not support PDF. The create
schema named the task types but nothing said what each one reads or writes.
``automation capabilities`` asks the server, which derives the answer from the
schemas it validates a create with. Runs the real CLI in-process against a real
tenant (no doubles) inside a scratch project it deletes afterwards.

    pytest tests/live/test_automation_capabilities.py -m live -v
"""

from __future__ import annotations

from typing import Any

import pytest
from live_harness import LiveCli
from mammoth.models.automations import AutomationConditionType, AutomationTaskType

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def capabilities(live_cli: LiveCli, scratch_project: int) -> dict[str, Any]:
    data, _ = live_cli.ok("automation", "capabilities", project=scratch_project)
    assert isinstance(data, dict)
    return data


def _by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {row[key]: row for row in rows}


def test_pdf_is_listed_as_a_file_format_automations_read(capabilities: dict[str, Any]) -> None:
    tasks = _by(capabilities["tasks"], "task_type")
    assert "pdf" in tasks["append_data"]["formats_in"]


def test_email_attachments_are_listed_as_csv_only(capabilities: dict[str, Any]) -> None:
    tasks = _by(capabilities["tasks"], "task_type")
    assert tasks["send_an_alert"]["formats_out"] == ["csv"]
    assert tasks["send_an_alert"]["options"]["alert_type"] == ["email"]


def test_every_task_and_trigger_the_sdk_can_create_is_listed(capabilities: dict[str, Any]) -> None:
    assert {t["task_type"] for t in capabilities["tasks"]} == {e.value for e in AutomationTaskType}
    assert {c["condition_type"] for c in capabilities["conditions"]} == {
        e.value for e in AutomationConditionType
    }


def test_schedule_options_come_from_the_server(capabilities: dict[str, Any]) -> None:
    schedule = _by(capabilities["conditions"], "condition_type")["at_specific_time"]
    assert "weekly" in schedule["options"]["frequency"]
    assert "mo" in schedule["options"]["by_week_day"]
