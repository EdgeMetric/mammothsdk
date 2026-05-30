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
from unittest.mock import MagicMock, patch

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
    DashboardActionType,
    DashboardAuthType,
    DashboardPatchItem,
    DashboardPatchOp,
    DashboardPatchPath,
    DashboardShareRole,
    DashboardShareUser,
)
from mammoth.models.external_keys import ExternalKeyType, ModelConfigSpec
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
    with patch("mammoth.client.requests.Session"):
        c = MammothClient(api_key="key", api_secret="secret", workspace_id=1)
    c.project_id = 100
    c._request_json = MagicMock(return_value={})
    c._request_list = MagicMock(return_value=[])
    c._request = MagicMock(return_value={})
    c._wait_if_job = MagicMock(side_effect=lambda r, **kw: r)
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
    def test_list(self, client: MammothClient):
        client.projects.list()
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects"
        )

    def test_get_by_id(self, client: MammothClient):
        # projects.get() calls list() internally and filters
        client._request_json.return_value = {"projects": [{"id": 42, "name": "Test Project"}]}
        result = client.projects.get(project=42)
        assert result["id"] == 42
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/workspaces/1/projects"
        )

    def test_create(self, client: MammothClient):
        client.projects.create(name="New Project")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/workspaces/1/projects"
        )

    def test_update(self, client: MammothClient):
        client.projects.update(project_id=42, name="Renamed")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/projects/42")

    def test_delete(self, client: MammothClient):
        client.projects.delete(project_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/workspaces/1/projects"
        )

    def test_browse(self, client: MammothClient):
        client.projects.browse(project_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/projects/42/browse")

    def test_add_users(self, client: MammothClient):
        client.projects.add_users(project_id=42, user_ids=["u1", "u2"])
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/projects/42/users")

    def test_remove_users(self, client: MammothClient):
        client.projects.remove_users(project_id=42, user_ids=["u1"])
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/projects/42/users")

    def test_bulk_update(self, client: MammothClient):
        client.projects.bulk_update(patch_data={"name": "x"})
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/workspaces/1/projects"
        )

    def test_bulk_delete(self, client: MammothClient):
        client.projects.bulk_delete(project_ids=[1, 2])
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/workspaces/1/projects"
        )


# ======================================================================
# DatasetsAPI
# ======================================================================


