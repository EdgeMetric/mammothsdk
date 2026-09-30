"""Unit tests for ALL API sub-clients — verifies each method calls the correct
HTTP method, endpoint, and parameters.

Tests every public method on every API sub-client:
  ProjectsAPI, DatasetsAPI, DataviewsAPI, PipelineAPI, FilesAPI, FoldersAPI,
  JobsAPI, ExportsAPI, ConnectorsAPI, DashboardsAPI, AutomationsAPI,
  SchedulesAPI, BatchesAPI, BrowseAPI, ClientAppsAPI, ExternalKeysAPI,
  ActivityLogsAPI, AddonsAPI, ReportsAPI, UserProfileAPI, WorkspaceAPI, AIAPI
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mammoth.api.automations import SchedulePatchItem
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from mammoth.models.automations import (
    AlertType,
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
    FirstPullAt,
    OnRefreshAction,
    PatchAutomationDetails,
    PullDataExecutionParams,
    RruleFrequency,
    RruleSpec,
    ScheduleCreateSpec,
    SchedulePatchPath,
    SchedulePatchValue,
    ScheduleStatus,
    ScheduleType,
    TaskDetailsSpec,
    WorkItemName,
    WorkItemSpec,
)
from mammoth.models.connectors import DsConfigPatchOp, DsConfigPatchPath
from mammoth.models.dashboards import (
    CreateBlankParams,
    DashboardActionType,
    DashboardAuthType,
    DashboardPatchItem,
    DashboardPatchOp,
    DashboardPatchPath,
    DashboardShareRole,
    DashboardShareUser,
)
from mammoth.models.exports import OdbcType
from mammoth.models.external_keys import ExternalKeyType, ModelConfigSpec
from mammoth.models.projects import DataSyncPatchItem
from mammoth.models.workspaces import (
    BillingCycle,
    UserRolePatchOp,
    WorkspacePatchOp,
    WorkspacePatchPath,
    WorkspaceRoleType,
)

# ── Shared Fixtures ──────────────────────────────────────────────


@pytest.fixture
def client() -> MammothClient:
    """MammothClient with mocked session and _request_json/_request_list."""
    with patch("mammoth.client.httpx.AsyncClient"):
        c = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
    c.project_id = 100
    c._request_json = AsyncMock(return_value={})
    c._request_list = AsyncMock(return_value=[])
    c._request = AsyncMock(return_value={})
    c._wait_if_job = AsyncMock(side_effect=lambda r, **kw: r)
    return c


# ── Helper ──────────────────────────────────────────────────────


def assert_called_with_method_and_endpoint(
    mock: MagicMock, method: str, endpoint_substring: str
) -> None:
    """Assert the mock was called with given HTTP method and endpoint contains substring."""
    mock.assert_called_once()
    args = mock.call_args
    assert args[0][0] == method, f"Expected HTTP {method}, got {args[0][0]}"
    assert (
        endpoint_substring in args[0][1]
    ), f"Expected endpoint containing '{endpoint_substring}', got '{args[0][1]}'"


def assert_json_body(mock: MagicMock, expected: dict) -> None:
    """Assert the mock's last call sent exactly *expected* as the JSON body.

    Pins the full request payload (not a subset) so a renamed/dropped/extra key
    is caught — the regression guard the route-only assertions above can't give.
    """
    body = mock.call_args.kwargs.get("json")
    assert body == expected, f"Expected JSON body {expected}, got {body}"


# ======================================================================
# ProjectsAPI
# ======================================================================


class TestProjectsAPI:
    async def test_list(self, client: MammothClient):
        await client.projects.list()
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects"
        )

    async def test_get_by_id(self, client: MammothClient):
        # await projects.get() calls list() internally and filters
        client._request_json = AsyncMock(
            return_value={"projects": [{"id": 42, "name": "Test Project"}]}
        )
        result = await client.projects.get(project=42)
        assert result["id"] == 42
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects"
        )

    async def test_create(self, client: MammothClient):
        await client.projects.create(name="New Project")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/workspaces/1/projects"
        )

    async def test_update(self, client: MammothClient):
        # ProjectPatch: ``patches`` with bare-name paths; colour lives in properties.
        await client.projects.update(project_id=42, name="Renamed", color="#123456")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/projects/42")
        assert_json_body(
            client._request_json,
            {
                "patches": [
                    {"op": "replace", "path": "name", "value": "Renamed"},
                    {"op": "replace", "path": "properties", "value": {"color": "#123456"}},
                ]
            },
        )

    async def test_delete(self, client: MammothClient):
        await client.projects.delete(project_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/workspaces/1/projects/42"
        )

    async def test_browse(self, client: MammothClient):
        await client.projects.browse(project_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/projects/42/browse")

    async def test_add_users(self, client: MammothClient):
        # AddUsersToProject: ``users`` of {user_id, role}; ids are numeric.
        await client.projects.add_users(project_id=42, user_ids=[5, "6"], role="project_analyst")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/projects/42/users")
        assert_json_body(
            client._request_json,
            {
                "users": [
                    {"user_id": 5, "role": "project_analyst"},
                    {"user_id": 6, "role": "project_analyst"},
                ]
            },
        )

    async def test_add_users_rejects_emails(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="numeric user ids"):
            await client.projects.add_users(project_id=42, user_ids=["someone@example.com"])
        client._request_json.assert_not_called()

    async def test_remove_users(self, client: MammothClient):
        await client.projects.remove_users(project_id=42, user_ids=["u1"])
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/projects/42/users")

    async def test_bulk_update(self, client: MammothClient):
        await client.projects.bulk_update(patch_data={"name": "x"})
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/workspaces/1/projects"
        )

    async def test_bulk_delete(self, client: MammothClient):
        await client.projects.bulk_delete(project_ids=[1, 2])
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/workspaces/1/projects"
        )

    async def test_checkpoint_list(self, client: MammothClient):
        await client.projects.checkpoint_list(project_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects/42/checkpoints"
        )

    async def test_checkpoint_list_rejects_non_positive_project_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.projects.checkpoint_list(project_id=0)

    async def test_data_check_list(self, client: MammothClient):
        await client.projects.data_check_list(project_id=42, dataview_id=7, status="pending")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects/42/data-checks"
        )
        assert client._request_json.call_args.kwargs["params"] == {
            "dataview_id": 7,
            "status": "pending",
        }

    async def test_pending_changes(self, client: MammothClient):
        await client.projects.pending_changes(project_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects/42/pending-changes"
        )

    async def test_list_agent_memory(self, client: MammothClient):
        client._request_json.return_value = {
            "projects": [
                {"id": 7, "properties": {"agent_memory": ["other"]}},
                {"id": 42, "properties": {"agent_memory": ["Show amounts in EUR"]}},
            ]
        }
        result = await client.projects.list_agent_memory(project_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects"
        )
        assert client._request_json.call_args.kwargs["params"]["fields"] == "id,properties"
        assert result == {"items": ["Show amounts in EUR"]}

    async def test_list_agent_memory_absent_is_empty(self, client: MammothClient):
        client._request_json.return_value = {"projects": [{"id": 42, "properties": {}}]}
        assert await client.projects.list_agent_memory(project_id=42) == {"items": []}

    async def test_list_agent_memory_unknown_project_raises(self, client: MammothClient):
        client._request_json.return_value = {"projects": [{"id": 7}]}
        with pytest.raises(ValueError, match="42"):
            await client.projects.list_agent_memory(project_id=42)

    async def test_add_agent_memory(self, client: MammothClient):
        client._request_json.return_value = {
            "properties": {"agent_memory": ["Show amounts in EUR"]}
        }
        result = await client.projects.add_agent_memory(project_id=42, text="Show amounts in EUR")
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/workspaces/1/projects/42"
        )
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "add", "path": "agent_memory", "value": "Show amounts in EUR"}]},
        )
        assert result == {"items": ["Show amounts in EUR"]}

    async def test_remove_agent_memory(self, client: MammothClient):
        client._request_json.return_value = {"properties": {}}
        result = await client.projects.remove_agent_memory(project_id=42, index=3)
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/workspaces/1/projects/42"
        )
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "remove", "path": "agent_memory", "value": 3}]},
        )
        assert result == {"items": []}

    async def test_agent_memory_writes_reject_non_positive_project_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.projects.add_agent_memory(project_id=0, text="x")
        with pytest.raises(MammothValidationError):
            await client.projects.remove_agent_memory(project_id=0, index=0)

    async def test_publish_credentials(self, client: MammothClient):
        await client.projects.publish_credentials(project_id=42, odbc_type="postgres")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects/42/credentials"
        )
        assert client._request_json.call_args.kwargs["params"] == {"odbc_type": "postgres"}

    async def test_resource_dependencies(self, client: MammothClient):
        await client.projects.resource_dependencies(
            project_id=42, resource_ids=["1", "2"], is_recursive=True
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects/42/resource-dependencies"
        )
        assert client._request_json.call_args.kwargs["params"] == {
            "resource_ids": "1,2",
            "is_recursive": True,
        }

    async def test_resource_status(self, client: MammothClient):
        await client.projects.resource_status(project_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects/42/resource-status"
        )

    async def test_sample_flow(self, client: MammothClient):
        await client.projects.sample_flow(project_id=42, label_resource_id=8)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/workspaces/1/projects/42/sample-flow"
        )
        assert_json_body(client._request_json, {"label_resource_id": 8})

    async def test_user_update(self, client: MammothClient):
        await client.projects.user_update(project_id=42, role="project_admin", user_id=9)
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/workspaces/1/projects/42/users"
        )
        assert client._request_json.call_args.kwargs["params"] == {"user_id": 9}
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "permissions", "value": "project_admin"}]},
        )

    async def test_user_update_requires_exactly_one_target(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.projects.user_update(project_id=42, role="project_admin")
        with pytest.raises(MammothValidationError):
            await client.projects.user_update(
                project_id=42, role="project_admin", user_id=9, invite_id=10
            )

    async def test_resource_dependencies_update_emits_release_patch_wire(
        self, client: MammothClient
    ):
        patches = [
            DataSyncPatchItem(
                op="replace",
                path="data_sync",
                value={
                    "context_type": "dataview",
                    "context_id": 42,
                    "data_pass_through": None,
                    "run_pending_update": True,
                },
            )
        ]
        await client.projects.resource_dependencies_update(7, patches, workspace_id=4)
        assert_called_with_method_and_endpoint(
            client._request_json,
            "PATCH",
            "/workspaces/4/projects/7/resource-dependencies",
        )
        assert_json_body(
            client._request_json,
            {
                "patches": [
                    {
                        "op": "replace",
                        "path": "data_sync",
                        "value": {
                            "context_type": "dataview",
                            "context_id": 42,
                            "data_pass_through": None,
                            "run_pending_update": True,
                        },
                    }
                ]
            },
        )

    async def test_resource_dependencies_update_rejects_invalid_before_request(
        self, client: MammothClient
    ):
        with pytest.raises(MammothValidationError):
            await client.projects.resource_dependencies_update(
                7,
                [
                    {
                        "op": "replace",
                        "path": "wrong",
                        "value": {"context_type": "task", "context_id": 9},
                    }
                ],
            )
        with pytest.raises(MammothValidationError):
            await client.projects.resource_dependencies_update(
                7, [{"path": "data_sync", "value": {"context_type": "task", "context_id": 9}}]
            )
        with pytest.raises(MammothValidationError):
            await client.projects.resource_dependencies_update(
                7, [{"op": "replace", "value": {"context_type": "task", "context_id": 9}}]
            )
        with pytest.raises(MammothValidationError):
            await client.projects.resource_dependencies_update(
                7,
                [
                    {
                        "op": "replace",
                        "path": "data_sync",
                        "value": {"context_type": "task", "context_id": 9},
                    }
                ],
                workspace_id=0,
            )
        client._request_json.assert_not_called()


# ======================================================================
# DatasetsAPI
# ======================================================================


class TestTemplatesAPI:
    async def test_list_reads_bare_array_and_wraps_it(self, client: MammothClient):
        client._request_list = AsyncMock(return_value=[{"id": 3}])
        assert await client.templates.list() == {"templates": [{"id": 3}]}
        assert_called_with_method_and_endpoint(
            client._request_list, "GET", "/workspaces/1/templates"
        )


class TestDatasetsAPI:
    async def test_list(self, client: MammothClient):
        await client.datasets.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets")

    async def test_get(self, client: MammothClient):
        await client.datasets.get(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets/500")

    async def test_get_can_ask_for_a_smaller_record(self, client: MammothClient):
        """A caller reading a dataset into a model's context pays per field."""
        await client.datasets.get(dataset_id=500, fields="__standard")
        assert client._request_json.call_args.kwargs["params"] == {"fields": "__standard"}

    async def test_get_that_asks_for_nothing_leaves_the_route_its_default(
        self, client: MammothClient
    ):
        await client.datasets.get(dataset_id=500)
        assert client._request_json.call_args.kwargs.get("params") is None

    async def test_create(self, client: MammothClient):
        await client.datasets.create(dataset_spec={"name": "ds"}, ds_creation_type="file")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/datasets")

    async def test_update(self, client: MammothClient):
        await client.datasets.update(patch_data=[{"op": "rename_dataset", "path": "/500"}])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/datasets")

    async def test_rename(self, client: MammothClient):
        await client.datasets.rename(dataset_id=500, name="New Name")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/datasets/500")
        # OpenAPI DatasetPatchRequest for the singular route: one operation,
        # op=replace, path=name, value=<new name>.
        assert client._request_json.call_args.kwargs["json"] == {
            "patch": {"op": "replace", "path": "name", "value": "New Name"}
        }

    async def test_delete(self, client: MammothClient):
        await client.datasets.delete(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/datasets/500")

    async def test_preview_interpretation(self, client: MammothClient):
        await client.datasets.preview_interpretation(dataset_id=500, instruction="rows 3 down")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/interpretation/preview"
        )
        assert client._request_json.call_args.kwargs["json"] == {"user_instruction": "rows 3 down"}

    async def test_confirm_interpretation_reuses_the_previewed_plan(self, client: MammothClient):
        # The route never trusts a client's copy of the plan — it carries SQL.
        # An empty structure_map is what tells it to re-read its own.
        await client.datasets.confirm_interpretation(dataset_id=500, instruction="rows 3 down")
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/datasets/500/interpretation"
        )
        assert client._request_json.call_args.kwargs["json"] == {
            "user_instruction": "rows 3 down",
            "structure_map": {},
        }

    async def test_get_unstructured_rows(self, client: MammothClient):
        await client.datasets.get_unstructured_rows(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/unstructured_data"
        )

    async def test_discard_unstructured_rows(self, client: MammothClient):
        await client.datasets.discard_unstructured_rows(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/datasets/500/unstructured_data"
        )

    async def test_list_batches(self, client: MammothClient):
        await client.datasets.list_batches(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets/500/batches")

    async def test_get_batch(self, client: MammothClient):
        await client.datasets.get_batch(dataset_id=500, batch_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/batches/10")

    async def test_get_batch_data(self, client: MammothClient):
        client._request_json = AsyncMock(return_value={"job_id": 77, "status": "pending"})
        await client.datasets.get_batch_data(
            dataset_id=500, batch_id=10, columns="a,b", limit=10, offset=3
        )
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/batches/10/data")
        assert client._request_json.call_args.kwargs["params"] == {
            "limit": 10,
            "offset": 3,
            "columns": "a,b",
        }

    async def test_get_batch_data_rejects_invalid_paging(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="between 0 and 100"):
            await client.datasets.get_batch_data(dataset_id=500, batch_id=10, limit=101)
        with pytest.raises(MammothValidationError, match="non-negative"):
            await client.datasets.get_batch_data(dataset_id=500, batch_id=10, offset=-1)
        client._request_json.assert_not_called()

    async def test_get_file_settings(self, client: MammothClient):
        await client.datasets.get_file_settings(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/file_settings"
        )

    async def test_bulk_update(self, client: MammothClient):
        await client.datasets.bulk_update(patch_data={"name": "x"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/datasets")

    async def test_bulk_delete(self, client: MammothClient):
        # The route takes the ids query parameter; there is no delete-all form.
        await client.datasets.bulk_delete(dataset_ids=[7, 8])
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/workspaces/1/projects/100/datasets"
        )
        assert client._request_json.call_args.kwargs["params"] == {"ids": "7,8"}
        with pytest.raises(MammothValidationError, match="dataset_ids"):
            await client.datasets.bulk_delete()

    async def test_create_from_pdf(self, client: MammothClient):
        await client.datasets.create_from_pdf(file_object_id=7, file_name="report.pdf")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/datasets-from-pdf")
        assert_json_body(
            client._request_json,
            {
                "file_object_id": 7,
                "file_name": "report.pdf",
                "delete_file_after_extract": False,
            },
        )

    async def test_create_from_pdf_optional_fields(self, client: MammothClient):
        await client.datasets.create_from_pdf(
            file_object_id=7,
            file_name="report.pdf",
            file_id="abc123",
            table_list=[0, 2],
            is_preview_needed=True,
            user_instruction="extract totals",
        )
        assert_json_body(
            client._request_json,
            {
                "file_object_id": 7,
                "file_name": "report.pdf",
                "delete_file_after_extract": False,
                "file_id": "abc123",
                "table_list": [0, 2],
                "is_preview_needed": True,
                "user_instruction": "extract totals",
            },
        )

    async def test_create_from_pdf_rejects_nonpositive_file_object_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="file_object_id"):
            await client.datasets.create_from_pdf(file_object_id=0, file_name="report.pdf")
        client._request_json.assert_not_called()

    async def test_file_settings_update(self, client: MammothClient):
        await client.datasets.file_settings_update(
            dataset_id=500,
            delimiter=",",
            has_header=True,
            initial_skip_count=0,
            quotechar='"',
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/file_settings"
        )
        assert_json_body(
            client._request_json,
            {
                "delimiter": ",",
                "has_header": True,
                "initial_skip_count": 0,
                "quotechar": '"',
                "preview_mode": False,
                "skip_auto_process_check": True,
                "set_project_level_date_format": False,
            },
        )

    async def test_file_settings_update_rejects_nonpositive_dataset_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataset_id"):
            await client.datasets.file_settings_update(
                dataset_id=0,
                delimiter=",",
                has_header=True,
                initial_skip_count=0,
                quotechar='"',
            )
        client._request_json.assert_not_called()

    async def test_file_settings_undo(self, client: MammothClient):
        await client.datasets.file_settings_undo(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/datasets/500/file_settings"
        )

    async def test_restore(self, client: MammothClient):
        await client.datasets.restore(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/restore"
        )

    async def test_trash(self, client: MammothClient):
        await client.datasets.trash(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/datasets/500/trash")

    async def test_trash_rejects_nonpositive_dataset_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataset_id"):
            await client.datasets.trash(dataset_id=-1)
        client._request_json.assert_not_called()


# ======================================================================
# DataviewsAPI
# ======================================================================


class TestDataviewsAPI:
    async def test_list(self, client: MammothClient):
        await client.dataviews.list(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/dataviews"
        )

    async def test_get(self, client: MammothClient):
        # sequence=0 pins the read to the base dataset so no latest-sequence
        # resolution call is made (that path has its own test below).
        await client.dataviews.get(dataset_id=500, dataview_id=42, sequence=0)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dataviews/42")

    async def test_get_leaves_the_sequence_to_the_server_when_omitted(self, client: MammothClient):
        """No sequence means "the last task in the pipeline" to the API itself.

        Working it out here took an extra request and got it wrong while a
        draft was open: the highest task is the staged one, which never ran.
        """
        await client.dataviews.get(dataset_id=500, dataview_id=42)
        calls = client._request_json.call_args_list
        assert len(calls) == 1, "no latest-sequence lookup"
        assert "sequence" not in (calls[0][1].get("params") or {})

    async def test_query_data_leaves_the_sequence_to_the_server_when_omitted(
        self, client: MammothClient
    ):
        await client.dataviews.query_data(dataset_id=500, dataview_id=42)
        calls = client._request_json.call_args_list
        assert len(calls) == 1, "no latest-sequence lookup"
        assert "sequence" not in calls[0][1]["json"]

    async def test_create(self, client: MammothClient):
        await client.dataviews.create(dataset_id=500, name="New View")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/dataviews"
        )

    async def test_update(self, client: MammothClient):
        await client.dataviews.update(
            dataset_id=500, dataview_id=42, patch_data=[{"op": "replace"}]
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/dataviews/42")

    async def test_delete(self, client: MammothClient):
        await client.dataviews.delete(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/dataviews/42")

    async def test_bulk_delete(self, client: MammothClient):
        await client.dataviews.bulk_delete(dataset_id=500, dataview_ids=[42, 43])
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/datasets/500/dataviews"
        )

    async def test_query_data(self, client: MammothClient):
        # sequence=0 pins to the base dataset so no latest-sequence resolution
        # call is made.
        await client.dataviews.query_data(dataset_id=500, dataview_id=42, sequence=0)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dataviews/42/data")

    async def test_aggregate_pivot(self, client: MammothClient):
        await client.dataviews.aggregate(
            dataset_id=500,
            dataview_id=42,
            group_by=["column_1"],
            aggregations=[{"column": "column_2", "function": "SUM", "as_name": "Total"}],
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/data/query"
        )
        assert_json_body(
            client._request_json,
            {
                "param": {
                    "PIVOT": {
                        "SELECT": [
                            {
                                "FUNCTION": "SUM",
                                "AS": "Total",
                                "INTERNAL_NAME": "agg_0",
                                "COLUMN": "column_2",
                            }
                        ],
                        "GROUP_BY": [{"COLUMN": "column_1", "INTERNAL_NAME": "group_0"}],
                    }
                }
            },
        )

    async def test_aggregate_metric(self, client: MammothClient):
        await client.dataviews.aggregate(
            dataset_id=500,
            dataview_id=42,
            metric={"function": "COUNT"},
        )
        assert_json_body(
            client._request_json,
            {
                "param": {
                    "METRIC": {
                        "EXPRESSION": [{"TYPE": "FUNCTION", "VALUE": {"FUNCTION": "COUNT"}}],
                        "AS": "COUNT",
                        "INTERNAL_NAME": "metric",
                    }
                }
            },
        )

    async def test_aggregate_forwards_condition_sequence_and_limit(self, client: MammothClient):
        await client.dataviews.aggregate(
            dataset_id=500,
            dataview_id=42,
            metric={"function": "COUNT"},
            condition={"column_1": {"GT": {"VALUE": 0}}},
            sequence=3,
            limit=10,
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert body["param"]["CONDITION"] == {"column_1": {"GT": {"VALUE": 0}}}
        assert body["param"]["SEQUENCE_NUMBER"] == 3
        assert body["display_properties"] == {"LIMIT": 10}

    async def test_aggregate_requires_exactly_one_of_aggregations_or_metric(
        self, client: MammothClient
    ):
        with pytest.raises(MammothValidationError):
            await client.dataviews.aggregate(dataset_id=500, dataview_id=42)
        with pytest.raises(MammothValidationError):
            await client.dataviews.aggregate(
                dataset_id=500,
                dataview_id=42,
                group_by=["column_1"],
                metric={"function": "COUNT"},
            )

    async def test_aggregate_rejects_unsupported_function(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.dataviews.aggregate(
                dataset_id=500,
                dataview_id=42,
                metric={"column": "column_1", "function": "MEDIAN"},
            )

    async def test_aggregate_requires_column_unless_count(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.dataviews.aggregate(
                dataset_id=500,
                dataview_id=42,
                metric={"function": "SUM"},
            )

    async def test_aggregate_group_by_date_truncate(self, client: MammothClient):
        await client.dataviews.aggregate(
            dataset_id=500,
            dataview_id=42,
            group_by=[{"column": "column_1", "truncate": "month"}],
            aggregations=[{"function": "COUNT"}],
        )
        assert_json_body(
            client._request_json,
            {
                "param": {
                    "PIVOT": {
                        "SELECT": [{"FUNCTION": "COUNT", "AS": "COUNT", "INTERNAL_NAME": "agg_0"}],
                        "GROUP_BY": [
                            {
                                "COLUMN": "column_1",
                                "INTERNAL_NAME": "group_0",
                                "TRUNCATE": "MONTH",
                            }
                        ],
                    }
                }
            },
        )

    async def test_aggregate_group_by_numeric_resolution(self, client: MammothClient):
        await client.dataviews.aggregate(
            dataset_id=500,
            dataview_id=42,
            group_by=[{"column": "column_2", "resolution": "AUTO"}],
            aggregations=[{"function": "COUNT"}],
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert body["param"]["PIVOT"]["GROUP_BY"] == [
            {"COLUMN": "column_2", "INTERNAL_NAME": "group_0", "RESOLUTION": "AUTO"}
        ]

    async def test_aggregate_group_by_rejects_unsupported_truncate(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.dataviews.aggregate(
                dataset_id=500,
                dataview_id=42,
                group_by=[{"column": "column_1", "truncate": "FORTNIGHT"}],
                aggregations=[{"function": "COUNT"}],
            )

    async def test_aggregate_group_by_dict_requires_column(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.dataviews.aggregate(
                dataset_id=500,
                dataview_id=42,
                group_by=[{"truncate": "MONTH"}],
                aggregations=[{"function": "COUNT"}],
            )

    async def test_explore_date_column_buckets_by_truncate(self, client: MammothClient):
        await client.dataviews.explore(
            dataset_id=500,
            dataview_id=42,
            column="column_3",
            column_type="DATE",
            level="MONTH",
        )
        assert_json_body(
            client._request_json,
            {
                "param": {
                    "PIVOT": {
                        "SELECT": [{"FUNCTION": "COUNT", "AS": "count", "INTERNAL_NAME": "agg_0"}],
                        "GROUP_BY": [
                            {
                                "COLUMN": "column_3",
                                "INTERNAL_NAME": "group_0",
                                "TRUNCATE": "MONTH",
                            }
                        ],
                    }
                }
            },
        )

    async def test_explore_numeric_column_buckets_by_resolution_default_auto(
        self, client: MammothClient
    ):
        await client.dataviews.explore(
            dataset_id=500, dataview_id=42, column="column_2", column_type="NUMERIC"
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert body["param"]["PIVOT"]["GROUP_BY"] == [
            {"COLUMN": "column_2", "INTERNAL_NAME": "group_0", "RESOLUTION": "AUTO"}
        ]

    async def test_explore_text_column_groups_by_raw_column(self, client: MammothClient):
        await client.dataviews.explore(
            dataset_id=500, dataview_id=42, column="column_1", column_type="TEXT"
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert body["param"]["PIVOT"]["GROUP_BY"] == [
            {"COLUMN": "column_1", "INTERNAL_NAME": "group_0"}
        ]

    async def test_explore_metric_adds_second_aggregation(self, client: MammothClient):
        await client.dataviews.explore(
            dataset_id=500,
            dataview_id=42,
            column="column_1",
            column_type="TEXT",
            metric={"column": "column_2", "function": "SUM", "as_name": "Total Spend"},
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert body["param"]["PIVOT"]["SELECT"] == [
            {"FUNCTION": "COUNT", "AS": "count", "INTERNAL_NAME": "agg_0"},
            {
                "FUNCTION": "SUM",
                "AS": "Total Spend",
                "INTERNAL_NAME": "agg_1",
                "COLUMN": "column_2",
            },
        ]

    async def test_explore_forwards_condition_and_sequence(self, client: MammothClient):
        await client.dataviews.explore(
            dataset_id=500,
            dataview_id=42,
            column="column_1",
            condition={"column_1": {"GT": {"VALUE": 0}}},
            sequence=3,
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert body["param"]["CONDITION"] == {"column_1": {"GT": {"VALUE": 0}}}
        assert body["param"]["SEQUENCE_NUMBER"] == 3

    async def test_explore_date_result_sorted_ascending_with_percentage(
        self, client: MammothClient
    ):
        client._request_json.return_value = {
            "data": [
                {"group_0": "2024-02-01", "agg_0": 30},
                {"group_0": "2024-01-01", "agg_0": 10},
            ]
        }
        result = await client.dataviews.explore(
            dataset_id=500, dataview_id=42, column="column_1", column_type="DATE", level="MONTH"
        )
        assert result["data"] == [
            {"group_0": "2024-01-01", "agg_0": 10, "percentage": 25.0},
            {"group_0": "2024-02-01", "agg_0": 30, "percentage": 75.0},
        ]

    async def test_explore_text_result_sorted_desc_and_defaults_limit_20(
        self, client: MammothClient
    ):
        client._request_json.return_value = {
            "data": [{"group_0": f"v{i}", "agg_0": i} for i in range(25)]
        }
        result = await client.dataviews.explore(
            dataset_id=500, dataview_id=42, column="column_1", column_type="TEXT"
        )
        assert len(result["data"]) == 20
        assert result["data"][0]["group_0"] == "v24"
        assert result["data"][-1]["group_0"] == "v5"

    async def test_explore_limit_trims_after_computing_percentage_of_the_full_total(
        self, client: MammothClient
    ):
        client._request_json.return_value = {
            "data": [
                {"group_0": "Email", "agg_0": 5},
                {"group_0": "Search", "agg_0": 15},
            ]
        }
        result = await client.dataviews.explore(
            dataset_id=500, dataview_id=42, column="column_1", column_type="TEXT", limit=1
        )
        assert result["data"] == [{"group_0": "Search", "agg_0": 15, "percentage": 75.0}]

    async def test_explore_sort_value_desc_and_offset_page_the_buckets(self, client: MammothClient):
        client._request_json.return_value = {
            "data": (
                [{"group_0": f"v{i}", "agg_0": 1} for i in range(5)]
                + [{"group_0": None, "agg_0": 1}]
            )
        }
        result = await client.dataviews.explore(
            dataset_id=500,
            dataview_id=42,
            column="column_1",
            column_type="TEXT",
            sort="value_desc",
            offset=1,
            limit=2,
        )
        assert [row["group_0"] for row in result["data"]] == ["v3", "v2"]

    async def test_explore_blank_bucket_sorts_last(self, client: MammothClient):
        client._request_json.return_value = {
            "data": [{"group_0": None, "agg_0": 9}, {"group_0": "2024-01-01", "agg_0": 1}]
        }
        result = await client.dataviews.explore(
            dataset_id=500, dataview_id=42, column="column_1", column_type="DATE"
        )
        assert [row["group_0"] for row in result["data"]] == ["2024-01-01", None]

    async def test_explore_rejects_unknown_sort(self, client: MammothClient):
        client._request_json.return_value = {"data": [{"group_0": "a", "agg_0": 1}]}
        with pytest.raises(MammothValidationError):
            await client.dataviews.explore(
                dataset_id=500, dataview_id=42, column="column_1", column_type="TEXT", sort="up"
            )

    async def test_aggregate_accepts_stddev_and_distinct_count(self, client: MammothClient):
        await client.dataviews.aggregate(
            dataset_id=500,
            dataview_id=42,
            aggregations=[
                {"column": "column_2", "function": "STDDEV"},
                {"column": "column_1", "function": "DISTINCT_COUNT"},
            ],
        )
        body = client._request_json.call_args.kwargs.get("json")
        assert [item["FUNCTION"] for item in body["param"]["PIVOT"]["SELECT"]] == [
            "STDDEV",
            "DISTINCT_COUNT",
        ]

    async def test_exportable_config_get(self, client: MammothClient):
        await client.dataviews.get_exportable_config(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/exportable-config"
        )

    async def test_exportable_config_apply_requires_exactly_one_source(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="Exactly one"):
            await client.dataviews.apply_exportable_config(dataset_id=500, dataview_id=42)
        with pytest.raises(MammothValidationError, match="Exactly one"):
            await client.dataviews.apply_exportable_config(
                dataset_id=500, dataview_id=42, items=[], config={}
            )
        client._request_json.assert_not_called()

    async def test_exportable_config_apply(self, client: MammothClient):
        await client.dataviews.apply_exportable_config(
            dataset_id=500,
            dataview_id=42,
            config={"tasks": []},
            is_paste_mode=True,
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/exportable-config"
        )
        assert_json_body(
            client._request_json,
            {"config": {"tasks": []}, "is_paste_mode": True},
        )

    async def test_active_users(self, client: MammothClient):
        await client.dataviews.active_users(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/activities"
        )

    async def test_mark_active(self, client: MammothClient):
        await client.dataviews.mark_active(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/activities"
        )

    async def test_conditional_format_list(self, client: MammothClient):
        await client.dataviews.conditional_format_list(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/conditional-format"
        )

    async def test_conditional_format_list_unpacks_rule_id_mapping(self, client: MammothClient):
        # Release returns {rule_id: rule}; the id is what delete needs.
        client._request_json = AsyncMock(
            return_value={
                "bca0ff33bd6f8ed1": {"cf_type": "RULE", "enabled": True, "sequence": 0},
                "1f2e3d4c5b6a7980": {"cf_type": "COLOR_SCALE", "enabled": True, "sequence": 1},
            }
        )
        rules = await client.dataviews.conditional_format_list(dataset_id=500, dataview_id=42)
        assert rules == [
            {"rule_id": "bca0ff33bd6f8ed1", "cf_type": "RULE", "enabled": True, "sequence": 0},
            {
                "rule_id": "1f2e3d4c5b6a7980",
                "cf_type": "COLOR_SCALE",
                "enabled": True,
                "sequence": 1,
            },
        ]

    async def test_conditional_format_list_empty_mapping(self, client: MammothClient):
        client._request_json = AsyncMock(return_value={})
        assert await client.dataviews.conditional_format_list(dataset_id=500, dataview_id=42) == []

    async def test_conditional_format_create(self, client: MammothClient):
        await client.dataviews.conditional_format_create(
            dataset_id=500, dataview_id=42, rule={"color": "red"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/conditional-format"
        )

    async def test_conditional_format_update(self, client: MammothClient):
        await client.dataviews.conditional_format_update(
            dataset_id=500, dataview_id=42, rule={"color": "blue"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/dataviews/42/conditional-format"
        )

    async def test_conditional_format_delete(self, client: MammothClient):
        # The route requires the rule_id query parameter; there is no delete-all.
        await client.dataviews.conditional_format_delete(
            dataset_id=500, dataview_id=42, rule_id="r1"
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/dataviews/42/conditional-format"
        )
        assert client._request_json.call_args.kwargs["params"] == {"rule_id": "r1"}
        with pytest.raises(MammothValidationError, match="rule_id"):
            await client.dataviews.conditional_format_delete(dataset_id=500, dataview_id=42)

    async def test_draft_mode(self, client: MammothClient):
        await client.dataviews.draft_mode(dataset_id=500, dataview_id=42, command="enter")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/draft-mode"
        )

    async def test_parameter_context(self, client: MammothClient):
        await client.dataviews.parameter_context(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/parameter-context"
        )

    async def test_parameter_context_rejects_nonpositive_dataview_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.dataviews.parameter_context(dataset_id=500, dataview_id=0)
        client._request_json.assert_not_called()

    async def test_preview(self, client: MammothClient):
        await client.dataviews.preview(dataset_id=500, dataview_id=42, rows=10, cols=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dataviews/42/preview")
        assert client._request_json.call_args.kwargs["params"] == {"rows": 10, "cols": 5}

    async def test_preview_omits_unset_params(self, client: MammothClient):
        await client.dataviews.preview(dataset_id=500, dataview_id=42)
        assert client._request_json.call_args.kwargs["params"] is None

    async def test_preview_rejects_nonpositive_dataview_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.dataviews.preview(dataset_id=500, dataview_id=0)
        client._request_json.assert_not_called()

    async def test_restore(self, client: MammothClient):
        await client.dataviews.restore(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/restore"
        )

    async def test_trash(self, client: MammothClient):
        await client.dataviews.trash(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dataviews/42/trash")

    async def test_trash_rejects_nonpositive_dataview_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.dataviews.trash(dataset_id=500, dataview_id=0)
        client._request_json.assert_not_called()


# ======================================================================
# PipelineAPI
# ======================================================================


class TestPipelineAPI:
    async def test_get_pipeline(self, client: MammothClient):
        await client.pipeline.get_pipeline(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/pipeline"
        )

    async def test_list_tasks(self, client: MammothClient):
        await client.pipeline.list_tasks(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/tasks")

    async def test_list_tasks_requests_full_fields(self, client: MammothClient):
        # __standard (the server default) omits transform_status and
        # reference_errors, so a task that failed at run time (a GEN_AI step
        # hitting a workspace AI quota, for example) is invisible: has_error
        # stays false and pipeline_state reads ready. __full is the only mode
        # that carries transform_status.
        await client.pipeline.list_tasks(dataview_id=42, dataset_id=500)
        assert client._request_json.call_args.kwargs["params"] == {"fields": "__full"}

    async def test_add_task(self, client: MammothClient):
        await client.pipeline.add_task(dataview_id=42, task_spec={"MATH": {}}, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/pipeline/tasks")

    async def test_get_task(self, client: MammothClient):
        await client.pipeline.get_task(dataview_id=42, task_id=7, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/tasks/7")

    async def test_get_task_requests_full_fields(self, client: MammothClient):
        await client.pipeline.get_task(dataview_id=42, task_id=7, dataset_id=500)
        assert client._request_json.call_args.kwargs["params"] == {"fields": "__full"}

    async def test_update_task(self, client: MammothClient):
        # TaskPatch: ``patches``; task_spec is the replace-params shortcut.
        await client.pipeline.update_task(
            dataview_id=42, task_id=7, task_spec={"MATH": {}}, dataset_id=500
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/pipeline/tasks/7")
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "params", "value": {"MATH": {}}}]},
        )

    async def test_delete_task(self, client: MammothClient):
        await client.pipeline.delete_task(dataview_id=42, task_id=7, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/pipeline/tasks/7")

    async def test_preview_task_can_say_how_many_rows_to_sample(self, client: MammothClient):
        """A caller showing a preview to a person chooses how much to show."""
        await client.pipeline.preview_task(
            dataview_id=42, task_spec={"MATH": {}}, dataset_id=500, sample_size=25
        )
        assert client._request_json.call_args.kwargs["params"] == {"sample_size": 25}

    async def test_preview_task_that_names_no_size_leaves_the_route_its_own(
        self, client: MammothClient
    ):
        await client.pipeline.preview_task(dataview_id=42, task_spec={"MATH": {}}, dataset_id=500)
        assert client._request_json.call_args.kwargs.get("params") is None

    async def test_preview_task(self, client: MammothClient):
        await client.pipeline.preview_task(dataview_id=42, task_spec={"MATH": {}}, dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/pipeline/task_preview"
        )

    async def test_draft_mode(self, client: MammothClient):
        await client.pipeline.draft_mode(dataview_id=42, command="enter", dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/draft-mode")

    async def test_draft_mode_rejects_unknown_operation_before_transport(
        self, client: MammothClient
    ):
        with pytest.raises(ValueError, match="enter, exit, submit, discard"):
            await client.pipeline.draft_mode(dataview_id=42, command="status", dataset_id=500)
        client._request_json.assert_not_called()

    async def test_edit_pipeline(self, client: MammothClient):
        await client.pipeline.edit_pipeline(
            dataview_id=42, patches=[{"op": "command"}], dataset_id=500
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/dataviews/42/pipeline"
        )

    async def test_command(self, client: MammothClient):
        await client.pipeline.command(dataview_id=42, command="exit", dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/draft-mode")
        assert_json_body(client._request_json, {"draft_operation": "exit"})

    async def test_items(self, client: MammothClient):
        await client.pipeline.items(dataview_id=42, dataset_id=500, status="pending", sequence=3)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/pipeline/items"
        )
        assert client._request_json.call_args.kwargs["params"] == {
            "sequence": 3,
            "status": "pending",
        }

    async def test_items_all_collects_pages_with_same_exact_parent(self, client: MammothClient):
        client._request_json = AsyncMock(
            side_effect=[
                {
                    "items": [{"id": 1}],
                    "next": (
                        "/api/v2/workspaces/1/projects/100/datasets/500/dataviews/42/"
                        "pipeline/items?limit=1&offset=1"
                    ),
                },
                {"items": [{"id": 2}], "next": ""},
            ]
        )

        result = await client.pipeline.items_all(
            dataview_id=42, dataset_id=500, limit=1, fields="__full", status="success"
        )

        assert result["items"] == [{"id": 1}, {"id": 2}]
        assert result["pages"] == 2
        calls = client._request_json.call_args_list
        assert [call.args[:2] for call in calls] == [
            ("GET", "/workspaces/1/projects/100/datasets/500/dataviews/42/pipeline/items"),
            ("GET", "/workspaces/1/projects/100/datasets/500/dataviews/42/pipeline/items"),
        ]
        assert calls[0].kwargs["params"] == {
            "fields": "__full",
            "limit": 1,
            "offset": 0,
            "status": "success",
        }
        assert calls[1].kwargs["params"] == {
            "fields": "__full",
            "limit": 1,
            "offset": 1,
            "status": "success",
        }

    async def test_items_all_rejects_repeated_offset(self, client: MammothClient):
        from mammoth.exceptions import MammothPaginationError

        client._request_json = AsyncMock(
            return_value={
                "items": [{"id": 1}],
                "next": (
                    "/api/v2/workspaces/1/projects/100/datasets/500/dataviews/42/"
                    "pipeline/items?offset=0"
                ),
            }
        )
        with pytest.raises(MammothPaginationError, match="non-advancing"):
            await client.pipeline.items_all(dataview_id=42, dataset_id=500, limit=1)

    @pytest.mark.parametrize(
        "next_hint",
        [
            "/api/v2/workspaces/1/projects/100/datasets/500/dataviews/42/pipeline/items?limit=1",
            "/api/v2/workspaces/1/projects/100/datasets/999/dataviews/42/pipeline/items?offset=1",
        ],
    )
    async def test_items_all_rejects_unverifiable_continuation(
        self, client: MammothClient, next_hint: str
    ):
        from mammoth.exceptions import MammothPaginationError

        client._request_json = AsyncMock(return_value={"items": [{"id": 1}], "next": next_hint})
        with pytest.raises(MammothPaginationError, match="unsupported pipeline-items"):
            await client.pipeline.items_all(dataview_id=42, dataset_id=500, limit=1)

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"dataset_id": 0},
            {"dataset_id": True},
            {"limit": 0},
            {"limit": 101},
            {"max_pages": 0},
            {"max_pages": 1001},
        ],
    )
    async def test_items_all_rejects_invalid_bounds_before_transport(
        self, client: MammothClient, kwargs: dict[str, object]
    ):
        from mammoth.exceptions import MammothValidationError

        call_kwargs = {"dataset_id": 500, **kwargs}
        with pytest.raises(MammothValidationError):
            await client.pipeline.items_all(dataview_id=42, **call_kwargs)
        client._request_json.assert_not_called()

    async def test_rerun(self, client: MammothClient):
        await client.pipeline.rerun(dataview_id=42, from_sequence=2, dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/pipeline/rerun"
        )
        assert_json_body(client._request_json, {"from_sequence": 2})

    async def test_rerun_rejects_negative_from_sequence(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.pipeline.rerun(dataview_id=42, from_sequence=-1, dataset_id=500)


# ======================================================================
# FilesAPI
# ======================================================================


class TestFilesAPI:
    async def test_list(self, client: MammothClient):
        # await files.list() parses response into FilesList Pydantic model
        client._request_json = AsyncMock(
            return_value={
                "files": [],
                "next": "",
            }
        )
        await client.files.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/files")

    async def test_get(self, client: MammothClient):
        # await files.get() parses response into FileDetails -> returns file field
        client._request_json = AsyncMock(
            return_value={
                "file": {"id": 10, "name": "test.csv"},
            }
        )
        await client.files.get(file_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/files/10")

    async def test_delete(self, client: MammothClient):
        await client.files.delete(file_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/files/10")

    async def test_bulk_delete(self, client: MammothClient):
        await client.files.bulk_delete(file_ids=[10, 11])
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/files")

    async def test_update_surfaces_completed_job_status(self, client: MammothClient):
        # The PATCH enqueues a job (the handle carries the job id); waiting yields
        # the completed payload, whose terminal status must be surfaced on the
        # returned schema while the original job id is preserved.
        from mammoth.models.files import (
            FilePatchData,
            FilePatchOperation,
            FilePatchPath,
            FilePatchRequest,
        )

        client._request_json = AsyncMock(return_value={"job_id": 77, "status_code": 202})
        client._wait_if_job = AsyncMock(side_effect=lambda r, **kw: {"status_code": 200})
        request = FilePatchRequest(
            patch=[
                FilePatchData(
                    op=FilePatchOperation.REPLACE,
                    path=FilePatchPath.PASSWORD,
                    value="secret",
                )
            ]
        )
        result = await client.files.update(file_id=10, patch_request=request)
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/files/10")
        assert result.job_id == 77  # preserved from the enqueue handle
        assert result.status_code == 200  # surfaced from the completed payload


# ======================================================================
# FoldersAPI
# ======================================================================


class TestFoldersAPI:
    async def test_list(self, client: MammothClient):
        await client.folders.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/folders")

    async def test_create(self, client: MammothClient):
        client._request_json = AsyncMock(
            return_value={"id": 1, "name": "Test", "resource_id": "r1"}
        )
        await client.folders.create(name="Test Folder")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/folders")

    async def test_delete(self, client: MammothClient):
        await client.folders.delete(folder_ids=[1, 2])
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/folders")

    async def test_move(self, client: MammothClient):
        # BulkFolderPatchRequest: patch [{op: move, from: [ids], path: folder | "root"}].
        await client.folders.move(resource_ids=["8024", 8025], target_folder_resource_id="17")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/folders")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "move", "from": [8024, 8025], "path": 17}]},
        )
        client._request_json.reset_mock()
        await client.folders.move(resource_ids=[8024])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "move", "from": [8024], "path": "root"}]},
        )

    async def test_bulk_delete(self, client: MammothClient):
        await client.folders.bulk_delete(folder_ids=[1, 2], check_dependency=False)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/folders")
        assert client._request_json.call_args.kwargs["params"] == {
            "ids": "1,2",
            "check_dependency": False,
        }

    async def test_get(self, client: MammothClient):
        client._request_json = AsyncMock(
            return_value={"id": 1, "name": "Test", "resource_id": "r1"}
        )
        await client.folders.get(folder_id=1)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/folders/1")

    async def test_get_rejects_non_positive_folder_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError):
            await client.folders.get(folder_id=0)

    async def test_trash(self, client: MammothClient):
        client._request_json = AsyncMock(
            return_value={
                "job": {
                    "id": 5,
                    "status": "processing",
                    "response": {},
                    "last_updated_at": datetime.now(timezone.utc),
                    "created_at": datetime.now(timezone.utc),
                    "path": "/folders/1/trash",
                    "operation": "trash_folder",
                }
            }
        )
        await client.folders.trash(folder_id=1)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/folders/1/trash")

    async def test_update(self, client: MammothClient):
        client._request_json = AsyncMock(
            return_value={"id": 1, "name": "Renamed", "resource_id": "r1"}
        )
        await client.folders.update(folder_id=1, name="Renamed")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/folders/1")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "name", "value": "Renamed"}]},
        )


# ======================================================================
# JobsAPI
# ======================================================================


class TestJobsAPI:
    async def test_get_job(self, client: MammothClient):
        await client.jobs.get_job(job_id=999)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/jobs/999")

    async def test_get_jobs(self, client: MammothClient):
        await client.jobs.get_jobs(job_ids=[1, 2, 3])
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/jobs")


# ======================================================================
# ExportsAPI (low-level)
# ======================================================================


class TestExportsAPILowLevel:
    async def test_list(self, client: MammothClient):
        # await exports.list() needs _find_dataset_for_dataview and returns Pydantic model
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        client._request_json = AsyncMock(
            return_value={
                "exports": [],
                "total": 0,
                "limit": 50,
                "offset": 0,
                "next": "",
            }
        )
        await client.exports.list(dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/exports")

    async def test_list_with_explicit_dataset_id_bypasses_parent_discovery(
        self, client: MammothClient
    ):
        client.pipeline._find_dataset_for_dataview = AsyncMock(side_effect=AssertionError)
        client._request_json = AsyncMock(
            return_value={
                "exports": [],
                "limit": 50,
                "offset": 0,
                "next": "",
            }
        )
        await client.exports.list(dataview_id=42, dataset_id=500, limit=23, offset=4)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/dataviews/42/pipeline/exports"
        )
        assert client._request_json.call_args.kwargs["params"] == {
            "limit": 23,
            "offset": 4,
        }

    async def test_list_rejects_nonpositive_explicit_dataset_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataset_id"):
            await client.exports.list(dataview_id=42, dataset_id=0)
        client._request_json.assert_not_called()

    async def test_get(self, client: MammothClient):
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        await client.exports.get(dataview_id=42, export_id=99, fields="__full")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/exports/99")
        assert client._request_json.call_args.kwargs["params"] == {"fields": "__full"}

    async def test_get_rejects_nonpositive_export_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="export_id"):
            await client.exports.get(dataview_id=42, export_id=0)
        client._request_json.assert_not_called()

    async def test_get_rejects_nonpositive_dataview_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.exports.get(dataview_id=0, export_id=99)
        client._request_json.assert_not_called()

    async def test_update(self, client: MammothClient):
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        patches = [{"op": "command", "path": "suspend", "value": None}]
        await client.exports.update(
            dataview_id=42, export_id=99, patches=patches, skip_validation=True
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/pipeline/exports/99"
        )
        assert_json_body(client._request_json, {"patches": patches})
        assert client._request_json.call_args.kwargs["params"] == {"skip_validation": True}

    async def test_update_rejects_nonpositive_export_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="export_id"):
            await client.exports.update(dataview_id=42, export_id=0, patches=[])
        client._request_json.assert_not_called()

    async def test_delete(self, client: MammothClient):
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        await client.exports.delete(dataview_id=42, export_id=99, skip_validation=True)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/pipeline/exports/99"
        )
        assert client._request_json.call_args.kwargs["params"] == {"skip_validation": True}

    async def test_delete_rejects_nonpositive_export_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="export_id"):
            await client.exports.delete(dataview_id=42, export_id=0)
        client._request_json.assert_not_called()

    async def test_publish_db(self, client: MammothClient):
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        await client.exports.publish_db(
            dataview_id=42,
            odbc_type=OdbcType.POSTGRES,
            target_properties={"table": "sales"},
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/publish-to-db"
        )
        assert_json_body(
            client._request_json,
            {"odbc_type": "postgres", "target_properties": {"table": "sales"}},
        )

    async def test_publish_db_rejects_nonpositive_dataview_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.exports.publish_db(
                dataview_id=0,
                odbc_type=OdbcType.POSTGRES,
                target_properties={"table": "sales"},
            )
        client._request_json.assert_not_called()

    async def test_publish_db_update(self, client: MammothClient):
        client.pipeline._find_dataset_for_dataview = AsyncMock(return_value=500)
        patch = [{"op": "replace", "path": "credentials", "value": {"odbc_type": "postgres"}}]
        await client.exports.publish_db_update(dataview_id=42, patch=patch)
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/dataviews/42/publish-to-db"
        )
        assert_json_body(client._request_json, {"patch": patch})

    async def test_publish_db_update_rejects_nonpositive_dataview_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.exports.publish_db_update(dataview_id=0, patch=[])
        client._request_json.assert_not_called()


class TestExportsAPICsv:
    """``to_csv`` downloads a local file; ``to_csv_url`` shares its create-and-wait
    logic but returns the signed URL undownloaded, for an embedded CLI caller
    that must never write to the host process's disk (see mammoth-cli's
    ``mammoth_cli/embed.py`` and ``commands/view.py::view_export_csv``)."""

    def _job_created_response(self, job_id: int) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "job": {
                "id": job_id,
                "status": "processing",
                "response": {},
                "last_updated_at": now,
                "created_at": now,
                "path": "/pipeline/exports",
                "operation": "add_export",
            }
        }

    async def test_to_csv_url_returns_signed_url_without_downloading(self, client: MammothClient):
        client._request_json.return_value = self._job_created_response(9001)
        client.exports._jobs_api.wait_for_job = AsyncMock(
            return_value={
                "status": "success",
                "response": {"url": "https://signed.example/file.csv", "trigger_id": 77},
            }
        )

        result = await client.exports.to_csv_url(dataview_id=42, dataset_id=500)

        assert result == {
            "url": "https://signed.example/file.csv",
            "trigger_id": 77,
            "job_id": 9001,
        }
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/pipeline/exports")

    async def test_to_csv_url_rejects_missing_project_id(self, client: MammothClient):
        client.project_id = None
        with pytest.raises(ValueError, match="project_id must be set"):
            await client.exports.to_csv_url(dataview_id=42, dataset_id=500)
        client._request_json.assert_not_called()

    async def test_to_csv_downloads_using_to_csv_url_result(self, client: MammothClient):
        client.exports.to_csv_url = AsyncMock(
            return_value={
                "url": "https://signed.example/file.csv",
                "trigger_id": None,
                "job_id": 9001,
            }
        )
        client.exports._download_file = AsyncMock(return_value=Path("/tmp/out.csv"))

        result = await client.exports.to_csv(
            dataview_id=42, output_path="/tmp/out.csv", dataset_id=500
        )

        client.exports.to_csv_url.assert_called_once_with(42, timeout=300, dataset_id=500)
        client.exports._download_file.assert_called_once_with(
            "https://signed.example/file.csv", Path("/tmp/out.csv"), job_handle=9001
        )
        assert result == Path("/tmp/out.csv")


# ======================================================================
# ConnectorsAPI
# ======================================================================


class TestConnectorsAPI:
    async def test_list(self, client: MammothClient):
        await client.connectors.list()
        assert_called_with_method_and_endpoint(client._request, "GET", "/connectors")

    async def test_get(self, client: MammothClient):
        # The server base64-decodes the connector_key path segment (see
        # decode_connector_key in mvc-service); the SDK sends it encoded
        # while callers keep passing the plain name_key.
        await client.connectors.get(connector_key="salesforce")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/connectors/c2FsZXNmb3JjZQ=="
        )

    async def test_list_connections(self, client: MammothClient):
        await client.connectors.list_connections(connector_key="salesforce")
        assert_called_with_method_and_endpoint(
            client._request, "GET", "/connectors/c2FsZXNmb3JjZQ==/connections"
        )

    async def test_create_connection(self, client: MammothClient):
        await client.connectors.create_connection(
            connector_key="salesforce", config={"code": "oauth_code"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connectors/c2FsZXNmb3JjZQ==/connections"
        )
        assert_json_body(client._request_json, {"code": "oauth_code"})

    async def test_create_connection_forwards_config_unchanged(self, client: MammothClient):
        creds = {
            "hostname": "db.example.com",
            "port": 5432,
            "database": "prod",
            "username": "u",
            "password": "p",
        }
        await client.connectors.create_connection(connector_key="postgres", config=creds)
        assert_json_body(client._request_json, creds)

    async def test_create_connection_rejects_empty_config(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="config"):
            await client.connectors.create_connection(connector_key="postgres", config={})
        client._request_json.assert_not_called()

    async def test_get_connection(self, client: MammothClient):
        await client.connectors.get_connection(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/connections/conn1")

    async def test_update_connection_wraps_patch_envelope(self, client: MammothClient):
        """PROD BUG FIX: SDK must wrap credentials in the patch envelope."""
        creds = {"host": "new.db.example.com", "password": "newpass"}
        await client.connectors.update_connection(
            connector_key="postgres", connection_key="conn1", credentials=creds
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/connections/conn1")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "connection", "value": creds}]},
        )

    async def test_update_connection_rejects_empty_credentials(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="credentials"):
            await client.connectors.update_connection(
                connector_key="postgres", connection_key="conn1", credentials={}
            )
        client._request_json.assert_not_called()

    async def test_delete_connection(self, client: MammothClient):
        await client.connectors.delete_connection(
            connector_key="salesforce", connection_key="conn1"
        )
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/connections/conn1")

    async def test_list_ds_configs(self, client: MammothClient):
        await client.connectors.list_ds_configs(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(
            client._request, "GET", "/connections/conn1/ds_configs"
        )

    async def test_create_ds_config_with_query(self, client: MammothClient):
        await client.connectors.create_ds_config(
            connector_key="postgres",
            connection_key="conn1",
            query="SELECT * FROM orders",
            table="orders",
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connections/conn1/ds_configs"
        )
        assert_json_body(
            client._request_json,
            {
                "query": "SELECT * FROM orders",
                "table": "orders",
                "validate": True,
                "data_sample": False,
            },
        )

    async def test_create_ds_config_with_file_source(self, client: MammothClient):
        await client.connectors.create_ds_config(
            connector_key="sftp",
            connection_key="conn1",
            file_source="/data/report.csv",
            data_sample=True,
            validate=False,
        )
        assert_json_body(
            client._request_json,
            {"file_source": "/data/report.csv", "validate": False, "data_sample": True},
        )

    async def test_create_ds_config_rejects_no_source(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="query"):
            await client.connectors.create_ds_config(
                connector_key="postgres", connection_key="conn1"
            )
        client._request_json.assert_not_called()

    async def test_create_ds_config_rejects_validate_xor(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="mutually exclusive"):
            await client.connectors.create_ds_config(
                connector_key="postgres",
                connection_key="conn1",
                query="SELECT 1",
                validate=True,
                data_sample=True,
            )
        client._request_json.assert_not_called()

    async def test_get_ds_config(self, client: MammothClient):
        await client.connectors.get_ds_config(
            connector_key="salesforce", connection_key="conn1", ds_config_key="dsc1"
        )
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/ds_configs/dsc1")

    async def test_update_ds_config_sends_patch_envelope(self, client: MammothClient):
        op = DsConfigPatchOp(
            op="replace",
            path=DsConfigPatchPath.QUERY,
            value={"query": "SELECT id FROM users", "ds_id": 10, "validate": True},
        )
        await client.connectors.update_ds_config(
            connector_key="postgres",
            connection_key="conn1",
            ds_config_key="dsc1",
            patch=[op],
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/ds_configs/dsc1")
        assert_json_body(
            client._request_json,
            {
                "patch": [
                    {
                        "op": "replace",
                        "path": "query",
                        "value": {"query": "SELECT id FROM users", "ds_id": 10, "validate": True},
                    }
                ]
            },
        )

    async def test_update_ds_config_rejects_empty_patch(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patch"):
            await client.connectors.update_ds_config(
                connector_key="postgres",
                connection_key="conn1",
                ds_config_key="dsc1",
                patch=[],
            )
        client._request_json.assert_not_called()

    async def test_delete_ds_config(self, client: MammothClient):
        await client.connectors.delete_ds_config(
            connector_key="salesforce", connection_key="conn1", ds_config_key="dsc1"
        )
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/ds_configs/dsc1")

    async def test_ds_config_delete_all_with_list(self, client: MammothClient):
        await client.connectors.ds_config_delete_all(
            connector_key="salesforce", connection_key="conn1", config_ids=["dsc1", "dsc2"]
        )
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/ds_configs")
        assert client._request_json.call_args.kwargs["params"] == {"config_ids": "dsc1,dsc2"}

    async def test_ds_config_delete_all_with_string(self, client: MammothClient):
        await client.connectors.ds_config_delete_all(
            connector_key="salesforce", connection_key="conn1", config_ids="dsc1,dsc2"
        )
        assert client._request_json.call_args.kwargs["params"] == {"config_ids": "dsc1,dsc2"}

    async def test_active_connectors(self, client: MammothClient):
        await client.connectors.active_connectors()
        assert_called_with_method_and_endpoint(client._request, "GET", "/active_connectors")


# ======================================================================
# DashboardsAPI
# ======================================================================


class TestDashboardsAPI:
    # ── list / get / delete / get_sources / get_analytics / get_by_url ───────

    async def test_list(self, client: MammothClient):
        await client.dashboards.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards")

    async def test_list_forwards_nullable_project_id(self, client: MammothClient):
        await client.dashboards.list(project_id=42)
        client._request_json.assert_called_once_with(
            "GET", "/dashboards", params={"project_id": 42}
        )

    async def test_get(self, client: MammothClient):
        await client.dashboards.get(dashboard_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards/5")

    async def test_delete(self, client: MammothClient):
        await client.dashboards.delete(dashboard_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/dashboards/5")

    @pytest.mark.parametrize("archived", [True, False])
    async def test_archive_sets_archived_state(self, client: MammothClient, archived: bool):
        await client.dashboards.archive(dashboard_id=5, archived=archived)
        # The route declares no response schema and answers with a non-dict
        # JSON value; the shape-checked wrapper would report outcome_unknown
        # for a write that committed.
        client._request.assert_called_once_with(
            "POST", "/dashboards/5/archive", json={"archived": archived}
        )

    async def test_archive_rejects_invalid_inputs(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.archive(dashboard_id=0, archived=True)
        with pytest.raises(MammothValidationError, match="archived"):
            await client.dashboards.archive(dashboard_id=5, archived="true")  # type: ignore[arg-type]
        client._request.assert_not_called()

    async def test_get_sources(self, client: MammothClient):
        await client.dashboards.get_sources()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards/sources")

    async def test_get_analytics(self, client: MammothClient):
        await client.dashboards.get_analytics(dashboard_id=5)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dashboards/5/analytics"
        )

    async def test_get_by_url(self, client: MammothClient):
        await client.dashboards.get_by_url(url="my-dashboard")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dashboards/url/my-dashboard"
        )

    async def test_get_draft_data_sends_widget_data_spec(self, client: MammothClient):
        # The route takes ``{"params": WidgetDataParams}``; a top-level ``sql``
        # body was rejected on release with HTTP 400 "params: Field required".
        await client.dashboards.get_draft_data(
            dashboard_id=5,
            widget_id="550e8400-e29b-41d4-a716-446655440000",
            global_filters={"region": "North"},
        )
        client._request_json.assert_called_once_with(
            "POST",
            "/dashboards/5/getDraftData",
            json={
                "params": {
                    "widget_id": "550e8400-e29b-41d4-a716-446655440000",
                    "global_filters": {"region": "North"},
                }
            },
        )

    async def test_get_publish_data_sends_widget_data_spec(self, client: MammothClient):
        await client.dashboards.get_publish_data(
            dashboard_id=5, widget_id="550e8400-e29b-41d4-a716-446655440000"
        )
        client._request_json.assert_called_once_with(
            "POST",
            "/dashboards/5/getPublishData",
            json={"params": {"widget_id": "550e8400-e29b-41d4-a716-446655440000"}},
        )

    async def test_widget_data_reads_reject_empty_widget_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="widget_id"):
            await client.dashboards.get_draft_data(dashboard_id=5, widget_id="")
        client._request_json.assert_not_called()

    # ── create_blank ─────────────────────────────────────────────────────────

    async def test_create_blank_sends_release_wire(self, client: MammothClient):
        await client.dashboards.create_blank(
            CreateBlankParams(dataview_id=42, style="presentation", title="Revenue")
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/v3/blank")
        assert_json_body(
            client._request_json,
            {
                "params": {
                    "dataview_id": 42,
                    "style": "presentation",
                    "title": "Revenue",
                }
            },
        )

    async def test_create_blank_rejects_nonpositive_dataview_before_request(
        self, client: MammothClient
    ):
        with pytest.raises(MammothValidationError, match="dataview_id"):
            await client.dashboards.create_blank({"dataview_id": 0})
        client._request_json.assert_not_called()

    # ── update ───────────────────────────────────────────────────────────────

    async def test_update_rename(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.TITLE, value="New Name"
        )
        await client.dashboards.update(dashboard_id=5, patch=[op])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/dashboards/5")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "title", "value": "New Name"}]},
        )

    async def test_update_theme(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.THEME, value="DARK_MODE"
        )
        await client.dashboards.update(dashboard_id=5, patch=[op])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "theme", "value": "DARK_MODE"}]},
        )

    async def test_update_intent(self, client: MammothClient):
        intent_value = "Show quarterly revenue by product line"
        op = DashboardPatchItem(
            op=DashboardPatchOp.ADD, path=DashboardPatchPath.INTENT, value=intent_value
        )
        await client.dashboards.update(dashboard_id=5, patch=[op])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "add", "path": "intent", "value": intent_value}]},
        )

    async def test_update_rejects_nonpositive_id(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.TITLE, value="x"
        )
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.update(dashboard_id=0, patch=[op])
        client._request_json.assert_not_called()

    async def test_update_rejects_empty_patch(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patch"):
            await client.dashboards.update(dashboard_id=5, patch=[])
        client._request_json.assert_not_called()

    async def test_update_rejects_short_intent_value(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.ADD, path=DashboardPatchPath.INTENT, value="too short"
        )
        with pytest.raises(MammothValidationError, match="intent"):
            await client.dashboards.update(dashboard_id=5, patch=[op])
        client._request_json.assert_not_called()

    # ── share ────────────────────────────────────────────────────────────────

    async def test_share_public(self, client: MammothClient):
        await client.dashboards.share(dashboard_id=5, type_of_auth=DashboardAuthType.PUBLIC)
        assert_called_with_method_and_endpoint(client._request, "POST", "/dashboards/5/share")
        assert_json_body(
            client._request,
            {"params": {"auth": {"type_of_auth": "public"}}},
        )

    async def test_share_mammoth_with_users(self, client: MammothClient):
        user = DashboardShareUser(
            email="alice@example.com", role=DashboardShareRole.EDITOR, shared=True
        )
        await client.dashboards.share(
            dashboard_id=5,
            type_of_auth=DashboardAuthType.MAMMOTH,
            users=[user],
        )
        assert_json_body(
            client._request,
            {
                "params": {
                    "auth": {
                        "type_of_auth": "mammoth",
                        "options": {
                            "users": [
                                {
                                    "email": "alice@example.com",
                                    "role": "dashboard_editor",
                                    "shared": True,
                                }
                            ]
                        },
                    }
                }
            },
        )

    async def test_share_password_type(self, client: MammothClient):
        await client.dashboards.share(dashboard_id=5, type_of_auth=DashboardAuthType.PASSWORD)
        assert_json_body(
            client._request,
            {"params": {"auth": {"type_of_auth": "password"}}},
        )

    async def test_share_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.share(dashboard_id=0, type_of_auth=DashboardAuthType.PUBLIC)
        client._request.assert_not_called()

    async def test_share_rejects_empty_user_email(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="email"):
            await client.dashboards.share(
                dashboard_id=5,
                type_of_auth=DashboardAuthType.MAMMOTH,
                users=[DashboardShareUser(email="", role=DashboardShareRole.VIEWER, shared=True)],
            )
        client._request.assert_not_called()

    # ── action ───────────────────────────────────────────────────────────────

    async def test_action_sync_no_params(self, client: MammothClient):
        await client.dashboards.action(dashboard_id=5, action=DashboardActionType.SYNC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/5/action")
        assert_json_body(client._request_json, {"action": "sync"})

    async def test_action_sync_scoped(self, client: MammothClient):
        await client.dashboards.action(
            dashboard_id=5, action=DashboardActionType.SYNC, params_view_id=42
        )
        assert_json_body(client._request_json, {"action": "sync", "params": {"view_id": 42}})

    async def test_action_publish_data(self, client: MammothClient):
        await client.dashboards.action(dashboard_id=5, action=DashboardActionType.PUBLISH_DATA)
        assert_json_body(client._request_json, {"action": "publish-data"})

    async def test_action_auto_sync(self, client: MammothClient):
        await client.dashboards.action(
            dashboard_id=5,
            action=DashboardActionType.AUTO_SYNC,
            params_enabled=True,
            params_view_id=42,
        )
        assert_json_body(
            client._request_json,
            {"action": "auto-sync", "params": {"enabled": True, "view_id": 42}},
        )

    async def test_action_auto_publish(self, client: MammothClient):
        await client.dashboards.action(
            dashboard_id=5, action=DashboardActionType.AUTO_PUBLISH, params_enabled=False
        )
        assert_json_body(
            client._request_json,
            {"action": "auto-publish", "params": {"enabled": False}},
        )

    async def test_action_delete_source(self, client: MammothClient):
        await client.dashboards.action(
            dashboard_id=5, action=DashboardActionType.DELETE_SOURCE, params_view_id=7
        )
        assert_json_body(
            client._request_json,
            {"action": "delete-source", "params": {"view_id": 7}},
        )

    async def test_action_rejects_nonpositive_dashboard_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.action(dashboard_id=0, action=DashboardActionType.SYNC)
        client._request_json.assert_not_called()

    async def test_action_auto_sync_requires_enabled(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="auto-sync"):
            await client.dashboards.action(dashboard_id=5, action=DashboardActionType.AUTO_SYNC)
        client._request_json.assert_not_called()

    async def test_action_auto_publish_requires_enabled(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="auto-publish"):
            await client.dashboards.action(dashboard_id=5, action=DashboardActionType.AUTO_PUBLISH)
        client._request_json.assert_not_called()

    async def test_action_delete_source_requires_view_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="delete-source"):
            await client.dashboards.action(dashboard_id=5, action=DashboardActionType.DELETE_SOURCE)
        client._request_json.assert_not_called()

    async def test_action_rejects_nonpositive_view_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="params_view_id"):
            await client.dashboards.action(
                dashboard_id=5, action=DashboardActionType.DELETE_SOURCE, params_view_id=0
            )
        client._request_json.assert_not_called()

    # ── cancel_generation / restore / trash ─────────────────────────────────────

    async def test_cancel_generation(self, client: MammothClient):
        await client.dashboards.cancel_generation(dashboard_id=5)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/5/cancel-generation"
        )

    async def test_cancel_generation_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.cancel_generation(dashboard_id=0)
        client._request_json.assert_not_called()

    async def test_restore(self, client: MammothClient):
        await client.dashboards.restore(dashboard_id=5)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/5/restore"
        )

    async def test_restore_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.restore(dashboard_id=0)
        client._request_json.assert_not_called()

    async def test_trash(self, client: MammothClient):
        await client.dashboards.trash(dashboard_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/5/trash")

    async def test_trash_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.trash(dashboard_id=0)
        client._request_json.assert_not_called()

    # ── job_by_url / published_data_by_url ──────────────────────────────────────

    async def test_job_by_url(self, client: MammothClient):
        await client.dashboards.job_by_url(url="my-dashboard", job_id=99)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dashboards/url/my-dashboard/jobs/99"
        )

    async def test_job_by_url_rejects_nonpositive_job_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="job_id"):
            await client.dashboards.job_by_url(url="my-dashboard", job_id=0)
        client._request_json.assert_not_called()

    async def test_published_data_by_url(self, client: MammothClient):
        body = {"params": {"widget_id": "w1"}}
        await client.dashboards.published_data_by_url(url="my-dashboard", body=body)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/url/my-dashboard/getPublishData"
        )
        assert_json_body(client._request_json, body)

    # ── widget_data / widget_data_by_url ─────────────────────────────────────────

    async def test_widget_data(self, client: MammothClient):
        body = {"widgets": [{"widget_id": "w1"}]}
        await client.dashboards.widget_data(dashboard_id=5, body=body)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/5/widgets/data"
        )
        assert_json_body(client._request_json, body)

    async def test_widget_data_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            await client.dashboards.widget_data(dashboard_id=0, body={})
        client._request_json.assert_not_called()

    async def test_widget_data_by_url(self, client: MammothClient):
        body = {"widgets": [{"widget_id": "w1"}]}
        await client.dashboards.widget_data_by_url(url="my-dashboard", body=body)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/url/my-dashboard/widgets/data"
        )
        assert_json_body(client._request_json, body)


