"""What the automation routes take, held to the routes as they stand.

The SDK's automation models were written by hand against an earlier shape of
these routes and drifted from them: a whole task type went missing, the
status patch carried a word the route refuses, and two commands had no path.
"""

from unittest.mock import AsyncMock, MagicMock

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
    TaskDetailsSpec,
)


def _api() -> tuple[AutomationsAPI, MagicMock]:
    client = MagicMock()
    client.workspace_id = 3
    client.project_id = 5
    client._request_json = AsyncMock(return_value={"id": 9})
    return AutomationsAPI(client), client


async def _create(task: AutomationTaskSpec) -> dict:
    api, client = _api()
    await api.create("nightly", "", [task])
    return client._request_json.call_args.kwargs["json"]


async def test_an_automation_can_apply_a_retention_policy() -> None:
    # The route has taken this task type for a while; the SDK knew four types
    # and this was not one of them.
    body = await _create(
        AutomationTaskSpec(
            task_type=AutomationTaskType.APPLY_RETENTION_POLICY,
            details=TaskDetailsSpec(datasource_id=12, rule_type="count_based", keep_count=5),
        )
    )

    assert body["tasks"] == [
        {
            "task_type": "apply_retention_policy",
            "details": {"datasource_id": 12, "rule_type": "count_based", "keep_count": 5},
        }
    ]


async def test_a_retention_policy_with_no_rule_is_refused() -> None:
    api, client = _api()
    task = AutomationTaskSpec(
        task_type=AutomationTaskType.APPLY_RETENTION_POLICY,
        details=TaskDetailsSpec(datasource_id=12),
    )

    with pytest.raises(MammothValidationError, match="retention"):
        await api.create("nightly", "", [task])

    client._request_json.assert_not_called()


async def test_a_count_based_policy_must_say_how_many_to_keep() -> None:
    api, client = _api()
    task = AutomationTaskSpec(
        task_type=AutomationTaskType.APPLY_RETENTION_POLICY,
        details=TaskDetailsSpec(datasource_id=12, rule_type="count_based"),
    )

    with pytest.raises(MammothValidationError, match="retention"):
        await api.create("nightly", "", [task])

    client._request_json.assert_not_called()


async def test_appending_into_no_dataset_yet_reaches_the_route() -> None:
    # The route asks only that the field be there; an empty list is its
    # business, not the SDK's.
    body = await _create(
        AutomationTaskSpec(
            task_type=AutomationTaskType.APPEND_DATA,
            details=TaskDetailsSpec(destination_dataset_ids=[], source_dataset_id=4),
        )
    )

    assert body["tasks"][0]["details"]["destination_dataset_ids"] == []


async def test_a_cloud_folder_may_be_named_by_more_than_a_path() -> None:
    # A connector that identifies a folder by id and path sends both.
    body = await _create(
        AutomationTaskSpec(
            task_type=AutomationTaskType.PULL_CLOUD_FILES,
            details=TaskDetailsSpec(
                connector_key="google_drive",
                connection_key="k",
                cloud_source_folder_path={"id": "abc", "path": "/Sales"},
                destination_folder_resource_id=7,
            ),
        )
    )

    assert body["tasks"][0]["details"]["cloud_source_folder_path"] == {
        "id": "abc",
        "path": "/Sales",
    }


async def test_starting_a_suspended_automation_again_says_restore() -> None:
    # The route takes "suspend" or "restore". "resume" is what the SDK sent,
    # and the route has never accepted it.
    api, client = _api()

    await api.update(
        9,
        [
            AutomationPatchItem(
                op=AutomationPatchOp.REPLACE,
                path=AutomationPatchPath.STATUS,
                value=AutomationStatus.RESTORE.value,
            )
        ],
    )

    assert client._request_json.call_args.kwargs["json"] == {
        "patch": [{"op": "replace", "path": "status", "value": "restore"}]
    }


@pytest.mark.parametrize(
    "path", [AutomationPatchPath.APPROVE_RETENTION, AutomationPatchPath.REJECT_RETENTION]
)
async def test_a_retention_run_is_approved_or_rejected_by_command(
    path: AutomationPatchPath,
) -> None:
    api, client = _api()

    await api.update(9, [AutomationPatchItem(op=AutomationPatchOp.COMMAND, path=path, value="")])

    assert client._request_json.call_args.kwargs["json"] == {
        "patch": [{"op": "command", "path": path.value, "value": {}}]
    }


async def test_a_condition_cannot_ask_for_an_execution_mode_the_route_refuses() -> None:
    with pytest.raises(ValueError, match="execution_mode"):
        ConditionDetailsSpec(execution_mode="whenever")


async def test_a_condition_keeps_the_route_s_own_defaults() -> None:
    api, client = _api()
    condition = AutomationConditionSpec(
        condition_type=AutomationConditionType.RUN_CONFIG, details=ConditionDetailsSpec()
    )

    await api.create(
        "nightly",
        "",
        [
            AutomationTaskSpec(
                task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
                details=TaskDetailsSpec(ds_details=[{"ds_id": 1}]),
            )
        ],
        conditions=[condition],
    )

    # Nothing was set, so nothing is sent and the route applies its own.
    assert client._request_json.call_args.kwargs["json"]["conditions"] == [
        {"condition_type": "run_config", "details": {}}
    ]