class TestDatasetsAPI:
    def test_list(self, client: MammothClient):
        client.datasets.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets")

    def test_get(self, client: MammothClient):
        client.datasets.get(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets/500")

    def test_create(self, client: MammothClient):
        client.datasets.create(dataset_spec={"name": "ds"}, ds_creation_type="file")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/datasets")

    def test_update(self, client: MammothClient):
        client.datasets.update(patch_data=[{"op": "rename_dataset", "path": "/500"}])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/datasets")

    def test_rename(self, client: MammothClient):
        client.datasets.rename(dataset_id=500, name="New Name")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/datasets")

    def test_delete(self, client: MammothClient):
        client.datasets.delete(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/datasets/500")

    def test_list_batches(self, client: MammothClient):
        client.datasets.list_batches(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets/500/batches")

    def test_get_batch(self, client: MammothClient):
        client.datasets.get_batch(dataset_id=500, batch_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/batches/10")

    def test_get_file_settings(self, client: MammothClient):
        client.datasets.get_file_settings(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/file_settings"
        )

    def test_bulk_update(self, client: MammothClient):
        client.datasets.bulk_update(patch_data={"name": "x"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/datasets")

    def test_bulk_delete(self, client: MammothClient):
        client.datasets.bulk_delete()
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/datasets")


# ======================================================================
# DataviewsAPI
# ======================================================================


class TestDataviewsAPI:
    def test_list(self, client: MammothClient):
        client.dataviews.list(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/dataviews"
        )

    def test_get(self, client: MammothClient):
        client.dataviews.get(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dataviews/42")

    def test_create(self, client: MammothClient):
        client.dataviews.create(dataset_id=500, name="New View")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/dataviews"
        )

    def test_update(self, client: MammothClient):
        client.dataviews.update(dataset_id=500, dataview_id=42, patch_data=[{"op": "replace"}])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/dataviews/42")

    def test_delete(self, client: MammothClient):
        client.dataviews.delete(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/dataviews/42")

    def test_bulk_delete(self, client: MammothClient):
        client.dataviews.bulk_delete(dataset_id=500, dataview_ids=[42, 43])
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/datasets/500/dataviews"
        )

    def test_query_data(self, client: MammothClient):
        client.dataviews.query_data(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dataviews/42/data")

    def test_active_users(self, client: MammothClient):
        client.dataviews.active_users(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/activities"
        )

    def test_mark_active(self, client: MammothClient):
        client.dataviews.mark_active(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/activities"
        )

    def test_conditional_format_list(self, client: MammothClient):
        client.dataviews.conditional_format_list(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/conditional-format"
        )

    def test_conditional_format_create(self, client: MammothClient):
        client.dataviews.conditional_format_create(
            dataset_id=500, dataview_id=42, rule={"color": "red"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/conditional-format"
        )

    def test_conditional_format_update(self, client: MammothClient):
        client.dataviews.conditional_format_update(
            dataset_id=500, dataview_id=42, rule={"color": "blue"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/dataviews/42/conditional-format"
        )

    def test_conditional_format_delete(self, client: MammothClient):
        client.dataviews.conditional_format_delete(dataset_id=500, dataview_id=42)
        assert_called_with_method_and_endpoint(
            client._request_json, "DELETE", "/dataviews/42/conditional-format"
        )

    def test_draft_mode(self, client: MammothClient):
        client.dataviews.draft_mode(dataset_id=500, dataview_id=42, command="enter")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dataviews/42/draft-mode"
        )


# ======================================================================
# PipelineAPI
# ======================================================================


class TestPipelineAPI:
    def test_get_pipeline(self, client: MammothClient):
        client.pipeline.get_pipeline(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dataviews/42/pipeline"
        )

    def test_list_tasks(self, client: MammothClient):
        client.pipeline.list_tasks(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/tasks")

    def test_add_task(self, client: MammothClient):
        client.pipeline.add_task(dataview_id=42, task_spec={"MATH": {}}, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/pipeline/tasks")

    def test_get_task(self, client: MammothClient):
        client.pipeline.get_task(dataview_id=42, task_id=7, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/tasks/7")

    def test_update_task(self, client: MammothClient):
        client.pipeline.update_task(
            dataview_id=42, task_id=7, task_spec={"MATH": {}}, dataset_id=500
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/pipeline/tasks/7")

    def test_delete_task(self, client: MammothClient):
        client.pipeline.delete_task(dataview_id=42, task_id=7, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/pipeline/tasks/7")

    def test_preview_task(self, client: MammothClient):
        client.pipeline.preview_task(dataview_id=42, task_spec={"MATH": {}}, dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/pipeline/task_preview"
        )

    def test_draft_mode(self, client: MammothClient):
        client.pipeline.draft_mode(dataview_id=42, command="enter", dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/draft-mode")

    def test_edit_pipeline(self, client: MammothClient):
        client.pipeline.edit_pipeline(dataview_id=42, patches=[{"op": "command"}], dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/dataviews/42/pipeline"
        )


# ======================================================================
# FilesAPI
# ======================================================================


class TestFilesAPI:
    def test_list(self, client: MammothClient):
        # files.list() parses response into FilesList Pydantic model
        client._request_json.return_value = {
            "files": [],
            "next": "",
        }
        client.files.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/files")

    def test_get(self, client: MammothClient):
        # files.get() parses response into FileDetails -> returns file field
        client._request_json.return_value = {
            "file": {"id": 10, "name": "test.csv"},
        }
        client.files.get(file_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/files/10")

    def test_delete(self, client: MammothClient):
        client.files.delete(file_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/files/10")

    def test_bulk_delete(self, client: MammothClient):
        client.files.bulk_delete(file_ids=[10, 11])
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/files")


# ======================================================================
# FoldersAPI
# ======================================================================


class TestFoldersAPI:
    def test_list(self, client: MammothClient):
        client.folders.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/folders")

    def test_create(self, client: MammothClient):
        client._request_json.return_value = {"id": 1, "name": "Test", "resource_id": "r1"}
        client.folders.create(name="Test Folder")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/folders")

    def test_delete(self, client: MammothClient):
        client.folders.delete(folder_ids=[1, 2])
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/folders")

    def test_move(self, client: MammothClient):
        client.folders.move(resource_ids=["r1"], target_folder_resource_id="r2")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/folders")


# ======================================================================
# JobsAPI
# ======================================================================


class TestJobsAPI:
    def test_get_job(self, client: MammothClient):
        client.jobs.get_job(job_id=999)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/jobs/999")

    def test_get_jobs(self, client: MammothClient):
        client.jobs.get_jobs(job_ids=[1, 2, 3])
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/jobs")


# ======================================================================
# ExportsAPI (low-level)
# ======================================================================


class TestExportsAPILowLevel:
    def test_list(self, client: MammothClient):
        # exports.list() needs _find_dataset_for_dataview and returns Pydantic model
        client.pipeline._find_dataset_for_dataview = MagicMock(return_value=500)
        client._request_json.return_value = {
            "exports": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
            "next": "",
        }
        client.exports.list(dataview_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/pipeline/exports")


# ======================================================================
# ConnectorsAPI
# ======================================================================


class TestConnectorsAPI:
    def test_list(self, client: MammothClient):
        client.connectors.list()
        assert_called_with_method_and_endpoint(client._request, "GET", "/connectors")

    def test_get(self, client: MammothClient):
        client.connectors.get(connector_key="salesforce")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/connectors/salesforce"
        )

    def test_list_connections(self, client: MammothClient):
        client.connectors.list_connections(connector_key="salesforce")
        assert_called_with_method_and_endpoint(
            client._request, "GET", "/connectors/salesforce/connections"
        )

    def test_create_connection(self, client: MammothClient):
        client.connectors.create_connection(
            connector_key="salesforce", config={"code": "oauth_code"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connectors/salesforce/connections"
        )
        assert_json_body(client._request_json, {"code": "oauth_code"})

    def test_create_connection_forwards_config_unchanged(self, client: MammothClient):
        creds = {
            "hostname": "db.example.com",
            "port": 5432,
            "database": "prod",
            "username": "u",
            "password": "p",
        }
        client.connectors.create_connection(connector_key="postgres", config=creds)
        assert_json_body(client._request_json, creds)

    def test_create_connection_rejects_empty_config(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="config"):
            client.connectors.create_connection(connector_key="postgres", config={})
        client._request_json.assert_not_called()

    def test_get_connection(self, client: MammothClient):
        client.connectors.get_connection(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/connections/conn1")

    def test_update_connection_wraps_patch_envelope(self, client: MammothClient):
        """PROD BUG FIX: SDK must wrap credentials in the patch envelope."""
        creds = {"host": "new.db.example.com", "password": "newpass"}
        client.connectors.update_connection(
            connector_key="postgres", connection_key="conn1", credentials=creds
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/connections/conn1")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "connection", "value": creds}]},
        )

    def test_update_connection_rejects_empty_credentials(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="credentials"):
            client.connectors.update_connection(
                connector_key="postgres", connection_key="conn1", credentials={}
            )
        client._request_json.assert_not_called()

    def test_delete_connection(self, client: MammothClient):
        client.connectors.delete_connection(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/connections/conn1")

    def test_list_ds_configs(self, client: MammothClient):
        client.connectors.list_ds_configs(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(
            client._request, "GET", "/connections/conn1/ds_configs"
        )

    def test_create_ds_config_with_query(self, client: MammothClient):
        client.connectors.create_ds_config(
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

    def test_create_ds_config_with_file_source(self, client: MammothClient):
        client.connectors.create_ds_config(
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

    def test_create_ds_config_rejects_no_source(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="query"):
            client.connectors.create_ds_config(connector_key="postgres", connection_key="conn1")
        client._request_json.assert_not_called()

    def test_create_ds_config_rejects_validate_xor(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="mutually exclusive"):
            client.connectors.create_ds_config(
                connector_key="postgres",
                connection_key="conn1",
                query="SELECT 1",
                validate=True,
                data_sample=True,
            )
        client._request_json.assert_not_called()

    def test_get_ds_config(self, client: MammothClient):
        client.connectors.get_ds_config(
            connector_key="salesforce", connection_key="conn1", ds_config_key="dsc1"
        )
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/ds_configs/dsc1")

    def test_update_ds_config_sends_patch_envelope(self, client: MammothClient):
        op = DsConfigPatchOp(
            op="replace",
            path=DsConfigPatchPath.QUERY,
            value={"query": "SELECT id FROM users", "ds_id": 10, "validate": True},
        )
        client.connectors.update_ds_config(
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

    def test_update_ds_config_rejects_empty_patch(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patch"):
            client.connectors.update_ds_config(
                connector_key="postgres",
                connection_key="conn1",
                ds_config_key="dsc1",
                patch=[],
            )
        client._request_json.assert_not_called()

    def test_delete_ds_config(self, client: MammothClient):
        client.connectors.delete_ds_config(
            connector_key="salesforce", connection_key="conn1", ds_config_key="dsc1"
        )
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/ds_configs/dsc1")

    def test_active_connectors(self, client: MammothClient):
        client.connectors.active_connectors()
        assert_called_with_method_and_endpoint(client._request, "GET", "/active_connectors")


# ======================================================================
# DashboardsAPI
# ======================================================================


class TestDashboardsAPI:
    # ── list / get / delete / get_sources / get_analytics / get_by_url ───────

    def test_list(self, client: MammothClient):
        client.dashboards.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards")

    def test_get(self, client: MammothClient):
        client.dashboards.get(dashboard_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards/5")

    def test_delete(self, client: MammothClient):
        client.dashboards.delete(dashboard_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/dashboards/5")

    def test_get_sources(self, client: MammothClient):
        client.dashboards.get_sources()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards/sources")

    def test_get_analytics(self, client: MammothClient):
        client.dashboards.get_analytics(dashboard_id=5)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dashboards/5/analytics"
        )

    def test_get_by_url(self, client: MammothClient):
        client.dashboards.get_by_url(url="my-dashboard")
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/dashboards/url/my-dashboard"
        )

    def test_get_draft_data(self, client: MammothClient):
        client.dashboards.get_draft_data(dashboard_id=5, sql="SELECT 1")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/5/getDraftData"
        )

    def test_get_publish_data(self, client: MammothClient):
        client.dashboards.get_publish_data(dashboard_id=5, sql="SELECT 1")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/dashboards/5/getPublishData"
        )

    # ── create ───────────────────────────────────────────────────────────────

    def test_create_sends_correct_body(self, client: MammothClient):
        client.dashboards.create(
            intent="Show quarterly revenue by region",
            source=[101, 102],
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards")
        assert_json_body(
            client._request_json,
            {
                "params": {
                    "intent": "Show quarterly revenue by region",
                    "source": [101, 102],
                    "enable_filters": True,
                    "enable_pages": False,
                }
            },
        )

    def test_create_explicit_flags(self, client: MammothClient):
        client.dashboards.create(
            intent="Sales performance breakdown for EMEA",
            source=[7],
            enable_filters=False,
            enable_pages=True,
        )
        assert_json_body(
            client._request_json,
            {
                "params": {
                    "intent": "Sales performance breakdown for EMEA",
                    "source": [7],
                    "enable_filters": False,
                    "enable_pages": True,
                }
            },
        )

    def test_create_rejects_short_intent(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="intent"):
            client.dashboards.create(intent="too short", source=[1])
        client._request_json.assert_not_called()

    def test_create_rejects_empty_source(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="source"):
            client.dashboards.create(intent="Show quarterly revenue by region", source=[])
        client._request_json.assert_not_called()

    def test_create_rejects_nonpositive_source_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="source"):
            client.dashboards.create(intent="Show quarterly revenue by region", source=[1, 0])
        client._request_json.assert_not_called()

    # ── update ───────────────────────────────────────────────────────────────

    def test_update_rename(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.TITLE, value="New Name"
        )
        client.dashboards.update(dashboard_id=5, patch=[op])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/dashboards/5")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "title", "value": "New Name"}]},
        )

    def test_update_theme(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.THEME, value="DARK_MODE"
        )
        client.dashboards.update(dashboard_id=5, patch=[op])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "theme", "value": "DARK_MODE"}]},
        )

    def test_update_intent(self, client: MammothClient):
        intent_value = "Show quarterly revenue by product line"
        op = DashboardPatchItem(
            op=DashboardPatchOp.ADD, path=DashboardPatchPath.INTENT, value=intent_value
        )
        client.dashboards.update(dashboard_id=5, patch=[op])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "add", "path": "intent", "value": intent_value}]},
        )

    def test_update_rejects_nonpositive_id(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.REPLACE, path=DashboardPatchPath.TITLE, value="x"
        )
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            client.dashboards.update(dashboard_id=0, patch=[op])
        client._request_json.assert_not_called()

    def test_update_rejects_empty_patch(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patch"):
            client.dashboards.update(dashboard_id=5, patch=[])
        client._request_json.assert_not_called()

    def test_update_rejects_short_intent_value(self, client: MammothClient):
        op = DashboardPatchItem(
            op=DashboardPatchOp.ADD, path=DashboardPatchPath.INTENT, value="too short"
        )
        with pytest.raises(MammothValidationError, match="intent"):
            client.dashboards.update(dashboard_id=5, patch=[op])
        client._request_json.assert_not_called()

    # ── share ────────────────────────────────────────────────────────────────

    def test_share_public(self, client: MammothClient):
        client.dashboards.share(dashboard_id=5, type_of_auth=DashboardAuthType.PUBLIC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/5/share")
        assert_json_body(
            client._request_json,
            {"params": {"auth": {"type_of_auth": "public"}}},
        )

    def test_share_mammoth_with_users(self, client: MammothClient):
        user = DashboardShareUser(
            email="alice@example.com", role=DashboardShareRole.EDITOR, shared=True
        )
        client.dashboards.share(
            dashboard_id=5,
            type_of_auth=DashboardAuthType.MAMMOTH,
            users=[user],
        )
        assert_json_body(
            client._request_json,
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

    def test_share_password_type(self, client: MammothClient):
        client.dashboards.share(dashboard_id=5, type_of_auth=DashboardAuthType.PASSWORD)
        assert_json_body(
            client._request_json,
            {"params": {"auth": {"type_of_auth": "password"}}},
        )

    def test_share_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            client.dashboards.share(dashboard_id=0, type_of_auth=DashboardAuthType.PUBLIC)
        client._request_json.assert_not_called()

    def test_share_rejects_empty_user_email(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="email"):
            client.dashboards.share(
                dashboard_id=5,
                type_of_auth=DashboardAuthType.MAMMOTH,
                users=[DashboardShareUser(email="", role=DashboardShareRole.VIEWER, shared=True)],
            )
        client._request_json.assert_not_called()

    # ── action ───────────────────────────────────────────────────────────────

    def test_action_sync_no_params(self, client: MammothClient):
        client.dashboards.action(dashboard_id=5, action=DashboardActionType.SYNC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/5/action")
        assert_json_body(client._request_json, {"action": "sync"})

    def test_action_sync_scoped(self, client: MammothClient):
        client.dashboards.action(dashboard_id=5, action=DashboardActionType.SYNC, params_view_id=42)
        assert_json_body(client._request_json, {"action": "sync", "params": {"view_id": 42}})

    def test_action_publish_data(self, client: MammothClient):
        client.dashboards.action(dashboard_id=5, action=DashboardActionType.PUBLISH_DATA)
        assert_json_body(client._request_json, {"action": "publish-data"})

    def test_action_auto_sync(self, client: MammothClient):
        client.dashboards.action(
            dashboard_id=5,
            action=DashboardActionType.AUTO_SYNC,
            params_enabled=True,
            params_view_id=42,
        )
        assert_json_body(
            client._request_json,
            {"action": "auto-sync", "params": {"enabled": True, "view_id": 42}},
        )

    def test_action_auto_publish(self, client: MammothClient):
        client.dashboards.action(
            dashboard_id=5, action=DashboardActionType.AUTO_PUBLISH, params_enabled=False
        )
        assert_json_body(
            client._request_json,
            {"action": "auto-publish", "params": {"enabled": False}},
        )

    def test_action_delete_source(self, client: MammothClient):
        client.dashboards.action(
            dashboard_id=5, action=DashboardActionType.DELETE_SOURCE, params_view_id=7
        )
        assert_json_body(
            client._request_json,
            {"action": "delete-source", "params": {"view_id": 7}},
        )

    def test_action_rejects_nonpositive_dashboard_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="dashboard_id"):
            client.dashboards.action(dashboard_id=0, action=DashboardActionType.SYNC)
        client._request_json.assert_not_called()

    def test_action_auto_sync_requires_enabled(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="auto-sync"):
            client.dashboards.action(dashboard_id=5, action=DashboardActionType.AUTO_SYNC)
        client._request_json.assert_not_called()

    def test_action_auto_publish_requires_enabled(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="auto-publish"):
            client.dashboards.action(dashboard_id=5, action=DashboardActionType.AUTO_PUBLISH)
        client._request_json.assert_not_called()

    def test_action_delete_source_requires_view_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="delete-source"):
            client.dashboards.action(dashboard_id=5, action=DashboardActionType.DELETE_SOURCE)
        client._request_json.assert_not_called()

    def test_action_rejects_nonpositive_view_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="params_view_id"):
            client.dashboards.action(
                dashboard_id=5, action=DashboardActionType.DELETE_SOURCE, params_view_id=0
            )
        client._request_json.assert_not_called()


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
    def test_list(self, client: MammothClient) -> None:
        client.automations.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/automations")

    def test_create(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=42)]),
        )
        client.automations.create(
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

    def test_create_empty_name_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=1)]),
        )
        with pytest.raises(MammothValidationError):
            client.automations.create(name="", description="d", tasks=[task])
        client._request_json.assert_not_called()

    def test_create_empty_tasks_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.automations.create(name="A", description="d", tasks=[])
        client._request_json.assert_not_called()

    def test_create_task_missing_ds_details_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(),
        )
        with pytest.raises(MammothValidationError):
            client.automations.create(name="A", description="d", tasks=[task])
        client._request_json.assert_not_called()

    def test_create_task_missing_alert_fields_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.SEND_AN_ALERT,
            details=TaskDetailsSpec(alert_type=AlertType.EMAIL),
        )
        with pytest.raises(MammothValidationError):
            client.automations.create(name="A", description="d", tasks=[task])
        client._request_json.assert_not_called()

    def test_create_condition_at_specific_time_missing_interval_raises(
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
            client.automations.create(name="A", description="d", tasks=[task], conditions=[cond])
        client._request_json.assert_not_called()

    def test_create_condition_by_month_day_out_of_range_raises(self, client: MammothClient) -> None:
        task = AutomationTaskSpec(
            task_type=AutomationTaskType.RUN_DATA_RETRIEVAL,
            details=TaskDetailsSpec(ds_details=[DataRefreshConfig(ds_id=1)]),
        )
        cond = AutomationConditionSpec(
            condition_type=AutomationConditionType.RUN_CONFIG,
            details=ConditionDetailsSpec(by_month_day=[32]),
        )
        with pytest.raises(MammothValidationError):
            client.automations.create(name="A", description="d", tasks=[task], conditions=[cond])
        client._request_json.assert_not_called()

    def test_get(self, client: MammothClient) -> None:
        client.automations.get(automation_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/automations/10")

    def test_update_command_run(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.RUN, value={}
        )
        client.automations.update(automation_id=10, patch=[patch_item])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/automations/10")
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "command", "path": "run", "value": {}}]},
        )

    def test_update_status_suspend(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE,
            path=AutomationPatchPath.STATUS,
            value=AutomationStatus.SUSPEND.value,
        )
        client.automations.update(automation_id=10, patch=[patch_item])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "status", "value": "suspend"}]},
        )

    def test_update_details(self, client: MammothClient) -> None:
        details = PatchAutomationDetails(name="Renamed")
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE, path=AutomationPatchPath.DETAILS, value=details
        )
        client.automations.update(automation_id=10, patch=[patch_item])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "details", "value": {"name": "Renamed"}}]},
        )

    def test_update_invalid_id_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.RUN, value={}
        )
        with pytest.raises(MammothValidationError):
            client.automations.update(automation_id=0, patch=[patch_item])
        client._request_json.assert_not_called()

    def test_update_empty_patch_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.automations.update(automation_id=10, patch=[])
        client._request_json.assert_not_called()

    def test_update_command_wrong_path_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.COMMAND, path=AutomationPatchPath.STATUS, value={}
        )
        with pytest.raises(MammothValidationError):
            client.automations.update(automation_id=10, patch=[patch_item])
        client._request_json.assert_not_called()

    def test_update_status_invalid_value_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE,
            path=AutomationPatchPath.STATUS,
            value="active",
        )
        with pytest.raises(MammothValidationError):
            client.automations.update(automation_id=10, patch=[patch_item])
        client._request_json.assert_not_called()

    def test_update_details_all_none_raises(self, client: MammothClient) -> None:
        patch_item = AutomationPatchItem(
            op=AutomationPatchOp.REPLACE,
            path=AutomationPatchPath.DETAILS,
            value=PatchAutomationDetails(),
        )
        with pytest.raises(MammothValidationError):
            client.automations.update(automation_id=10, patch=[patch_item])
        client._request_json.assert_not_called()

    def test_delete(self, client: MammothClient) -> None:
        client.automations.delete(automation_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/automations/10")

    def test_list_schedules(self, client: MammothClient) -> None:
        client.automations.list_schedules()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules")

    def test_create_schedule(self, client: MammothClient) -> None:
        client.automations.create_schedule(spec=_SCHEDULE_CREATE_SPEC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")
        assert_json_body(client._request_json, _SCHEDULE_CREATE_BODY)

    def test_create_schedule_invalid_interval_raises(self, client: MammothClient) -> None:
        spec = ScheduleCreateSpec(
            rrule=RruleSpec(frequency=RruleFrequency.DAILY, start=_DT, interval=-1)
        )
        with pytest.raises(MammothValidationError):
            client.automations.create_schedule(spec=spec)
        client._request_json.assert_not_called()

    def test_update_schedule(self, client: MammothClient) -> None:
        client.automations.update_schedule(schedule_id=5, patch=[_SCHEDULE_PATCH_RRULE_ITEM])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/schedules/5")
        assert_json_body(client._request_json, _SCHEDULE_PATCH_RRULE_BODY)

    def test_update_schedule_status(self, client: MammothClient) -> None:
        client.automations.update_schedule(schedule_id=5, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "status", "value": "pause"}]},
        )

    def test_update_schedule_invalid_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.automations.update_schedule(schedule_id=0, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        client._request_json.assert_not_called()

    def test_update_schedule_empty_patch_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.automations.update_schedule(schedule_id=5, patch=[])
        client._request_json.assert_not_called()

    def test_update_schedule_invalid_op_raises(self, client: MammothClient) -> None:
        bad_item = SchedulePatchItem(op="add", path=SchedulePatchPath.STATUS, value="pause")
        with pytest.raises(MammothValidationError):
            client.automations.update_schedule(schedule_id=5, patch=[bad_item])
        client._request_json.assert_not_called()

    def test_update_schedule_status_invalid_value_raises(self, client: MammothClient) -> None:
        bad_item = SchedulePatchItem(op="replace", path=SchedulePatchPath.STATUS, value="stop")
        with pytest.raises(MammothValidationError):
            client.automations.update_schedule(schedule_id=5, patch=[bad_item])
        client._request_json.assert_not_called()

    def test_delete_schedule(self, client: MammothClient) -> None:
        client.automations.delete_schedule(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/schedules/5")


# ======================================================================
# SchedulesAPI
# ======================================================================


class TestSchedulesAPI:
    def test_list(self, client: MammothClient) -> None:
        client.schedules.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules")

    def test_get(self, client: MammothClient) -> None:
        client.schedules.get(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules/5")

    def test_create(self, client: MammothClient) -> None:
        """SchedulesAPI.create produces the same wire body as AutomationsAPI.create_schedule."""
        client.schedules.create(spec=_SCHEDULE_CREATE_SPEC)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")
        assert_json_body(client._request_json, _SCHEDULE_CREATE_BODY)

    def test_create_with_project_id(self, client: MammothClient) -> None:
        client.schedules.create(spec=_SCHEDULE_CREATE_SPEC, project_id=99)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")
        assert_json_body(client._request_json, _SCHEDULE_CREATE_BODY)

    def test_create_invalid_project_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.schedules.create(spec=_SCHEDULE_CREATE_SPEC, project_id=0)
        client._request_json.assert_not_called()

    def test_create_invalid_interval_raises(self, client: MammothClient) -> None:
        spec = ScheduleCreateSpec(
            rrule=RruleSpec(frequency=RruleFrequency.HOURLY, start=_DT, interval=0)
        )
        with pytest.raises(MammothValidationError):
            client.schedules.create(spec=spec)
        client._request_json.assert_not_called()

    def test_update(self, client: MammothClient) -> None:
        """SchedulesAPI.update produces the same wire body as AutomationsAPI.update_schedule."""
        client.schedules.update(schedule_id=5, patch=[_SCHEDULE_PATCH_RRULE_ITEM])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/schedules/5")
        assert_json_body(client._request_json, _SCHEDULE_PATCH_RRULE_BODY)

    def test_update_status(self, client: MammothClient) -> None:
        client.schedules.update(schedule_id=5, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "path": "status", "value": "pause"}]},
        )

    def test_update_invalid_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.schedules.update(schedule_id=-1, patch=[_SCHEDULE_PATCH_STATUS_ITEM])
        client._request_json.assert_not_called()

    def test_update_invalid_project_id_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.schedules.update(
                schedule_id=5, patch=[_SCHEDULE_PATCH_STATUS_ITEM], project_id=0
            )
        client._request_json.assert_not_called()

    def test_update_empty_patch_raises(self, client: MammothClient) -> None:
        with pytest.raises(MammothValidationError):
            client.schedules.update(schedule_id=5, patch=[])
        client._request_json.assert_not_called()

    def test_update_invalid_op_raises(self, client: MammothClient) -> None:
        bad_item = SchedulePatchItem(op="remove", path=SchedulePatchPath.RRULE, value="pause")
        with pytest.raises(MammothValidationError):
            client.schedules.update(schedule_id=5, patch=[bad_item])
        client._request_json.assert_not_called()

    def test_delete(self, client: MammothClient) -> None:
        client.schedules.delete(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/schedules/5")


# ======================================================================
# BatchesAPI
# ======================================================================


class TestBatchesAPI:
    def test_list(self, client: MammothClient):
        client.batches.list(dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets/500/batches")

    def test_get(self, client: MammothClient):
        client.batches.get(dataset_id=500, batch_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/batches/10")

    def test_create_sends_correct_body(self, client: MammothClient):
        client.batches.create(
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
                "source": "datasource",
                "source_id": 42,
                "mapping": {"src_col": "dst_col"},
                "delete_source_ds": False,
            },
        )

    def test_create_with_optional_fields(self, client: MammothClient):
        client.batches.create(
            dataset_id=500,
            source_id=42,
            mapping={"a": "b"},
            is_validation_required=True,
            delete_source_ds=True,
        )
        assert_json_body(
            client._request_json,
            {
                "source": "datasource",
                "source_id": 42,
                "mapping": {"a": "b"},
                "is_validation_required": True,
                "delete_source_ds": True,
            },
        )

    def test_create_rejects_nonpositive_source_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="source_id"):
            client.batches.create(dataset_id=500, source_id=0, mapping={"a": "b"})
        client._request_json.assert_not_called()

    def test_create_rejects_empty_mapping(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="mapping"):
            client.batches.create(dataset_id=500, source_id=1, mapping={})
        client._request_json.assert_not_called()

    def test_update_wraps_patch_envelope(self, client: MammothClient):
        """PROD BUG FIX: SDK must wrap patch ops in {"patch": [...]} envelope."""
        patch_ops = [{"op": "replace", "value": {"approve": [101, 102]}}]
        client.batches.update(dataset_id=500, patch=patch_ops)
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/datasets/500/batches"
        )
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "replace", "value": {"approve": [101, 102]}}]},
        )

    def test_update_remove_op(self, client: MammothClient):
        patch_ops = [{"op": "remove", "value": [101, 102]}]
        client.batches.update(dataset_id=500, patch=patch_ops)
        assert_json_body(
            client._request_json,
            {"patch": [{"op": "remove", "value": [101, 102]}]},
        )

    def test_update_rejects_empty_patch(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patch"):
            client.batches.update(dataset_id=500, patch=[])
        client._request_json.assert_not_called()

    def test_update_rejects_invalid_op(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="op"):
            client.batches.update(dataset_id=500, patch=[{"op": "add", "value": [1]}])
        client._request_json.assert_not_called()

    def test_delete(self, client: MammothClient):
        client.batches.delete(dataset_id=500, batch_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/batches/10")


# ======================================================================
# BrowseAPI
# ======================================================================


class TestBrowseAPI:
    def test_workspaces(self, client: MammothClient):
        client.browse.workspaces()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces")

    def test_projects(self, client: MammothClient):
        client.browse.projects()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/projects")

    def test_datasets(self, client: MammothClient):
        client.browse.datasets()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/datasets")

    def test_dataviews(self, client: MammothClient):
        client.browse.dataviews(dataset_id=500)
        assert_called_with_method_and_endpoint(
            client._request_json, "GET", "/datasets/500/dataviews"
        )


# ======================================================================
# ClientAppsAPI
# ======================================================================


class TestClientAppsAPI:
    def test_list(self, client: MammothClient):
        # client_apps.list() returns Pydantic model
        client._request_json.return_value = {
            "result": [],
        }
        client.client_apps.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/clientapps")

    def test_create(self, client: MammothClient):
        # client_apps.create() returns Pydantic model with ValueWrapper fields
        client._request_json.return_value = {
            "client_app": {
                "client_key": {"value": "ck1"},
                "app_name": {"value": "MyApp"},
            },
        }
        client.client_apps.create(app_name="MyApp")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/clientapps")

    def test_get(self, client: MammothClient):
        # client_apps.get() returns ClientAppSchema with ValueWrapper fields
        client._request_json.return_value = {
            "client_key": {"value": "ck1"},
            "app_name": {"value": "MyApp"},
        }
        client.client_apps.get(client_key="ck1")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/clientapps/ck1")

    def test_delete(self, client: MammothClient):
        client.client_apps.delete(client_key="ck1")
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/clientapps/ck1")


# ======================================================================
# ExternalKeysAPI
# ======================================================================


class TestExternalKeysAPI:
    def test_list(self, client: MammothClient):
        client.external_keys.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/external_keys")

    def test_get(self, client: MammothClient):
        client.external_keys.get(key_id=3)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/external_keys/3")

    def test_create_minimal(self, client: MammothClient):
        client.external_keys.create(
            key_type=ExternalKeyType.ANTHROPIC,
            key_name="Claude key",
            secure_key="sk-ant-123",
        )
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/external_keys")
        assert_json_body(
            client._request_json,
            {"key_type": "anthropic", "key_name": "Claude key", "secure_key": "sk-ant-123"},
        )

    def test_create_with_model_settings(self, client: MammothClient):
        client.external_keys.create(
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

    def test_create_rejects_empty_name(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="key_name"):
            client.external_keys.create(
                key_type=ExternalKeyType.GEMINI, key_name="", secure_key="abc"
            )
        client._request_json.assert_not_called()

    def test_create_rejects_short_secure_key(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="secure_key"):
            client.external_keys.create(
                key_type=ExternalKeyType.GROK, key_name="k", secure_key="ab"
            )
        client._request_json.assert_not_called()

    def test_create_model_settings_requires_model_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="model_id"):
            client.external_keys.create(
                key_type=ExternalKeyType.OPEN_AI,
                key_name="k",
                secure_key="abc",
                model_settings=ModelConfigSpec(web_search=True),
            )
        client._request_json.assert_not_called()

    def test_delete(self, client: MammothClient):
        client.external_keys.delete(key_id=3)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/external_keys/3")


# ======================================================================
# ActivityLogsAPI
# ======================================================================


class TestActivityLogsAPI:
    def test_list(self, client: MammothClient):
        client.activity_logs.list()
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/activity_log")

    def test_export(self, client: MammothClient):
        client.activity_logs.export()
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/activity_log/export")


# ======================================================================
# AddonsAPI
# ======================================================================


class TestAddonsAPI:
    def test_add_connector_single(self, client: MammothClient):
        client.addons.add_connector(connector_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/connectors")
        assert_json_body(client._request_json, {"connector_id": 42})

    def test_add_connector_bulk(self, client: MammothClient):
        client.addons.add_connector(connector_ids=[42, 43])
        assert_json_body(client._request_json, {"connector_ids": [42, 43]})

    def test_remove_connector_single(self, client: MammothClient):
        client.addons.remove_connector(connector_id=42)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/connectors")
        assert_json_body(client._request_json, {"connector_id": 42})

    def test_connector_requires_exactly_one(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="exactly one"):
            client.addons.add_connector()
        with pytest.raises(MammothValidationError, match="exactly one"):
            client.addons.add_connector(connector_id=1, connector_ids=[2])
        client._request_json.assert_not_called()

    def test_connector_rejects_nonpositive_id(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="positive"):
            client.addons.add_connector(connector_id=0)
        with pytest.raises(MammothValidationError, match="positive"):
            client.addons.add_connector(connector_ids=[1, -2])
        client._request_json.assert_not_called()

    def test_connector_rejects_empty_list(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="non-empty"):
            client.addons.add_connector(connector_ids=[])
        client._request_json.assert_not_called()

    def test_add_storage(self, client: MammothClient):
        client.addons.add_storage(additional_storage_gb=50)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/storage")
        assert_json_body(client._request_json, {"additional_storage_gb": 50})

    def test_remove_storage(self, client: MammothClient):
        client.addons.remove_storage(removal_storage_gb=20)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/storage")
        assert_json_body(client._request_json, {"removal_storage_gb": 20})

    def test_storage_rejects_nonpositive(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="positive"):
            client.addons.add_storage(additional_storage_gb=0)
        with pytest.raises(MammothValidationError, match="positive"):
            client.addons.remove_storage(removal_storage_gb=-5)
        client._request_json.assert_not_called()

    def test_add_users(self, client: MammothClient):
        client.addons.add_users(user_count=5)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/users")
        assert_json_body(client._request_json, {"user_count": 5})

    def test_add_users_defaults_to_one(self, client: MammothClient):
        client.addons.add_users()
        assert_json_body(client._request_json, {"user_count": 1})

    def test_remove_users(self, client: MammothClient):
        client.addons.remove_users(user_count=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/users")
        assert_json_body(client._request_json, {"user_count": 5})

    def test_users_rejects_nonpositive(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="positive"):
            client.addons.add_users(user_count=0)
        with pytest.raises(MammothValidationError, match="positive"):
            client.addons.remove_users(user_count=-1)
        client._request_json.assert_not_called()


# ======================================================================
# ReportsAPI
# ======================================================================


class TestReportsAPI:
    def test_list(self, client: MammothClient):
        client.reports.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/reports")


# ======================================================================
# UserProfileAPI
# ======================================================================


class TestUserProfileAPI:
    def test_get(self, client: MammothClient):
        client.user_profile.get()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/self")

    def test_update(self, client: MammothClient):
        client.user_profile.update(first_name="Alice")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/self")

    def test_change_password(self, client: MammothClient):
        client.user_profile.change_password(current_password="old", new_password="new")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/change_password")

    def test_get_preferences(self, client: MammothClient):
        client.user_profile.get_preferences()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/preferences")

    def test_update_preferences(self, client: MammothClient):
        client.user_profile.update_preferences(theme="dark")
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/preferences")


# ======================================================================
# WorkspaceAPI
# ======================================================================


class TestWorkspaceAPI:
    def test_list(self, client: MammothClient):
        client.workspaces.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces")

    def test_get(self, client: MammothClient):
        client.workspaces.get()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces/1")

    def test_update_name(self, client: MammothClient):
        op = WorkspacePatchOp(op="replace", path=WorkspacePatchPath.NAME, value="Acme Corp")
        client.workspaces.update(patches=[op])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/workspaces/1")
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "name", "value": "Acme Corp"}]},
        )

    def test_update_billing_cycle(self, client: MammothClient):
        op = WorkspacePatchOp(
            op="replace", path=WorkspacePatchPath.BILLING_CYCLE, value=BillingCycle.YEARLY
        )
        client.workspaces.update(patches=[op])
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "billing_cycle", "value": "yearly"}]},
        )

    def test_update_plan_id(self, client: MammothClient):
        op = WorkspacePatchOp(op="replace", path=WorkspacePatchPath.PLAN_ID, value=3)
        client.workspaces.update(patches=[op])
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "plan_id", "value": 3}]},
        )

    def test_update_rejects_empty_patches(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patches"):
            client.workspaces.update(patches=[])
        client._request_json.assert_not_called()

    def test_update_rejects_name_too_long(self, client: MammothClient):
        with pytest.raises(ValueError, match="name"):
            WorkspacePatchOp(op="replace", path=WorkspacePatchPath.NAME, value="x" * 51)

    def test_update_rejects_invalid_billing_cycle(self, client: MammothClient):
        with pytest.raises(ValueError, match="billing_cycle"):
            WorkspacePatchOp(op="replace", path=WorkspacePatchPath.BILLING_CYCLE, value="quarterly")

    def test_delete(self, client: MammothClient):
        client.workspaces.delete()
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/workspaces/1")

    def test_reactivate(self, client: MammothClient):
        client.workspaces.reactivate()
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/workspaces/1/reactivate"
        )

    def test_list_users(self, client: MammothClient):
        client.workspaces.list_users()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/workspaces/1/users")

    def test_get_user(self, client: MammothClient):
        client.workspaces.get_user(user_id="u1")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/users/u1")

    def test_update_user_sends_patch_envelope(self, client: MammothClient):
        op = UserRolePatchOp(op="replace", path="role", value=WorkspaceRoleType.WORKSPACE_ADMIN)
        client.workspaces.update_user(user_id="u1", patches=[op])
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/users/u1")
        assert_json_body(
            client._request_json,
            {"patches": [{"op": "replace", "path": "role", "value": "workspace_admin"}]},
        )

    def test_update_user_rejects_empty_user_id(self, client: MammothClient):
        op = UserRolePatchOp(op="replace", path="role", value=WorkspaceRoleType.WORKSPACE_MEMBER)
        with pytest.raises(MammothValidationError, match="user_id"):
            client.workspaces.update_user(user_id="", patches=[op])
        client._request_json.assert_not_called()

    def test_update_user_rejects_empty_patches(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="patches"):
            client.workspaces.update_user(user_id="u1", patches=[])
        client._request_json.assert_not_called()

    def test_update_user_rejects_invalid_role(self, client: MammothClient):
        with pytest.raises(ValueError):
            UserRolePatchOp(op="replace", path="role", value="admin")


