"""``--dry-run`` runs the SDK-side checks and shows the body the SDK would send."""

from __future__ import annotations

import pytest
from mammoth.exceptions import MammothValidationError
from mammoth.models.automations import (
    AutomationConditionSpec,
    AutomationTaskSpec,
    ConditionDetailsSpec,
)

from mammoth_cli.runtime.dryrun import SDK_PREVIEWS, DryRunStop, make_gate
from mammoth_cli.services.mapping import map_sdk_exception

_CREATE = "mammoth.api.automations.AutomationsAPI.create"
_APPEND_TASK = {
    "task_type": "append_data",
    "details": {"destination_dataset_ids": [7], "source_folder_resource_id": 5},
}


def _create_arguments(condition_details: dict[str, object]) -> dict[str, object]:
    return {
        "name": "Folder append",
        "description": "",
        "tasks": [AutomationTaskSpec.model_validate(_APPEND_TASK)],
        "conditions": [
            AutomationConditionSpec(
                condition_type="at_specific_time",
                details=ConditionDetailsSpec.model_validate(condition_details),
            )
        ],
    }


def test_dry_run_of_automation_create_without_interval_and_start_at_fails_like_the_real_call():
    arguments = _create_arguments({"frequency": "daily"})
    with pytest.raises(MammothValidationError) as dry:
        make_gate("automation.create")(_CREATE, arguments)
    with pytest.raises(MammothValidationError) as real:
        SDK_PREVIEWS[_CREATE].check(arguments)  # the check is the SDK's own, run by both paths
    assert str(dry.value) == str(real.value)
    assert map_sdk_exception(dry.value).code == "invalid_arguments"


def test_dry_run_of_automation_create_with_interval_and_start_at_stops_with_a_report():
    arguments = _create_arguments(
        {"frequency": "daily", "interval": 1, "start_at": "2026-11-01T00:00:00Z"}
    )
    with pytest.raises(DryRunStop):
        make_gate("automation.create")(_CREATE, arguments)


def test_folder_append_dry_run_shows_only_what_the_server_would_receive():
    arguments = _create_arguments(
        {"interval": 1, "frequency": "daily", "start_at": "2026-11-01T00:00:00Z"}
    )
    with pytest.raises(DryRunStop) as stop:
        make_gate("automation.create")(_CREATE, arguments)
    body = stop.value.record["would_call"]["arguments"]["body"]
    details = body["conditions"][0]["details"]
    assert "on_refresh_action" not in details
    assert "action" not in body["tasks"][0]["details"]
    assert body["tasks"][0]["details"] == _APPEND_TASK["details"]
