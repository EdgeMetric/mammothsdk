"""``view export update`` keeps the schedule and send window the server would reset (#348).

The server rewrites ``additional_properties`` from the request's top-level ``schedule`` and
``send_window`` and deregisters the export's ScheduleJob when a save carries neither, so the
merge must lift the stored ones out of ``additional_properties``. The service is the real SDK
client against a loopback server; the PATCH body it receives is what is asserted. The same
shape was seen on a dev server (release.mammoth.io) with a scheduled export.
"""

# ruff: noqa: F811 -- the fixtures are imported and then named as test parameters

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands.view import export_update
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.sdk_service import SdkMammothService
from tests.unit.commands.loopback_service import (
    API,
    PROJECT,
    Recorder,
    server,  # noqa: F401
    service,  # noqa: F401
)

VIEW, DATASET, EXPORT = 20, 77, 9
EXPORT_PATH = (
    f"{API}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/exports/{EXPORT}"
)
SCHEDULE = {
    "frequency": "daily",
    "interval": 1,
    "start_now": False,
    "start_at": "2027-01-01T02:00:00",
}
SEND_WINDOW = {"frequency": "weekly", "interval": 1, "by_week_day": ["MO"]}


def _stored(**extra: Any) -> dict[str, Any]:
    """A scheduled email export as ``view export get`` returns it (schedule in the properties)."""
    return {
        "id": EXPORT,
        "status": "executed",
        "handler_type": "email",
        "trigger_type": "schedule",
        "end_of_pipeline": True,
        "sequence": 4,
        "target_properties": {"TO": ["a@example.com"]},
        "additional_properties": {"note": "kept", "schedule": SCHEDULE},
        "condition": {},
        **extra,
    }


def _windowed(window: dict[str, Any] = SEND_WINDOW, **extra: Any) -> dict[str, Any]:
    """An email export on a pipeline trigger with a send window (what the server accepts)."""
    return _stored(
        trigger_type="pipeline",
        additional_properties={
            "note": "kept",
            "send_window": window,
            "send_window_pending_since": "2026-10-28T00:00:00",
        },
        **extra,
    )


def _update(
    service: SdkMammothService, server: Recorder, changes: dict[str, Any], **stored: Any
) -> dict[str, Any]:
    """Read the export, merge ``changes`` over it, send the edit; the value PATCHed."""
    server.answers[("GET", EXPORT_PATH)] = _stored(**stored)
    return _update_stored(service, server, changes)


def _update_stored(
    service: SdkMammothService, server: Recorder, changes: dict[str, Any]
) -> dict[str, Any]:
    """Merge ``changes`` over the export the server already holds; the value PATCHed."""
    server.answers[("PATCH", EXPORT_PATH)] = {}
    export = service.call(
        "mammoth.api.exports.ExportsAPI.get",
        dataview_id=VIEW,
        export_id=EXPORT,
        project_id=PROJECT,
        dataset_id=DATASET,
        fields="__full",
    )
    patches = export_update.normalize_patches(
        export_update.shorthand_patches(changes), dict(export), VIEW
    )
    service.call(
        "mammoth.api.exports.ExportsAPI.update",
        dataview_id=VIEW,
        export_id=EXPORT,
        patches=patches,
        project_id=PROJECT,
        dataset_id=DATASET,
    )
    (body,) = server.bodies("PATCH", "/exports/")
    (patch,) = body["patches"]
    value: dict[str, Any] = patch["value"]
    return value


def test_the_stored_schedule_goes_back_as_a_top_level_field(
    service: SdkMammothService, server: Recorder
) -> None:
    value = _update(service, server, {"save_as_mode": "REPLACE_IN_DS"})

    assert value["schedule"] == SCHEDULE
    assert "send_window" not in value
    # Not left inside additional_properties, where the server strips it.
    assert value["additional_properties"] == {"note": "kept"}
    assert value["target_properties"]["SAVE_AS_DS_MODE"] == "REPLACE_IN_DS"
    assert value["trigger_type"] == "schedule"
    assert value["sequence"] is None and value["end_of_pipeline"] is True


def test_a_schedule_the_caller_gives_replaces_the_stored_one(
    service: SdkMammothService, server: Recorder
) -> None:
    new = {"frequency": "hourly", "interval": 2}

    value = _update(service, server, {"schedule": new} | {"end_of_pipeline": True})

    assert value["schedule"] == new


