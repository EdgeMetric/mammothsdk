"""``automation update`` with ``schedule`` (mammothsdk#381 item 7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import automation as automation_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_GET = "mammoth.api.automations.AutomationsAPI.get"
_UPDATE = "mammoth.api.automations.AutomationsAPI.update"
_WEEKLY_TUESDAY = {
    "frequency": "weekly",
    "interval": 1,
    "by_week_day": ["tu"],
    "start_at": "2026-11-10T07:00:00",
    "until": "2027-06-01T00:00:00",
    "start_now": False,
}


@pytest.fixture(autouse=True)
def _auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def _automation(*conditions: dict[str, Any]) -> dict[str, Any]:
    return {
        "automation": {
            "id": 574,
            "tasks": [
                {
                    "task_type": "run_data_retrieval",
                    "details": [{"ds_details": {"ds_id": 42}}, {"ds_details": {"ds_id": 43}}],
                }
            ],
            "conditions": (
                list(conditions)
                or [
                    {
                        "condition_type": "at_specific_time",
                        "condition_mode": "and",
                        "details": dict(_WEEKLY_TUESDAY),
                    }
                ]
            ),
        }
    }


def _update(tmp_path: Path, document: dict[str, Any]) -> Any:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(document), encoding="utf-8")
    return automation_cmd.automation_update(
        Invocation(
            command_id="automation.update",
            project=40,
            extra_args=["574"],
            input_file=str(doc),
            yes=True,
        )
    )


def test_a_schedule_change_keeps_the_datasets_and_starts_no_run(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """A details patch with only conditions is accepted and dropped; tasks go with it."""
    fake_service.responses[_GET] = _automation()
    fake_service.responses[_UPDATE] = {"id": 574}
    data, _meta = _update(
        tmp_path, {"schedule": {"by_week_day": ["mo"], "start_at": "2026-11-09T07:00:00"}}
    )
    (sent,) = [kwargs for symbol, kwargs in fake_service.call_log if symbol == _UPDATE]
    (patch,) = sent["patch"]
    assert patch["path"] == "details"
    value = patch["value"]
    assert value["tasks"] == [
        {
            "task_type": "run_data_retrieval",
            "details": {"ds_details": [{"ds_id": 42}, {"ds_id": 43}]},
        }
    ]
    (condition,) = value["conditions"]
    assert condition["details"] == {
        **_WEEKLY_TUESDAY,
        "by_week_day": ["mo"],
        "start_at": "2026-11-09T07:00:00",
        "start_now": False,
    }
    assert value["condition_mode"] == "and"
    assert data["schedule"]["by_week_day"] == ["mo"]


def test_a_dataset_option_beyond_ds_id_survives_a_schedule_change(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    stored = _automation()
    stored["automation"]["tasks"][0]["details"] = [
        {"ds_details": {"ds_id": 42, "sheet": "Q4"}},
        {"ds_details": {"ds_id": 43}},
    ]
    fake_service.responses[_GET] = stored
    fake_service.responses[_UPDATE] = {"id": 574}
    _update(tmp_path, {"schedule": {"by_week_day": ["mo"]}})
    (sent,) = [kwargs for symbol, kwargs in fake_service.call_log if symbol == _UPDATE]
    (task,) = sent["patch"][0]["value"]["tasks"]
    assert task["details"]["ds_details"] == [{"ds_id": 42, "sheet": "Q4"}, {"ds_id": 43}]


def test_a_refresh_and_export_automation_is_refused_not_stripped_of_the_export(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """The old code wrote a refresh-only tasks list, dropping the export from the body."""
    stored = _automation()
    stored["automation"]["tasks"].append(
        {"task_type": "run_exports", "details": {"trigger_ids": [12]}}
    )
    fake_service.responses[_GET] = stored
    with pytest.raises(CliError) as caught:
        _update(tmp_path, {"schedule": {"by_week_day": ["mo"]}})
    assert "run_exports" in caught.value.message
    assert _UPDATE not in fake_service.calls


@pytest.mark.parametrize(
    ("document", "words"),
    [
        ({"schedule": {"weekday": "mo"}}, "not ['weekday']"),
        ({"schedule": {}}, "must be an object"),
        ({"schedule": {"by_week_day": ["mo"]}, "add_datasets": [7]}, "schedule"),
    ],
)
def test_a_schedule_change_it_cannot_apply_is_refused_before_writing(
    fake_service: FakeMammothService, tmp_path: Path, document: dict[str, Any], words: str
) -> None:
    fake_service.responses[_GET] = _automation()
    with pytest.raises(CliError) as caught:
        _update(tmp_path, document)
    assert words in caught.value.message
    assert _UPDATE not in fake_service.calls


def test_a_patch_with_conditions_and_no_tasks_is_refused(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """The server answers it 200 and keeps the old schedule (gorakhpur, 11-03)."""
    patch = [{"op": "replace", "path": "details", "value": {"conditions": []}}]
    with pytest.raises(CliError) as caught:
        _update(tmp_path, {"patch": patch})
    assert "conditions but no tasks" in caught.value.message
    assert '"schedule"' in caught.value.hint
    assert _UPDATE not in fake_service.calls
