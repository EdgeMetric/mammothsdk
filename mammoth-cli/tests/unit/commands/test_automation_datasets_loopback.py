"""``automation update add_datasets`` against the real SDK client and a loopback server (#328).

The server starts a refresh of every dataset when an automation's datasets are edited and the
automation has no recurrence rule (manual or no timing condition): ``validate_and_get_conditions``
sets ``start_now`` then and ``update_automation_details`` queues a run per task. Such an edit is
refused before anything is sent. This was seen on a dev server (release.mammoth.io): a raw edit of
a manual automation started the refreshes; the same edit of a daily one with ``start_now`` false
started none.
"""

# ruff: noqa: F811 -- the fixtures are imported and then named as test parameters

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands import automation_datasets
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.sdk_service import SdkMammothService
from tests.unit.commands.loopback_service import (
    API,
    PROJECT,
    Recorder,
    server,  # noqa: F401
    service,  # noqa: F401
)

AUTOMATION = 261
PATH = f"{API}/projects/{PROJECT}/automations/{AUTOMATION}"
DAILY = {
    "condition_mode": "and",
    "condition_type": "at_specific_time",
    "details": {"frequency": "daily", "interval": 1, "start_at": "2027-01-01T02:00:00"},
}
MANUAL = {
    "condition_mode": "and",
    "condition_type": "run_config",
    "details": {"trigger_type": "manual"},
}


def _automation(*conditions: dict[str, Any]) -> dict[str, Any]:
    """An automation as the server returns it (wrapped under ``automation``)."""
    return {
        "automation": {
            "id": AUTOMATION,
            "conditions": list(conditions),
            "tasks": [
                {
                    "task_type": "run_data_retrieval",
                    "details": [{"id": 254, "ds_details": {"ds_id": 14223}, "status": "idle"}],
                }
            ],
        }
    }


def _add(service: SdkMammothService, server: Recorder, *conditions: dict[str, Any]) -> list[Any]:
    """Read the automation, build the add-dataset patch, send it; the PATCH bodies received."""
    server.answers[("GET", PATH)] = _automation(*conditions)
    server.answers[("PATCH", PATH)] = {}
    current = service.call("mammoth.api.automations.AutomationsAPI.get", automation_id=AUTOMATION)
    patch, _ = automation_datasets.dataset_patch(
        automation_datasets.automation_record(current), [14226], []
    )
    service.call(
        "mammoth.api.automations.AutomationsAPI.update", automation_id=AUTOMATION, patch=patch
    )
    return server.bodies("PATCH", "/automations/")


def test_a_daily_automation_gets_the_dataset_with_start_now_false(
    service: SdkMammothService, server: Recorder
) -> None:
    (body,) = _add(service, server, DAILY)

    (patch,) = body["patch"]
    value = patch["value"]
    assert [d["ds_id"] for d in value["tasks"][0]["details"]["ds_details"]] == [14223, 14226]
    (condition,) = value["conditions"]
    assert condition["condition_type"] == "at_specific_time"
    assert condition["details"]["start_now"] is False
    assert value["condition_mode"] == "and"


@pytest.mark.parametrize(
    "conditions", [(MANUAL,), (), (MANUAL, DAILY)], ids=["manual", "no conditions", "manual+daily"]
)
def test_an_automation_the_server_would_run_is_refused_and_nothing_is_sent(
    service: SdkMammothService, server: Recorder, conditions: tuple[dict[str, Any], ...]
) -> None:
    with pytest.raises(CliError) as refused:
        _add(service, server, *conditions)

    assert refused.value.code == "invalid_argument"
    assert "no recurring schedule" in refused.value.message
    assert server.bodies("PATCH", "/automations/") == []