# ======================================================================
# AutomationsAPI
# ======================================================================


_DT = datetime(2025, 1, 1, tzinfo=timezone.utc)

_SCHEDULE_CREATE_SPEC = ScheduleCreateSpec(
    rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=_DT),
    work_items=[
        WorkItemSpec(
            name=WorkItemName.PULL_CLOUD_DATA,
            execution_params=PullDataExecutionParams(
                schedule_type=ScheduleType.MOMENT,
                first_pull_at=FirstPullAt.NOW,
                on_refresh_action=OnRefreshAction.REPLACE,
            ),
            args=[10, 20],
        )
    ],
)

_SCHEDULE_CREATE_BODY = {
    "rrule": {"frequency": "daily", "start": "2025-01-01T00:00:00+00:00"},
    "work_items": [
        {
            "name": "pull_cloud_data",
            "execution_params": {
                "schedule_type": "moment",
                "first_pull_at": "now",
                "on_refresh_action": "replace",
            },
            "args": [10, 20],
        }
    ],
}

_SCHEDULE_PATCH_STATUS_ITEM = SchedulePatchItem(
    op="replace",
    path=SchedulePatchPath.STATUS,
    value=ScheduleStatus.PAUSE,
)

_SCHEDULE_PATCH_RRULE_ITEM = SchedulePatchItem(
    op="replace",
    path=SchedulePatchPath.RRULE,
    value=SchedulePatchValue(
        rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=_DT),
        work_items=[
            WorkItemSpec(
                name=WorkItemName.PULL_CLOUD_DATA,
                execution_params=PullDataExecutionParams(
                    schedule_type=ScheduleType.MOMENT,
                    first_pull_at=FirstPullAt.NOW,
                    on_refresh_action=OnRefreshAction.REPLACE,
                ),
                args=[5],
            )
        ],
    ),
)

