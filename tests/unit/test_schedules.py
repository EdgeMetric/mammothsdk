"""Unit tests for the SchedulesAPI client.

The backend's `/schedules` resource only ever supports the `pull_cloud_data`
work item (apiv2/apiv2/schedules/helper.py ALLOWED_TASK_RESOURCE_MAP) and its
`list_schedules` route is permanently unimplemented
(apiv2/apiv2/schedules/controller.py ScheduleController.list_schedules always
raises ClientError(not_implemented_error), HTTP 400) -- both confirmed by
reading the backend source, not a live call. See docs/release-status.md
2.0.46.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.automations import SchedulePatchItem
from mammoth.api.schedules import SchedulesAPI
from mammoth.exceptions import MammothValidationError
from mammoth.models.automations import (
    FirstPullAt,
    OnRefreshAction,
    PullDataExecutionParams,
    RruleFrequency,
    RruleSpec,
    ScheduleCreateSpec,
    SchedulePatchPath,
    SchedulePatchValue,
    ScheduleStatus,
    ScheduleType,
    WorkItemName,
    WorkItemSpec,
)


def _make_api() -> tuple[SchedulesAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 4
    mock_client.project_id = 101
    api = SchedulesAPI(mock_client)
    return api, mock_client


def _spec(**rrule_kwargs) -> ScheduleCreateSpec:
    rrule = RruleSpec(frequency=RruleFrequency.DAILY, start="2026-01-01T00:00:00Z", **rrule_kwargs)
    return ScheduleCreateSpec(
        rrule=rrule,
        work_items=[
            WorkItemSpec(
                name=WorkItemName.PULL_CLOUD_DATA,
                execution_params=PullDataExecutionParams(
                    schedule_type=ScheduleType.MOMENT,
                    first_pull_at=FirstPullAt.NOW,
                    on_refresh_action=OnRefreshAction.REPLACE,
                ),
                args=[123],
            )
        ],
    )


class TestCreate:
    def test_create_sends_rrule_and_work_items(self) -> None:
        api, mock_client = _make_api()
        api.create(_spec(interval=2))
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", "/workspaces/4/projects/101/schedules")
        body = kwargs["json"]
        assert body["rrule"]["frequency"] == "daily"
        assert body["rrule"]["interval"] == 2
        assert body["work_items"][0]["name"] == "pull_cloud_data"
        assert body["work_items"][0]["args"] == [123]

    def test_create_uses_explicit_project_id_over_client_default(self) -> None:
        api, mock_client = _make_api()
        api.create(_spec(), project_id=999)
        args, _ = mock_client._request_json.call_args
        assert args == ("POST", "/workspaces/4/projects/999/schedules")

    def test_create_nonpositive_project_id_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="project_id"):
            api.create(_spec(), project_id=0)

    def test_create_nonpositive_interval_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="interval"):
            api.create(_spec(interval=0))


class TestGet:
    def test_get(self) -> None:
        api, mock_client = _make_api()
        api.get(55)
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/4/projects/101/schedules/55"
        )


class TestList:
    def test_list_default_no_params(self) -> None:
        api, mock_client = _make_api()
        api.list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/4/projects/101/schedules", params=None
        )

    def test_list_forwards_limit_and_offset(self) -> None:
        api, mock_client = _make_api()
        api.list(limit=10, offset=5)
        _, kwargs = mock_client._request_json.call_args
        assert kwargs["params"] == {"limit": 10, "offset": 5}


class TestUpdate:
    def test_update_rrule_and_work_items(self) -> None:
        api, mock_client = _make_api()
        value = SchedulePatchValue(
            rrule=RruleSpec(frequency=RruleFrequency.WEEKLY, start="2026-02-01T00:00:00Z"),
            work_items=[
                WorkItemSpec(
                    name=WorkItemName.PULL_CLOUD_DATA,
                    execution_params=PullDataExecutionParams(
                        schedule_type=ScheduleType.PERIOD,
                        first_pull_at=FirstPullAt.LATER,
                        on_refresh_action=OnRefreshAction.APPEND,
                    ),
                    args=[1, 2],
                )
            ],
        )
        api.update(
            55, patch=[SchedulePatchItem(op="replace", path=SchedulePatchPath.RRULE, value=value)]
        )
        args, kwargs = mock_client._request_json.call_args
        assert args == ("PATCH", "/workspaces/4/projects/101/schedules/55")
        op = kwargs["json"]["patch"][0]
        assert op == {
            "op": "replace",
            "path": "rrule",
            "value": {
                "rrule": {"frequency": "weekly", "start": "2026-02-01T00:00:00+00:00"},
                "work_items": [
                    {
                        "name": "pull_cloud_data",
                        "execution_params": {
                            "schedule_type": "period",
                            "first_pull_at": "later",
                            "on_refresh_action": "append",
                        },
                        "args": [1, 2],
                    }
                ],
            },
        }

    def test_update_status_pause(self) -> None:
        api, mock_client = _make_api()
        api.update(
            55,
            patch=[
                SchedulePatchItem(
                    op="replace", path=SchedulePatchPath.STATUS, value=ScheduleStatus.PAUSE
                )
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"][0]["value"] == "pause"

    def test_update_status_resume(self) -> None:
        api, mock_client = _make_api()
        api.update(
            55,
            patch=[
                SchedulePatchItem(
                    op="replace", path=SchedulePatchPath.STATUS, value=ScheduleStatus.RESUME
                )
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"][0]["value"] == "resume"

    def test_update_empty_patch_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            api.update(55, patch=[])

    def test_update_nonpositive_schedule_id_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="schedule_id"):
            api.update(
                0,
                patch=[
                    SchedulePatchItem(
                        op="replace", path=SchedulePatchPath.STATUS, value=ScheduleStatus.PAUSE
                    )
                ],
            )


class TestDelete:
    def test_delete(self) -> None:
        api, mock_client = _make_api()
        api.delete(55)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/workspaces/4/projects/101/schedules/55"
        )