def test_an_export_without_a_schedule_sends_none(
    service: SdkMammothService, server: Recorder
) -> None:
    value = _update(
        service,
        server,
        {"trigger_type": "pipeline"},
        trigger_type="pipeline",
        additional_properties={"note": "kept"},
    )

    assert "schedule" not in value and "send_window" not in value
    assert value["additional_properties"] == {"note": "kept"}


def test_a_sequence_without_end_of_pipeline_false_is_refused(
    service: SdkMammothService, server: Recorder
) -> None:
    with pytest.raises(CliError) as refused:
        _update(service, server, {"sequence": 3})

    assert refused.value.code == "invalid_argument"
    assert server.bodies("PATCH", "/exports/") == []


def test_a_sequence_with_end_of_pipeline_false_unpins_the_export(
    service: SdkMammothService, server: Recorder
) -> None:
    value = _update(service, server, {"sequence": 3, "end_of_pipeline": False})

    assert value["sequence"] == 3 and value["end_of_pipeline"] is False


def test_additional_properties_given_without_a_schedule_keep_the_stored_one(
    service: SdkMammothService, server: Recorder
) -> None:
    value = _update(service, server, {"additional_properties": {"note": "new"}})

    assert value["additional_properties"] == {"note": "new"}
    assert value["schedule"] == SCHEDULE


def test_a_null_schedule_from_the_caller_removes_it(
    service: SdkMammothService, server: Recorder
) -> None:
    value = _update(service, server, {"schedule": None})

    assert value["schedule"] is None


def test_the_stored_send_window_goes_back_without_the_held_send_state(
    service: SdkMammothService, server: Recorder
) -> None:
    server.answers[("GET", EXPORT_PATH)] = _windowed()
    value = _update_stored(service, server, {"save_as_mode": "REPLACE_IN_DS"})

    assert value["send_window"] == SEND_WINDOW
    assert "schedule" not in value
    assert value["additional_properties"] == {"note": "kept"}
    assert value["trigger_type"] == "pipeline"


def test_a_stored_schedule_that_has_ended_is_refused_not_resent(
    service: SdkMammothService, server: Recorder
) -> None:
    ended = {**SCHEDULE, "start_now": True, "until": "2020-01-01T00:00:00"}

    with pytest.raises(CliError) as refused:
        _update(
            service,
            server,
            {"save_as_mode": "REPLACE_IN_DS"},
            additional_properties={"schedule": ended},
        )

    assert refused.value.code == "invalid_argument"
    assert "schedule" in str(refused.value) and "until" in str(refused.value)
    assert server.bodies("PATCH", "/exports/") == []


def test_a_new_until_from_the_caller_replaces_an_ended_one(
    service: SdkMammothService, server: Recorder
) -> None:
    ended = {**SCHEDULE, "start_now": True, "until": "2020-01-01T00:00:00"}
    renewed = {**SCHEDULE, "start_now": True, "until": "2999-01-01T00:00:00"}

    value = _update(
        service, server, {"schedule": renewed}, additional_properties={"schedule": ended}
    )

    assert value["schedule"] == renewed


def test_a_stored_schedule_with_a_future_until_is_still_carried(
    service: SdkMammothService, server: Recorder
) -> None:
    open_ended = {**SCHEDULE, "start_now": True, "until": "2999-01-01T00:00:00"}

    value = _update(
        service,
        server,
        {"save_as_mode": "REPLACE_IN_DS"},
        additional_properties={"schedule": open_ended},
    )

    assert value["schedule"] == open_ended


def test_a_stored_send_window_that_has_ended_is_refused_not_resent(
    service: SdkMammothService, server: Recorder
) -> None:
    ended = {**SEND_WINDOW, "until": "2020-01-01T00:00:00"}
    server.answers[("GET", EXPORT_PATH)] = _windowed(ended)

    with pytest.raises(CliError) as refused:
        _update_stored(service, server, {"save_as_mode": "REPLACE_IN_DS"})

    assert refused.value.code == "invalid_argument"
    assert "send_window" in str(refused.value) and "until" in str(refused.value)
    assert server.bodies("PATCH", "/exports/") == []