_SCHEDULE_PATCH_RRULE_BODY = {
    "patch": [
        {
            "op": "replace",
            "path": "rrule",
            "value": {
                "rrule": {"frequency": "daily", "start": "2025-01-01T00:00:00+00:00"},
                "work_items": [
                    {
                        "name": "pull_cloud_data",
                        "execution_params": {
                            "schedule_type": "moment",
                            "first_pull_at": "now",
                            "on_refresh_action": "replace",
                        },
                        "args": [5],
                    }
                ],
            },
        }
    ]
}


class TestAutomationsAPI:
    async def test_list(self, client: MammothClient) -> None:
        await client.automations.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/automations")

    async def test_create(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=42)]),
        )
        await client.automations.create(
            name="Nightly",
            description="desc",
            tasks=[task],
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/automations")
        assert_json_body(
            client._request_json,
            {
                "name": "Nightly",
                "description": "desc",
                "tasks": [
                    {
                        "task_type": "run_data_retrieval",
                        "details": {"ds_details": [{"ds_id": 42}]},
                    }
                ],
                "conditions": [],
                "condition_mode": "and",
            },
        )

    async def test_create_empty_name_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=1)]),
        )
        with pytest.raises(MammothValidationError):
            await client.automations.create(name="", description="d", tasks=[task])
        client._request_json.assert_not_called()

    async def test_create_empty_tasks_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.automations.create(name="A", description="d", tasks=[])
        client._request_json.assert_not_called()

    async def test_create_task_missing_ds_details_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(),
        )
        with pytest.raises(MammothValidationError):
            await client.automations.create(name="A", description="d", tasks=[task])
        client._request_json.assert_not_called()

    async def test_create_task_missing_alert_fields_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.SEND_AN_ALERT,
            details=TaskDetailsSpec(alert_type=AlertType.EMAIL),
        )
        with pytest.raises(MammothValidationError):
            await client.automations.create(name="A", description="d", tasks=[task])
        client._request_json.assert_not_called()

    async def test_create_condition_at_specific_time_missing_interval_raises(
        self, client: MammothClient
    ) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=1)]),
        )
        cond = AutomationConditionSpec(
            condition_type=AutomationConditionType.AT_SPECIFIC_TIME,
            details=ConditionDetailsSpec(start_at=_DT),  # missing interval
        )
        with pytest.raises(MammothValidationError):
            await client.automations.create(
                name="A", description="d", tasks=[task], conditions=[cond]
            )
        client._request_json.assert_not_called()

    async def test_create_condition_by_month_day_out_of_range_raises(
        self, client: MammothClient
    ) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=1)]),
        )
        cond = AutomationConditionSpec(
            condition_type=AutomationConditionType.RUN_CONFIG,
            details=ConditionDetailsSpec(by_month_day=[32]),
        )
        with pytest.raises(MammothValidationError):
            await client.automations.create(
                name="A", description="d", tasks=[task], conditions=[cond]
            )
        client._request_json.assert_not_called()

    async def test_get(self, client: MammothClient) -> None:
        await client.automations.get(automation_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/automations/10")

    async def test_update_command_run(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.RUN, value={}
        )
        await client.automations.update(automation_id=10, patch=[patch_item])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/automations/10")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "command", "path": "run", "value": {}}]},
        )

    async def test_update_status_suspend(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE,
            path=AutomationPatchPath.STATUS,
            value=AutomationStatus.SUSPEND.value,
        )
        await client.automations.update(automation_id=10, patch=[patch_item])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "status", "value": "suspend"}]},
        )

    async def test_update_details(self, client: MammothClient) -> None:
        details = PatchAutomationDetails(name="Renamed")
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE, path=AutomationPatchPath.DETAILS, value=details
        )
        await client.automations.update(automation_id=10, patch=[patch_item])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "details", "value": {"name": "Renamed"}}]},
        )

    async def test_update_invalid_id_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.RUN, value={}
        )
        with pytest.raises(MammothValidationError):
            await client.automations.update(automation_id=0, patch=[patch_item])
        client._request_json.assert_not_called()

    async def test_update_empty_patch_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.automations.update(automation_id=10, patch=[])
        client._request_json.assert_not_called()

    async def test_update_command_wrong_path_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.STATUS, value={}
        )
        with pytest.raises(MammothValidationError):
            await client.automations.update(automation_id=10, patch=[patch_item])
        client._request_json.assert_not_called()

    async def test_update_status_invalid_value_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE,
            path=AutomationPatchPath.STATUS,
            value="active",
        )
        with pytest.raises(MammothValidationError):
            await client.automations.update(automation_id=10, patch=[patch_item])
        client._request_json.assert_not_called()

    async def test_update_details_all_none_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE,
            path=AutomationPatchPath.DETAILS,
            value=PatchAutomationDetails(),
        )
        with pytest.raises(MammothValidationError):
            await client.automations.update(automation_id=10, patch=[patch_item])
        client._request_json.assert_not_called()

    async def test_delete(self, client: MammothClient) -> None:
        await client.automations.delete(automation_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/automations/10")

    async def test_restore(self, client: MammothClient) -> None:
        await client.automations.restore(automation_id=10)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/automations/10/restore"
        )

    async def test_trash(self, client: MammothClient) -> None:
        await client.automations.trash(automation_id=10)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/automations/10/trash"
        )

    async def test_list_schedules(self, client: MammothClient) -> None:
        await client.automations.list_schedules()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules")

    async def test_create_schedule(self, client: MammothClient) -> None:
        await client.automations.create_schedule(spec=_SCHEDULE_CREATE_SPEC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")
        assert_json_body(client._request_json, _SCHEDULE_CREATE_BODY)

    async def test_create_schedule_invalid_interval_raises(self, client: MammothClient) -> None:
        spec = ScheduleCreateSpec(
            rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=_DT, interval=-1)
        )
        with pytest.raises(MammothValidationError):
            await client.automations.create_schedule(spec=spec)
        client._request_json.assert_not_called()

    async def test_update_schedule(self, client: MammothClient) -> None:
        await client.automations.update_schedule(schedule_id=5, patch=[_SCHEDULE_PATCH_RRULE_ITEM])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/schedules/5")
        assert_json_body(client._request_json, _SCHEDULE_PATCH_RRULE_BODY)

    async def test_update_schedule_status(self, client: MammothClient) -> None:
        await client.automations.update_schedule(schedule_id=5, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "status", "value": "pause"}]},
        )

    async def test_update_schedule_invalid_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.automations.update_schedule(
                schedule_id=0, patch=[_SCHEDULE_PATCH_STATUS_ITEM]
            )
        client._request_json.assert_not_called()

    async def test_update_schedule_empty_patch_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.automations.update_schedule(schedule_id=5, patch=[])
        client._request_json.assert_not_called()

    async def test_update_schedule_invalid_op_raises(self, client: MammothClient) -> None:
        bad_item = SchedulePatchItem(op="add", path=SchedulePatchPath.STATUS, value="pause")
        with pytest.raises(MammothValidationError):
            await client.automations.update_schedule(schedule_id=5, patch=[bad_item])
        client._request_json.assert_not_called()

    async def test_update_schedule_status_invalid_value_raises(self, client: MammothClient) -> None:
        bad_item = SchedulePatchItem(op="replace", path=SchedulePatchPath.STATUS, value="stop")
        with pytest.raises(MammothValidationError):
            await client.automations.update_schedule(schedule_id=5, patch=[bad_item])
        client._request_json.assert_not_called()

    async def test_delete_schedule(self, client: MammothClient) -> None:
        await client.automations.delete_schedule(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/schedules/5")


# ======================================================================
# SchedulesAPI
# ======================================================================


class TestSchedulesAPI:
    async def test_list(self, client: MammothClient) -> None:
        await client.schedules.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules")

    async def test_get(self, client: MammothClient) -> None:
        await client.schedules.get(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules/5")

    async def test_create(self, client: MammothClient) -> None:
        """SchedulesAPI.create produces the same wire body as AutomationsAPI.create_schedule."""
        await client.schedules.create(spec=_SCHEDULE_CREATE_SPEC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")
        assert_json_body(client._request_json, _SCHEDULE_CREATE_BODY)

    async def test_create_with_project_id(self, client: MammothClient) -> None:
        await client.schedules.create(spec=_SCHEDULE_CREATE_SPEC, project_id=99)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")
        assert_json_body(client._request_json, _SCHEDULE_CREATE_BODY)

    async def test_create_invalid_project_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.schedules.create(spec=_SCHEDULE_CREATE_SPEC, project_id=0)
        client._request_json.assert_not_called()

    async def test_create_invalid_interval_raises(self, client: MammothClient) -> None:
        spec = ScheduleCreateSpec(
            rrule=RruleSpec(frequency=RruleFrequency.HOURLY, start=_DT, interval=0)
        )
        with pytest.raises(MammothValidationError):
            await client.schedules.create(spec=spec)
        client._request_json.assert_not_called()

    async def test_update(self, client: MammothClient) -> None:
        """SchedulesAPI.update produces the same wire body as AutomationsAPI.update_schedule."""
        await client.schedules.update(schedule_id=5, patch=[_SCHEDULE_PATCH_RRULE_ITEM])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/schedules/5")
        assert_json_body(client._request_json, _SCHEDULE_PATCH_RRULE_BODY)

    async def test_update_status(self, client: MammothClient) -> None:
        await client.schedules.update(schedule_id=5, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "status", "value": "pause"}]},
        )

    async def test_update_invalid_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.schedules.update(schedule_id=-1, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        client._request_json.assert_not_called()

    async def test_update_invalid_project_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.schedules.update(
                schedule_id=5, patch=[_SCHEDULE_PATCH_STATUS_ITEM], project_id=0
            )
        client._request_json.assert_not_called()

    async def test_update_empty_patch_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            await client.schedules.update(schedule_id=5, patch=[])
        client._request_json.assert_not_called()

    async def test_update_invalid_op_raises(self, client: MammothClient) -> None:
        bad_item = SchedulePatchItem(op="remove", path=SchedulePatchPath.RRULE, value="pause")
        with pytest.raises(MammothValidationError):
            await client.schedules.update(schedule_id=5, patch=[bad_item])
        client._request_json.assert_not_called()

    async def test_delete(self, client: MammothClient) -> None:
        await client.schedules.delete(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/schedules/5")


# ======================================================================
# BatchesAPI
# ======================================================================


class TestBatchesAPI:
    async def test_list(self, client: MammothClient):
        await client.batches.list(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets/500/batches")

    async def test_get(self, client: MammothClient):
        await client.batches.get(dataset_id=500, batch_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/batches/10")

    async def test_create_sends_correct_body(self, client: MammothClient):
        await client.batches.create(
            dataset_id=500,
            source_id=42,
            mapping={"src_col": "dst_col"},
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/batches"
        )
        assert_json_body(
            client._request_json,
            {
                # BatchesPostRequest: mapping is a list of ColumnNameMapping items.
                "source_id": 42,
                "mapping": [
                    {
                        "source_c_name": "src_col",
                        "destination_c_name": "dst_col",
                        "expected_destination_c_type": "TEXT",
                    }
                ],
                "delete_source_ds": False,
            },
        )

    async def test_create_with_optional_fields(self, client: MammothClient):
        await client.batches.create(
            dataset_id=500,
            source_id=42,
            mapping={"a": "b"},
            is_validation_required=True,
            delete_source_ds=True,
        )
        assert_json_body(
            client._request_json,
            {
                "source_id": 42,
                "mapping": [
                    {
                        "source_c_name": "a",
                        "destination_c_name": "b",
                        "expected_destination_c_type": "TEXT",
                    }
                ],
                "validate_only": True,
                "delete_source_ds": True,
            },
        )

    async def test_create_rejects_nonpositive_source_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="source_id"):
            await client.batches.create(dataset_id=500, source_id=0, mapping={"a": "b"})
        client._request_json.assert_not_called()

    async def test_create_rejects_empty_mapping(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="mapping"):
            await client.batches.create(dataset_id=500, source_id=1, mapping={})
        client._request_json.assert_not_called()

    async def test_update_wraps_patch_envelope(self, client: MammothClient):
        """PROD BUG FIX: SDK must wrap patch ops in {"patch": [...]} envelope."""
        patch_ops = [{"op": "replace", "value": {"approve": [101, 102]}}]
        await client.batches.update(dataset_id=500, patch=patch_ops)
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/datasets/500/batches"
        )
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "value": {"approve": [101, 102]}}]},
        )

    async def test_update_remove_op(self, client: MammothClient):
        patch_ops = [{"op": "remove", "value": [101, 102]}]
        await client.batches.update(dataset_id=500, patch=patch_ops)
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "remove", "value": [101, 102]}]},
        )

    async def test_update_rejects_empty_patch(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patch"):
            await client.batches.update(dataset_id=500, patch=[])
        client._request_json.assert_not_called()

    async def test_update_rejects_invalid_op(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="op"):
            await client.batches.update(dataset_id=500, patch=[{"op": "add", "value": [1]}])
        client._request_json.assert_not_called()

    async def test_delete(self, client: MammothClient):
        await client.batches.delete(dataset_id=500, batch_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/batches/10")

    async def test_bulk_delete_no_ids(self, client: MammothClient):
        await client.batches.bulk_delete(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/datasets/500/batches"
        )
        assert client._request_json.call_args.kwargs.get("params") is None

    async def test_bulk_delete_with_ids(self, client: MammothClient):
        await client.batches.bulk_delete(dataset_id=500, ids=[10, 11])
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/datasets/500/batches"
        )
        assert client._request_json.call_args.kwargs["params"] == {"ids": "10,11"}


# ======================================================================
# BrowseAPI
# ======================================================================


class TestBrowseAPI:
    async def test_workspaces(self, client: MammothClient):
        await client.browse.workspaces()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces")

    async def test_projects(self, client: MammothClient):
        await client.browse.projects()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/projects")

    async def test_datasets(self, client: MammothClient):
        await client.browse.datasets()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets")

    async def test_dataviews(self, client: MammothClient):
        await client.browse.dataviews(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/dataviews"
        )

    @pytest.mark.parametrize(
        "browse, endpoint",
        [
            (lambda b: b.workspaces(fields="__min", limit=25, offset=50), "/workspaces"),
            (lambda b: b.projects(fields="__min", limit=25, offset=50), "/projects"),
            (lambda b: b.datasets(fields="__min", limit=25, offset=50), "/datasets"),
            (
                lambda b: b.dataviews(dataset_id=500, fields="__min", limit=25, offset=50),
                "/datasets/500/dataviews",
            ),
        ],
    )
    async def test_a_browse_can_ask_for_one_page_of_smaller_records(
        self, client: MammothClient, browse, endpoint
    ):
        """A caller reading a list into a model's context pays for every field."""
        await browse(client.browse)
        assert_called_with_method_and_endpoint(client._request_json, "GET", endpoint)
        assert client._request_json.call_args.kwargs["params"] == {
            "fields": "__min",
            "limit": 25,
            "offset": 50,
        }

    async def test_a_browse_that_asks_for_nothing_leaves_the_route_its_defaults(
        self, client: MammothClient
    ):
        await client.browse.datasets()
        assert client._request_json.call_args.kwargs.get("params") is None

    async def test_root(self, client: MammothClient):
        await client.browse.root()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/browse")
        assert client._request_json.call_args.kwargs.get("params") is None

    async def test_root_with_filters(self, client: MammothClient):
        await client.browse.root(name="foo", browse_type="project", limit=10, offset=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/browse")
        assert client._request_json.call_args.kwargs["params"] == {
            "name": "foo",
            "browse_type": "project",
            "offset": 5,
            "limit": 10,
        }


# ======================================================================
# ClientAppsAPI
# ======================================================================


class TestClientAppsAPI:
    async def test_list(self, client: MammothClient):
        # await client_apps.list() returns Pydantic model
        client._request_json = AsyncMock(
            return_value={
                "result": [],
            }
        )
        await client.client_apps.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/clientapps")

    async def test_create(self, client: MammothClient):
        # await client_apps.create() returns Pydantic model with ValueWrapper fields
        client._request_json = AsyncMock(
            return_value={
                "client_app": {
                    "client_key": {"value": "ck1"},
                    "app_name": {"value": "MyApp"},
                },
            }
        )
        await client.client_apps.create(app_name="MyApp")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/clientapps")

    async def test_get(self, client: MammothClient):
        # await client_apps.get() returns ClientAppSchema with ValueWrapper fields
        client._request_json = AsyncMock(
            return_value={
                "client_key": {"value": "ck1"},
                "app_name": {"value": "MyApp"},
            }
        )
        await client.client_apps.get(client_key="ck1")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/clientapps/ck1")

    async def test_delete(self, client: MammothClient):
        await client.client_apps.delete(client_key="ck1")
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/clientapps/ck1")


# ======================================================================
# ExternalKeysAPI
# ======================================================================


class TestExternalKeysAPI:
    async def test_list(self, client: MammothClient):
        await client.external_keys.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/external_keys")

    async def test_get(self, client: MammothClient):
        await client.external_keys.get(key_id=3)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/external_keys/3")

    async def test_create_minimal(self, client: MammothClient):
        await client.external_keys.create(
            key_type=ExternalKeyType.ANTHROPIC,
            key_name="Claude key",
            secure_key="sk-ant-123",
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/external_keys")
        assert_json_body(
            client._request_json,
            {"key_type": "anthropic", "key_name": "Claude key", "secure_key": "sk-ant-123"},
        )

    async def test_create_with_model_settings(self, client: MammothClient):
        await client.external_keys.create(
            key_type=ExternalKeyType.OPEN_AI,
            key_name="GPT key",
            secure_key="sk-123",
            description="prod",
            model_id="gpt-5.4",
            model_settings=ModelConfigSpec(web_search=True, thinking_budget=2048),
        )
        # model_settings emits the aliased wire key "model_config" with only set fields.
        assert_json_body(
            client._request_json,
            {
                "key_type": "open_ai",
                "key_name": "GPT key",
                "secure_key": "sk-123",
                "description": "prod",
                "model_id": "gpt-5.4",
                "model_config": {"web_search": True, "thinking_budget": 2048},
            },
        )

    async def test_create_rejects_empty_name(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="key_name"):
            await client.external_keys.create(
                key_type=ExternalKeyType.GEMINI, key_name="", secure_key="abc"
            )
        client._request_json.assert_not_called()

    async def test_create_rejects_short_secure_key(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="secure_key"):
            await client.external_keys.create(
                key_type=ExternalKeyType.GROK, key_name="k", secure_key="ab"
            )
        client._request_json.assert_not_called()

    async def test_create_model_settings_requires_model_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="model_id"):
            await client.external_keys.create(
                key_type=ExternalKeyType.OPEN_AI,
                key_name="k",
                secure_key="abc",
                model_settings=ModelConfigSpec(web_search=True),
            )
        client._request_json.assert_not_called()

    async def test_delete(self, client: MammothClient):
        await client.external_keys.delete(key_id=3)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/external_keys/3")


# ======================================================================
# ActivityLogsAPI
# ======================================================================


class TestActivityLogsAPI:
    async def test_list(self, client: MammothClient):
        await client.activity_logs.list()
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/activity_log")

    async def test_export(self, client: MammothClient):
        await client.activity_logs.export()
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/activity_log/export")


# ======================================================================
# AddonsAPI
# ======================================================================


class TestAddonsAPI:
    async def test_add_connector_single(self, client: MammothClient):
        await client.addons.add_connector(connector_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/connectors")
        assert_json_body(client._request_json, {"connector_id": 42})

    async def test_add_connector_bulk(self, client: MammothClient):
        await client.addons.add_connector(connector_ids=[42, 43])
        assert_json_body(client._request_json, {"connector_ids": [42, 43]})

    async def test_remove_connector_single(self, client: MammothClient):
        await client.addons.remove_connector(connector_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/connectors")
        assert_json_body(client._request_json, {"connector_id": 42})

    async def test_connector_requires_exactly_one(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="exactly one"):
            await client.addons.add_connector()
        with pytest.raises(MammothValidationError, match="exactly one"):
            await client.addons.add_connector(connector_id=1, connector_ids=[2])
        client._request_json.assert_not_called()

    async def test_connector_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="positive"):
            await client.addons.add_connector(connector_id=0)
        with pytest.raises(MammothValidationError, match="positive"):
            await client.addons.add_connector(connector_ids=[1, -2])
        client._request_json.assert_not_called()

    async def test_connector_rejects_empty_list(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="non-empty"):
            await client.addons.add_connector(connector_ids=[])
        client._request_json.assert_not_called()

    async def test_add_storage(self, client: MammothClient):
        await client.addons.add_storage(additional_storage_gb=50)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/storage")
        assert_json_body(client._request_json, {"additional_storage_gb": 50})

    async def test_remove_storage(self, client: MammothClient):
        await client.addons.remove_storage(removal_storage_gb=20)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/storage")
        assert_json_body(client._request_json, {"removal_storage_gb": 20})

    async def test_storage_rejects_nonpositive(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="positive"):
            await client.addons.add_storage(additional_storage_gb=0)
        with pytest.raises(MammothValidationError, match="positive"):
            await client.addons.remove_storage(removal_storage_gb=-5)
        client._request_json.assert_not_called()

    async def test_add_users(self, client: MammothClient):
        await client.addons.add_users(user_count=5)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/users")
        assert_json_body(client._request_json, {"user_count": 5})

    async def test_add_users_defaults_to_one(self, client: MammothClient):
        await client.addons.add_users()
        assert_json_body(client._request_json, {"user_count": 1})

    async def test_remove_users(self, client: MammothClient):
        await client.addons.remove_users(user_count=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/users")
        assert_json_body(client._request_json, {"user_count": 5})

    async def test_users_rejects_nonpositive(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="positive"):
            await client.addons.add_users(user_count=0)
        with pytest.raises(MammothValidationError, match="positive"):
            await client.addons.remove_users(user_count=-1)
        client._request_json.assert_not_called()


# ======================================================================
# ReportsAPI
# ======================================================================


class TestReportsAPI:
    async def test_list(self, client: MammothClient):
        await client.reports.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/reports")


# ======================================================================
# UserProfileAPI
# ======================================================================


class TestUserProfileAPI:
    async def test_get(self, client: MammothClient):
        await client.user_profile.get()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/self")

    async def test_update(self, client: MammothClient):
        # SelfPatchData: the backend takes a JSON-Patch envelope keyed by
        # `path` (first_name/last_name/password/mfa), not a flat field dict.
        await client.user_profile.update(first_name="Alice", last_name="Doe")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/self")
        assert_json_body(
            client._request_json,
            {
                "patch": [
                    {"op": "replace", "path": "first_name", "value": "Alice"},
                    {"op": "replace", "path": "last_name", "value": "Doe"},
                ]
            },
        )

    async def test_update_one_name_part(self, client: MammothClient):
        await client.user_profile.update(first_name="Alice")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "first_name", "value": "Alice"}]},
        )

    async def test_update_requires_a_name_part(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="first_name.*last_name"):
            await client.user_profile.update()
        client._request_json.assert_not_called()

    async def test_change_password(self, client: MammothClient):
        await client.user_profile.change_password(current_password="old", new_password="new")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/change_password")

    async def test_get_preferences(self, client: MammothClient):
        await client.user_profile.get_preferences()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/preferences")

    async def test_update_preferences(self, client: MammothClient):
        # PreferencesPatchRequest: patch of replace ops on dotted preference paths.
        await client.user_profile.update_preferences(**{"GLOBAL.PREFERENCES.THEME": "dark"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/preferences")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "GLOBAL.PREFERENCES.THEME", "value": "dark"}]},
        )


# ======================================================================
# WorkspaceAPI
# ======================================================================


class TestWorkspaceAPI:
    async def test_list(self, client: MammothClient):
        await client.workspaces.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces")

    async def test_get(self, client: MammothClient):
        await client.workspaces.get()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces/1")

    async def test_update_name(self, client: MammothClient):
        op = WorkspacePatchOp(op="replace", path=WorkspacePatchPath.NAME, value="Acme Corp")
        await client.workspaces.update(patches=[op])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/workspaces/1")
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "name", "value": "Acme Corp"}]},
        )

    async def test_update_billing_cycle(self, client: MammothClient):
        op = WorkspacePatchOp(
            op="replace", path=WorkspacePatchPath.BILLING_CYCLE, value=BillingCycle.YEARLY
        )
        await client.workspaces.update(patches=[op])
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "billing_cycle", "value": "yearly"}]},
        )

    async def test_update_plan_id(self, client: MammothClient):
        op = WorkspacePatchOp(op="replace", path=WorkspacePatchPath.PLAN_ID, value=3)
        await client.workspaces.update(patches=[op])
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "plan_id", "value": 3}]},
        )

    async def test_update_rejects_empty_patches(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patches"):
            await client.workspaces.update(patches=[])
        client._request_json.assert_not_called()

    async def test_update_rejects_name_too_long(self, client: MammothClient):
        with pytest.raises(ValueError, match="name"):
            WorkspacePatchOp(op="replace", path=WorkspacePatchPath.NAME, value="x" * 51)

    async def test_update_rejects_invalid_billing_cycle(self, client: MammothClient):
        with pytest.raises(ValueError, match="billing_cycle"):
            WorkspacePatchOp(op="replace", path=WorkspacePatchPath.BILLING_CYCLE, value="quarterly")

    async def test_delete(self, client: MammothClient):
        await client.workspaces.delete()
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/workspaces/1")

    async def test_reactivate(self, client: MammothClient):
        await client.workspaces.reactivate()
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/workspaces/1/reactivate"
        )

    async def test_list_users(self, client: MammothClient):
        await client.workspaces.list_users()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces/1/users")

    async def test_list_users_forwards_fields(self, client: MammothClient):
        """``fields=__full`` adds ``user_roles`` and ``status`` per the backend
        (apiv2/apiv2/workspaces/user_schema.py:29); the SDK must pass it through."""
        await client.workspaces.list_users(fields="__full")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces/1/users")
        assert client._request_json.call_args.kwargs["params"] == {"fields": "__full"}

    async def test_get_user(self, client: MammothClient):
        client._request_json.return_value = {
            "users": [{"id": 5, "email": "a@x.io"}, {"id": 6, "email": "b@x.io"}]
        }
        user = await client.workspaces.get_user(user_id="6")
        assert user == {"id": 6, "email": "b@x.io"}
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces/1/users")
        assert client._request_json.call_args.kwargs["params"] == {"fields": "__full"}

    async def test_update_user_sends_patch_envelope(self, client: MammothClient):
        op = UserRolePatchOp(op="replace", path="role", value=WorkspaceRoleType.WORKSPACE_ADMIN)
        await client.workspaces.update_user(user_id="u1", patches=[op])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/users/u1")
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "role", "value": "workspace_admin"}]},
        )

    async def test_update_user_rejects_empty_user_id(self, client: MammothClient):
        op = UserRolePatchOp(op="replace", path="role", value=WorkspaceRoleType.WORKSPACE_MEMBER)
        with pytest.raises(MammothValidationError, match="user_id"):
            await client.workspaces.update_user(user_id="", patches=[op])
        client._request_json.assert_not_called()

    async def test_update_user_rejects_empty_patches(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patches"):
            await client.workspaces.update_user(user_id="u1", patches=[])
        client._request_json.assert_not_called()

    async def test_update_user_rejects_invalid_role(self, client: MammothClient):
        with pytest.raises(ValueError):
            UserRolePatchOp(op="replace", path="role", value="admin")


# ======================================================================
# AIAPI
# ======================================================================


class TestAIAPI:
    async def test_generate_profile(self, client: MammothClient):
        await client.ai.generate_profile(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/profile_generation")

    async def test_generate_data_sends_correct_body(self, client: MammothClient):
        await client.ai.generate_data(
            dataview_id=42,
            prompt="Generate realistic sales data",
            no_of_rows=25,
            dataset_id=500,
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/data/generate")
        assert_json_body(
            client._request_json,
            {"prompt": "Generate realistic sales data", "no_of_rows": 25},
        )

    async def test_generate_data_with_columns(self, client: MammothClient):
        await client.ai.generate_data(
            dataview_id=42,
            prompt="Generate sales data",
            no_of_rows=5,
            columns=["product", "revenue"],
            dataset_id=500,
        )
        assert_json_body(
            client._request_json,
            {
                "prompt": "Generate sales data",
                "no_of_rows": 5,
                "columns": ["product", "revenue"],
            },
        )

    async def test_generate_data_rejects_empty_prompt(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="prompt"):
            await client.ai.generate_data(dataview_id=42, prompt="", dataset_id=500)
        client._request_json.assert_not_called()

    async def test_generate_data_rejects_rows_too_low(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="no_of_rows"):
            await client.ai.generate_data(
                dataview_id=42, prompt="Generate data", no_of_rows=0, dataset_id=500
            )
        client._request_json.assert_not_called()

    async def test_generate_data_rejects_rows_too_high(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="no_of_rows"):
            await client.ai.generate_data(
                dataview_id=42, prompt="Generate data", no_of_rows=101, dataset_id=500
            )
        client._request_json.assert_not_called()

    async def test_get_data_gen_info(self, client: MammothClient):
        await client.ai.get_data_gen_info(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/data/generate")

    async def test_generate_sql(self, client: MammothClient):
        # The route requires the dataset_id query parameter.
        await client.ai.generate_sql(intent="count employees", dataset_id=48)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/sql_generation")
        assert client._request_json.call_args.kwargs["params"] == {"dataset_id": 48}
        with pytest.raises(MammothValidationError, match="dataset_id"):
            await client.ai.generate_sql(intent="count employees")

    async def test_generate_profile_sends_action(self, client: MammothClient):
        await client.ai.generate_profile(dataview_id=42, dataset_id=500, action="data_quality")
        assert client._request_json.call_args.kwargs["json"] == {
            "params": {"action": "data_quality"}
        }
        with pytest.raises(MammothValidationError, match="action"):
            await client.ai.generate_profile(dataview_id=42, dataset_id=500, action="profile")

    async def test_get_suggestions(self, client: MammothClient):
        await client.ai.get_suggestions(
            suggestion_type="generate_task", params={"prompt": "Filter Price > 100"}, dataview_id=73
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/suggestions")
        kwargs = client._request_json.call_args.kwargs
        assert kwargs["json"] == {
            "suggestion_type": "generate_task",
            "params": {"prompt": "Filter Price > 100"},
        }
        assert kwargs["params"] == {"dataview_id": 73}

    async def test_get_suggestions_requires_type_and_params(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="suggestion_type"):
            await client.ai.get_suggestions()
        with pytest.raises(MammothValidationError, match="params"):
            await client.ai.get_suggestions(suggestion_type="dashboards")
        client._request_json.assert_not_called()

    async def test_query_gen(self, client: MammothClient):
        await client.ai.query_gen(connector_key="sf", connection_key="conn1", query="list tables")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connections/conn1/chat"
        )
        assert client._request_json.call_args.kwargs["json"] == {"query": "list tables"}

    async def test_status(self, client: MammothClient):
        await client.ai.status(connector_key="sf", connection_key="conn1")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/connections/conn1/chat"
        )

    async def test_condition_generate(self, client: MammothClient):
        await client.ai.condition_generate(intent="rows where amount > 100", dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/sql_generation/condition"
        )
        assert client._request_json.call_args.kwargs["params"] == {"dataset_id": 500}
        assert_json_body(
            client._request_json,
            {"params": {"intent": "rows where amount > 100"}},
        )

    async def test_condition_generate_with_optional_fields(self, client: MammothClient):
        await client.ai.condition_generate(
            intent="rows where amount > 100",
            dataset_id=500,
            dataview_id=42,
            sequence_number=3,
        )
        assert client._request_json.call_args.kwargs["params"] == {
            "dataset_id": 500,
            "dataview_id": 42,
        }
        assert_json_body(
            client._request_json,
            {"params": {"intent": "rows where amount > 100", "sequence_number": 3}},
        )

    async def test_expression_generate(self, client: MammothClient):
        await client.ai.expression_generate(intent="total revenue", mode="metric", dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/sql_generation/expression"
        )
        assert_json_body(
            client._request_json,
            {"params": {"intent": "total revenue", "mode": "metric"}},
        )

    async def test_expression_generate_rejects_invalid_mode(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="mode"):
            await client.ai.expression_generate(
                intent="total revenue", mode="bogus", dataset_id=500
            )
        client._request_json.assert_not_called()

    async def test_retention_condition_generate(self, client: MammothClient):
        await client.ai.retention_condition(
            dataset_id=0, mode="generate", intent="completed payments older than 90 days"
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/sql_generation/retention_policy"
        )
        assert client._request_json.call_args.kwargs["params"] == {"dataset_id": 0}
        assert_json_body(
            client._request_json,
            {
                "mode": "generate",
                "intent": "completed payments older than 90 days",
                "condition_sql": None,
            },
        )

    async def test_retention_condition_test(self, client: MammothClient):
        await client.ai.retention_condition(
            dataset_id=500, mode="test", condition_sql="status = 'completed'"
        )
        assert_json_body(
            client._request_json,
            {"mode": "test", "intent": None, "condition_sql": "status = 'completed'"},
        )

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"dataset_id": 500, "mode": "other", "intent": "x"},
            {"dataset_id": 500, "mode": "generate"},
            {"dataset_id": 500, "mode": "test"},
            {"dataset_id": 500, "mode": "generate", "intent": "x", "condition_sql": "y"},
            {"dataset_id": 500, "mode": "test", "condition_sql": "y", "intent": "x"},
            {"dataset_id": 500, "mode": "test", "condition_sql": "y", "project_id": 0},
            {"dataset_id": 500, "mode": "test", "condition_sql": "y", "project_id": -1},
            {"dataset_id": 500, "mode": "test", "condition_sql": "y", "project_id": True},
        ],
    )
    async def test_retention_condition_rejects_invalid_payload(
        self, client: MammothClient, kwargs: dict[str, object]
    ):
        with pytest.raises(MammothValidationError, match="mode|intent|condition_sql|project_id"):
            await client.ai.retention_condition(**kwargs)
        client._request_json.assert_not_called()


