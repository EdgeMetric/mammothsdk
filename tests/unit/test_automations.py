"""Unit tests for the AutomationsAPI client.

Wire-contract assertions here are checked against the mvc-service backend
source (apiv2/apiv2/automations/{controller,schema,utils}.py) rather than a
live server, since a live koyal automation-get round trip is currently
blocked by a separate backend defect (see docs/release-status.md 2.0.46).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.automations import AutomationsAPI
from mammoth.exceptions import MammothValidationError
from mammoth.models.automations import (
    AutomationConditionSpec,
    AutomationConditionType,
    AutomationPatchItem,
    AutomationPatchOp,
    AutomationPatchPath,
    AutomationStatus,
    AutomationTaskSpec,
    AutomationTaskType,
    ConditionDetailsSpec,
    DataRefreshConfig,
    PatchAutomationDetails,
    TaskDetailsSpec,
)


def _make_api() -> tuple[AutomationsAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 4
    mock_client.project_id = 101
    api = AutomationsAPI(mock_client)
    return api, mock_client


class TestCreate:
    def test_create_run_data_retrieval_with_recurrence(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        api.create(
            name="Nightly refresh",
            description="",
            tasks=[
                AutomationTaskSpec(
                    task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
                    details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=42)]),
                )
            ],
            conditions=[
                AutomationConditionSpec(
                    condition_type=AutomationConditionType.AT_SPECIFIC_TIME,
                    details=ConditionDetailsSpec(
                        interval=1, frequency="daily", start_at="2026-01-01T00:00:00Z"
                    ),
                )
            ],
        )
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", "/workspaces/4/projects/101/automations")
        body = kwargs["json"]
        assert body["tasks"][0]["task_type"] == "run_data_retrieval"
        assert body["tasks"][0]["details"]["ds_details"] == [{"ds_id": 42}]
        assert body["conditions"][0]["condition_type"] == "at_specific_time"
        assert body["conditions"][0]["details"]["interval"] == 1

    @pytest.mark.parametrize(
        ("task_type", "details_kwargs"),
        [
            (
                AutomationTaskType.APPEND_DATA,
                {"destination_dataset_ids": [1], "source_dataset_id": 2},
            ),
            (
                AutomationTaskType.SEND_AN_ALERT,
                {"alert_type": "email", "recipients": ["a@b.com"], "subject": "hi"},
            ),
            (
                AutomationTaskType.PULL_CLOUD_FILES,
                {
                    "connector_key": "google_drive",
                    "connection_key": "conn",
                    "cloud_source_folder_path": "folder",
                    "destination_folder_resource_id": 5,
                },
            ),
        ],
    )
    def test_create_accepts_every_required_task_type(self, task_type, details_kwargs) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        api.create(
            name="x",
            description="",
            tasks=[
                AutomationTaskSpec(task_type=task_type, details=TaskDetailsSpec(**details_kwargs))
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["tasks"][0]["task_type"] == task_type.value

    def test_create_run_data_retrieval_missing_ds_details_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="ds_details"):
            api.create(
                name="x",
                description="",
                tasks=[
                    AutomationTaskSpec(
                        task_type=AutomationTaskType.RUN_DATA_RETRIEVAL, details=None
                    )
                ],
            )


class TestGet:
    def test_get(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"automation": {"id": 7}}
        result = api.get(7)
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/4/projects/101/automations/7"
        )
        assert result == {"automation": {"id": 7}}


class TestList:
    def test_list_unwraps_automations_key(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"automations": [{"id": 1}], "next": ""}
        result = api.list()
        mock_client._request_json.assert_called_once_with(
            "GET", "/workspaces/4/projects/101/automations"
        )
        assert result == [{"id": 1}]


class TestDelete:
    def test_delete(self) -> None:
        api, mock_client = _make_api()
        api.delete(7)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/workspaces/4/projects/101/automations/7"
        )


class TestTrashRestore:
    def test_trash(self) -> None:
        api, mock_client = _make_api()
        api.trash(7)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/4/projects/101/automations/7/trash"
        )

    def test_restore(self) -> None:
        api, mock_client = _make_api()
        api.restore(7)
        mock_client._request_json.assert_called_once_with(
            "POST", "/workspaces/4/projects/101/automations/7/restore"
        )


class TestUpdate:
    def test_update_command_run(self) -> None:
        api, mock_client = _make_api()
        api.update(
            7,
            patch=[
                AutomationPatchItem(
                    op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.RUN, value={}
                )
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"] == [{"op": "command", "path": "run", "value": {}}]

    def test_update_status_suspend_sends_suspend_on_the_wire(self) -> None:
        api, mock_client = _make_api()
        api.update(
            7,
            patch=[
                AutomationPatchItem(
                    op=AutomationPatchOp.REPLACE,
                    path=AutomationPatchPath.STATUS,
                    value=AutomationStatus.SUSPEND.value,
                )
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"][0]["value"] == "suspend"

    def test_update_status_resume_sends_restore_on_the_wire(self) -> None:
        """The backend's status vocabulary is 'suspend'/'restore', not
        'suspend'/'resume' (apiv2/apiv2/automations/schema.py
        AutomationStatusValueEnum, enforced in
        AutomationPatchData.validate_data). The SDK keeps the friendlier
        'resume' as its own public value -- matching ScheduleStatus's
        'pause'/'resume' vocabulary -- and must translate it to 'restore' on
        the wire. Sending 'resume' verbatim gets rejected by the backend with
        invalid_status_to_update (400), so an agent's automation-enable
        never applies.
        """
        api, mock_client = _make_api()
        api.update(
            7,
            patch=[
                AutomationPatchItem(
                    op=AutomationPatchOp.REPLACE,
                    path=AutomationPatchPath.STATUS,
                    value=AutomationStatus.RESUME.value,
                )
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"][0]["value"] == "restore"

    def test_update_details_patch(self) -> None:
        api, mock_client = _make_api()
        api.update(
            7,
            patch=[
                AutomationPatchItem(
                    op=AutomationPatchOp.REPLACE,
                    path=AutomationPatchPath.DETAILS,
                    value=PatchAutomationDetails(name="new name"),
                )
            ],
        )
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"][0]["value"] == {"name": "new name"}

    def test_update_details_patch_from_raw_dict_value(self) -> None:
        """``AutomationPatchItem.value`` is typed ``str | dict[str, Any] |
        PatchAutomationDetails``. Constructing the item straight from a typed
        ``PatchAutomationDetails`` (the test above) never exercises pydantic's
        union resolution; every real caller -- the CLI's ``--input`` JSON, and
        ``mammoth_cli.embed.invoke``'s dict-shaped request document -- builds
        the item from a plain dict via ``model_validate``/``TypeAdapter``.
        Pydantic's default "smart" union mode picks the exact ``dict[str,
        Any]`` match over coercing into ``PatchAutomationDetails`` (which
        needs nested-model construction), so ``item.value`` came back a bare
        dict and ``_validate_automation_patch_item``'s
        ``isinstance(item.value, PatchAutomationDetails)`` check failed --
        rejecting every details patch (rename, description, tasks, conditions)
        with "must include at least one of: name, description, tasks,
        conditions" even when a field was set. Reproduced live on koyal
        (mammoth-cli 2.0.46): ``automation update ID --input
        '{"patch": [{"op": "replace", "path": "details", "value":
        {"name": "..."}}]}'``.
        """
        api, mock_client = _make_api()
        item = AutomationPatchItem.model_validate(
            {"op": "replace", "path": "details", "value": {"name": "new name"}}
        )
        api.update(7, patch=[item])
        body = mock_client._request_json.call_args.kwargs["json"]
        assert body["patch"][0]["value"] == {"name": "new name"}

    def test_update_empty_patch_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="patch"):
            api.update(7, patch=[])

    def test_update_nonpositive_id_raises(self) -> None:
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="automation_id"):
            api.update(
                0,
                patch=[
                    AutomationPatchItem(
                        op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.RUN, value={}
                    )
                ],
            )