# ======================================================================
# AIAPI
# ======================================================================


class TestAIAPI:
    def test_generate_profile(self, client: MammothClient):
        client.ai.generate_profile(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/profile_generation")

    def test_generate_data_sends_correct_body(self, client: MammothClient):
        client.ai.generate_data(
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

    def test_generate_data_with_columns(self, client: MammothClient):
        client.ai.generate_data(
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

    def test_generate_data_rejects_empty_prompt(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="prompt"):
            client.ai.generate_data(dataview_id=42, prompt="", dataset_id=500)
        client._request_json.assert_not_called()

    def test_generate_data_rejects_rows_too_low(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="no_of_rows"):
            client.ai.generate_data(
                dataview_id=42, prompt="Generate data", no_of_rows=0, dataset_id=500
            )
        client._request_json.assert_not_called()

    def test_generate_data_rejects_rows_too_high(self, client: MammothClient):
        with pytest.raises(MammothValidationError, match="no_of_rows"):
            client.ai.generate_data(
                dataview_id=42, prompt="Generate data", no_of_rows=101, dataset_id=500
            )
        client._request_json.assert_not_called()

    def test_get_data_gen_info(self, client: MammothClient):
        client.ai.get_data_gen_info(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/data/generate")

    def test_generate_sql(self, client: MammothClient):
        client.ai.generate_sql(intent="count employees")
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/sql_generation")

    def test_get_suggestions(self, client: MammothClient):
        client.ai.get_suggestions()
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/suggestions")

    def test_query_gen(self, client: MammothClient):
        client.ai.query_gen(connector_key="sf", connection_key="conn1", prompt="list tables")
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connections/conn1/chat"
        )