class TestUrlScopedJobWait:
    async def test_wait_for_job_by_url_polls_the_url_scoped_route(self, client: MammothClient):
        # Published-dashboard jobs answer 4PERM002 on GET /jobs/{id}; the
        # URL-scoped job route is the only readable observer for them.
        client._request_json = AsyncMock(
            return_value={"job": {"id": 313, "status": "success", "response": {"ok": 1}}}
        )
        job = await client.dashboards.wait_for_job_by_url("IuZl5tk5", 313, timeout=5)
        assert job["status"] == "success"
        client._request_json.assert_called_once_with("GET", "/dashboards/url/IuZl5tk5/jobs/313")

    async def test_wait_if_job_uses_custom_fetch(self):
        with patch("mammoth.client.httpx.AsyncClient"):
            client = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
        client._request_json = AsyncMock(return_value={})
        seen: list[int] = []

        async def fetch(job_id: int, remaining: float) -> dict:
            seen.append(job_id)
            return {"id": job_id, "status": "success", "response": {"value": 58824}}

        assert await client.wait_if_job({"job_id": 311}, timeout=5, fetch=fetch) == {"value": 58824}
        assert seen == [311]
        client._request_json.assert_not_called()


class TestProjectsPagination:
    """The projects route caps ``limit`` at 100; ``list_all`` walks the pages."""

    @staticmethod
    def _page(start: int, count: int, next_token: str) -> dict:
        return {
            "projects": [{"id": i, "name": f"p{i}"} for i in range(start, start + count)],
            "limit": 100,
            "offset": start,
            "next": next_token,
        }

    async def test_list_sends_offset_only_when_nonzero(self, client: MammothClient):
        await client.projects.list(limit=50)
        assert client._request_json.call_args.kwargs["params"] == {
            "fields": "id,name",
            "limit": 50,
        }
        client._request_json.reset_mock()
        await client.projects.list(limit=50, offset=50)
        assert client._request_json.call_args.kwargs["params"] == {
            "fields": "id,name",
            "limit": 50,
            "offset": 50,
        }

    async def test_list_all_follows_full_pages(self, client: MammothClient):
        client._request_json = AsyncMock(
            side_effect=[
                self._page(0, 100, "?offset=100"),
                self._page(100, 100, "?offset=200"),
                self._page(200, 7, ""),
            ]
        )
        projects = await client.projects.list_all()
        assert len(projects) == 207
        assert [
            c.kwargs["params"].get("offset", 0) for c in client._request_json.call_args_list
        ] == [
            0,
            100,
            200,
        ]

    async def test_list_all_stops_when_the_server_ignores_offset(self, client: MammothClient):
        client._request_json = AsyncMock(
            side_effect=[self._page(0, 100, ""), self._page(0, 100, "")]
        )
        projects = await client.projects.list_all()
        assert len(projects) == 100
        assert client._request_json.call_count == 2

    async def test_get_by_name_sees_past_the_first_page(self, client: MammothClient):
        second = self._page(100, 1, "")
        second["projects"] = [{"id": 100, "name": "From Claude"}]
        client._request_json = AsyncMock(side_effect=[self._page(0, 100, "?offset=100"), second])
        assert await client.projects.get(project="From Claude") == {
            "id": 100,
            "name": "From Claude",
        }
