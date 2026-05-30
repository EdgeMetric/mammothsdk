"""Unit tests for ALL API sub-clients — verifies each method calls the correct
HTTP method, endpoint, and parameters.

Tests every public method on every API sub-client:
  ProjectsAPI, DatasetsAPI, DataviewsAPI, PipelineAPI, FilesAPI, FoldersAPI,
  JobsAPI, ExportsAPI, ConnectorsAPI, DashboardsAPI, AutomationsAPI,
  SchedulesAPI, BatchesAPI, BrowseAPI, ClientAppsAPI, ExternalKeysAPI,
  ActivityLogsAPI, AddonsAPI, ReportsAPI, UserProfileAPI, WorkspaceAPI, AIAPI
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mammoth.client import MammothClient

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
        client.connectors.create_connection(connector_key="salesforce", config={"host": "x"})
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connectors/salesforce/connections"
        )

    def test_get_connection(self, client: MammothClient):
        client.connectors.get_connection(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/connections/conn1")

    def test_update_connection(self, client: MammothClient):
        client.connectors.update_connection(
            connector_key="salesforce", connection_key="conn1", config={"host": "y"}
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/connections/conn1")

    def test_delete_connection(self, client: MammothClient):
        client.connectors.delete_connection(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/connections/conn1")

    def test_list_ds_configs(self, client: MammothClient):
        client.connectors.list_ds_configs(connector_key="salesforce", connection_key="conn1")
        assert_called_with_method_and_endpoint(
            client._request, "GET", "/connections/conn1/ds_configs"
        )

    def test_create_ds_config(self, client: MammothClient):
        client.connectors.create_ds_config(
            connector_key="salesforce", connection_key="conn1", config={"table": "x"}
        )
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/connections/conn1/ds_configs"
        )

    def test_get_ds_config(self, client: MammothClient):
        client.connectors.get_ds_config(
            connector_key="salesforce", connection_key="conn1", ds_config_key="dsc1"
        )
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/ds_configs/dsc1")

    def test_update_ds_config(self, client: MammothClient):
        client.connectors.update_ds_config(
            connector_key="salesforce",
            connection_key="conn1",
            ds_config_key="dsc1",
            config={"table": "y"},
        )
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/ds_configs/dsc1")

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
    def test_list(self, client: MammothClient):
        client.dashboards.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards")

    def test_create(self, client: MammothClient):
        client.dashboards.create(config={"name": "Dashboard 1"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards")

    def test_get(self, client: MammothClient):
        client.dashboards.get(dashboard_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/dashboards/5")

    def test_update(self, client: MammothClient):
        client.dashboards.update(dashboard_id=5, config={"name": "Updated"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/dashboards/5")

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

    def test_share(self, client: MammothClient):
        client.dashboards.share(dashboard_id=5, config={"emails": ["a@b.com"]})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/5/share")

    def test_action(self, client: MammothClient):
        client.dashboards.action(dashboard_id=5, action_config={"type": "refresh"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/dashboards/5/action")

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


# ======================================================================
# AutomationsAPI
# ======================================================================


class TestAutomationsAPI:
    def test_list(self, client: MammothClient):
        client.automations.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/automations")

    def test_create(self, client: MammothClient):
        client.automations.create(config={"name": "Auto1"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/automations")

    def test_get(self, client: MammothClient):
        client.automations.get(automation_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/automations/10")

    def test_update(self, client: MammothClient):
        client.automations.update(automation_id=10, config={"name": "Renamed"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/automations/10")

    def test_delete(self, client: MammothClient):
        client.automations.delete(automation_id=10)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/automations/10")

    def test_list_schedules(self, client: MammothClient):
        client.automations.list_schedules()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules")

    def test_create_schedule(self, client: MammothClient):
        client.automations.create_schedule(config={"cron": "0 * * * *"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")

    def test_update_schedule(self, client: MammothClient):
        client.automations.update_schedule(schedule_id=5, config={"cron": "0 0 * * *"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/schedules/5")

    def test_delete_schedule(self, client: MammothClient):
        client.automations.delete_schedule(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/schedules/5")


# ======================================================================
# SchedulesAPI
# ======================================================================


class TestSchedulesAPI:
    def test_list(self, client: MammothClient):
        client.schedules.list()
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules")

    def test_get(self, client: MammothClient):
        client.schedules.get(schedule_id=5)
        assert_called_with_method_and_endpoint(client._request_json, "GET", "/schedules/5")

    def test_create(self, client: MammothClient):
        client.schedules.create(config={"cron": "0 * * * *"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/schedules")

    def test_update(self, client: MammothClient):
        client.schedules.update(schedule_id=5, config={"cron": "0 0 * * *"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/schedules/5")

    def test_delete(self, client: MammothClient):
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

    def test_create(self, client: MammothClient):
        client.batches.create(dataset_id=500, config={"name": "b1"})
        assert_called_with_method_and_endpoint(
            client._request_json, "POST", "/datasets/500/batches"
        )

    def test_update(self, client: MammothClient):
        client.batches.update(dataset_id=500, config={"name": "b1_updated"})
        assert_called_with_method_and_endpoint(
            client._request_json, "PATCH", "/datasets/500/batches"
        )

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

    def test_create(self, client: MammothClient):
        client.external_keys.create(config={"name": "key1"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/external_keys")

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
    def test_add_connector(self, client: MammothClient):
        client.addons.add_connector(config={"type": "salesforce"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/connectors")

    def test_remove_connector(self, client: MammothClient):
        client.addons.remove_connector(config={"type": "salesforce"})
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/connectors")

    def test_add_storage(self, client: MammothClient):
        client.addons.add_storage(config={"type": "s3"})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/storage")

    def test_remove_storage(self, client: MammothClient):
        client.addons.remove_storage(config={"type": "s3"})
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/storage")

    def test_add_users(self, client: MammothClient):
        client.addons.add_users(config={"count": 5})
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/addons/users")

    def test_remove_users(self, client: MammothClient):
        client.addons.remove_users(config={"count": 5})
        assert_called_with_method_and_endpoint(client._request_json, "DELETE", "/addons/users")


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

    def test_update(self, client: MammothClient):
        client.workspaces.update(config={"name": "New WS Name"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/workspaces/1")

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

    def test_update_user(self, client: MammothClient):
        client.workspaces.update_user(user_id="u1", config={"role": "admin"})
        assert_called_with_method_and_endpoint(client._request_json, "PATCH", "/users/u1")


# ======================================================================
# AIAPI
# ======================================================================


class TestAIAPI:
    def test_generate_profile(self, client: MammothClient):
        client.ai.generate_profile(dataview_id=42, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/profile_generation")

    def test_generate_data(self, client: MammothClient):
        client.ai.generate_data(dataview_id=42, config={"rows": 100}, dataset_id=500)
        assert_called_with_method_and_endpoint(client._request_json, "POST", "/data/generate")

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
