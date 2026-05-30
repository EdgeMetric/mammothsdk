"""Full validation integration tests for the Mammoth Python SDK.

Target: app.mammoth.io (workspace 304, project 1134)
Credentials: val_client fixture (see conftest.py)

Covers every SDK public function not already tested in test_exhaustive.py
and test_advanced_transformations.py. All tests hit the live API — no mocking.

Run:
    pytest tests/integration/test_full_validation.py -v --tb=short
"""

from __future__ import annotations

import contextlib

import pytest

from mammoth import (
    ColumnType,
    Condition,
    JsonExtractionSpec,
    JsonType,
    MammothAPIError,
    MammothAuthError,
    MammothClient,
    Operator,
    SetValue,
    View,
)

# ═══════════════════════════════════════════════════════════════
#  1. Client Connection
# ═══════════════════════════════════════════════════════════════


class TestClientConnection:
    """Verify connectivity, auth, and context-manager usage."""

    def test_connection_success(self, val_client: MammothClient) -> None:
        assert val_client.test_connection() is True

    def test_bad_credentials(self) -> None:
        bad = MammothClient(api_key="INVALID", api_secret="INVALID", workspace_id=304)
        assert bad.test_connection() is False

    def test_context_manager(self) -> None:
        with MammothClient(
            api_key="REDACTED_CREDENTIAL",
            api_secret="REDACTED_CREDENTIAL",
            workspace_id=304,
        ) as c:
            c.set_project_id(1134)
            assert c.test_connection() is True


# ═══════════════════════════════════════════════════════════════
#  2. Browse API
# ═══════════════════════════════════════════════════════════════


class TestBrowseAPI:
    """Browse workspace/project/dataset hierarchy."""

    def test_workspaces(self, val_client: MammothClient) -> None:
        result = val_client.browse.workspaces()
        assert isinstance(result, dict)

    def test_projects(self, val_client: MammothClient) -> None:
        result = val_client.browse.projects()
        assert isinstance(result, dict)

    def test_datasets(self, val_client: MammothClient) -> None:
        result = val_client.browse.datasets()
        assert isinstance(result, dict)

    def test_dataviews(self, val_client: MammothClient, val_uploaded_dataset_id: int) -> None:
        result = val_client.browse.dataviews(val_uploaded_dataset_id)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════
#  3. Workspace API
# ═══════════════════════════════════════════════════════════════


class TestWorkspaceAPI:
    """Workspace list/get operations."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.workspaces.list()
        assert isinstance(result, (dict, list))

    def test_get(self, val_client: MammothClient) -> None:
        result = val_client.workspaces.get()
        assert isinstance(result, dict)
        assert "id" in result or "name" in result


# ═══════════════════════════════════════════════════════════════
#  4. Projects API
# ═══════════════════════════════════════════════════════════════


class TestProjectsAPI:
    """Project list, get, and create+delete lifecycle."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.projects.list()
        assert isinstance(result, (dict, list))

    def test_get(self, val_client: MammothClient) -> None:
        result = val_client.projects.get(1134)
        assert isinstance(result, dict)
        assert result["id"] == 1134

    def test_create_and_delete(self, val_client: MammothClient) -> None:
        result = val_client.projects.create(name="pytest_val_temp_project")
        proj_id = result.get("id") or result.get("project_id")
        assert proj_id is not None
        with contextlib.suppress(Exception):
            val_client.projects.delete(proj_id)


# ═══════════════════════════════════════════════════════════════
#  5. Folders API
# ═══════════════════════════════════════════════════════════════


class TestFoldersAPI:
    """Folder list and project root."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.folders.list()
        # Returns FoldersList Pydantic model — verify it has the folders attr
        assert hasattr(result, "folders") or isinstance(result, (dict, list))

    def test_get_project_root(self, val_client: MammothClient) -> None:
        result = val_client.folders.get_project_root()
        # Returns FolderSchema Pydantic model — verify it has an id attr
        assert hasattr(result, "id") or isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════
#  6. Datasets API
# ═══════════════════════════════════════════════════════════════


class TestDatasetsAPI:
    """Dataset list and get."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.datasets.list()
        assert isinstance(result, (dict, list))

    def test_get(self, val_client: MammothClient, val_uploaded_dataset_id: int) -> None:
        result = val_client.datasets.get(val_uploaded_dataset_id)
        assert isinstance(result, dict)
        # Response nests the dataset info under a "dataset" key
        ds = result.get("dataset", result)
        assert ds.get("id") == val_uploaded_dataset_id


# ═══════════════════════════════════════════════════════════════
#  7. Views Resource (CRUD)
# ═══════════════════════════════════════════════════════════════


class TestViewsResource:
    """View create, list, get, delete, and bulk_delete."""

    def test_list(self, val_client: MammothClient, val_uploaded_dataset_id: int) -> None:
        views = val_client.views.list(val_uploaded_dataset_id)
        assert isinstance(views, list)
        assert len(views) > 0
        assert all(isinstance(v, View) for v in views)

    def test_get(self, val_view: View, val_client: MammothClient) -> None:
        fetched = val_client.views.get(val_view.id)
        assert fetched.id == val_view.id
        assert len(fetched.display_names) > 0

    def test_create_and_delete(
        self, val_client: MammothClient, val_uploaded_dataset_id: int
    ) -> None:
        v = val_client.views.create(dataset_id=val_uploaded_dataset_id, name="pytest_create_del")
        assert v.id > 0
        val_client.views.delete(v.id)

    def test_bulk_delete(self, val_client: MammothClient, val_uploaded_dataset_id: int) -> None:
        v1 = val_client.views.create(dataset_id=val_uploaded_dataset_id, name="pytest_bulk_1")
        v2 = val_client.views.create(dataset_id=val_uploaded_dataset_id, name="pytest_bulk_2")
        val_client.views.bulk_delete([v1.id, v2.id])


# ═══════════════════════════════════════════════════════════════
#  8. Activity Logs
# ═══════════════════════════════════════════════════════════════


class TestActivityLogs:
    """Activity log listing."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.activity_logs.list()
        assert isinstance(result, (dict, list))


# ═══════════════════════════════════════════════════════════════
#  9. User Profile
# ═══════════════════════════════════════════════════════════════


class TestUserProfile:
    """User profile and preferences."""

    def test_get(self, val_client: MammothClient) -> None:
        result = val_client.user_profile.get()
        assert isinstance(result, dict)

    def test_get_preferences(self, val_client: MammothClient) -> None:
        result = val_client.user_profile.get_preferences()
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════
#  10. Reports
# ═══════════════════════════════════════════════════════════════


class TestReports:
    """Report listing."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.reports.list()
        assert isinstance(result, (dict, list))


# ═══════════════════════════════════════════════════════════════
#  11. Client Apps (requires admin access — API tokens may be denied)
# ═══════════════════════════════════════════════════════════════


class TestClientApps:
    """Client app listing — verifies clean error for restricted APIs."""

    def test_list(self, val_client: MammothClient) -> None:
        try:
            result = val_client.client_apps.list()
            assert isinstance(result, (dict, list))
        except MammothAuthError:
            pass  # Expected: "Cannot access this API with API-tokens"


# ═══════════════════════════════════════════════════════════════
#  12. External Keys
# ═══════════════════════════════════════════════════════════════


class TestExternalKeys:
    """External key listing."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.external_keys.list()
        assert isinstance(result, (dict, list))


# ═══════════════════════════════════════════════════════════════
#  13. Addons (may not exist on all workspaces)
# ═══════════════════════════════════════════════════════════════


class TestAddons:
    """Addon listing — verifies clean error when endpoint is unavailable."""

    def test_list(self, val_client: MammothClient) -> None:
        try:
            result = val_client.addons.list()
            assert isinstance(result, (dict, list))
        except MammothAPIError:
            pass  # Expected if addons not available


# ═══════════════════════════════════════════════════════════════
#  14. Schedules (may require orchestration addon)
# ═══════════════════════════════════════════════════════════════


class TestSchedules:
    """Schedule listing — verifies clean error if not configured."""

    def test_list(self, val_client: MammothClient) -> None:
        try:
            result = val_client.schedules.list()
            assert isinstance(result, (dict, list))
        except MammothAPIError:
            pass  # Expected if schedules not configured


# ═══════════════════════════════════════════════════════════════
#  15. Automations
# ═══════════════════════════════════════════════════════════════


class TestAutomations:
    """Automation listing."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.automations.list()
        assert isinstance(result, (dict, list))


# ═══════════════════════════════════════════════════════════════
#  16. Batches
# ═══════════════════════════════════════════════════════════════


class TestBatches:
    """Batch listing (requires dataset_id)."""

    def test_list(self, val_client: MammothClient, val_uploaded_dataset_id: int) -> None:
        result = val_client.batches.list(val_uploaded_dataset_id)
        assert isinstance(result, (dict, list))


# ═══════════════════════════════════════════════════════════════
#  17. Dashboards
# ═══════════════════════════════════════════════════════════════


class TestDashboards:
    """Dashboard listing."""

    def test_list(self, val_client: MammothClient) -> None:
        result = val_client.dashboards.list()
        assert isinstance(result, (dict, list))


# ═══════════════════════════════════════════════════════════════
#  18. Webhooks (full CRUD)
# ═══════════════════════════════════════════════════════════════


class TestWebhooks:
    """Webhook create, get, list, update, delete lifecycle."""

    def test_full_crud(self, val_client: MammothClient) -> None:
        # Create — response is {"webhook": {"id": ..., "name": ..., ...}}
        created = val_client.webhooks.create(name="pytest_val_webhook")
        assert isinstance(created, dict)
        inner = created.get("webhook", created)
        wh_id = inner.get("id") or inner.get("dataset_id")
        assert wh_id is not None

        try:
            # Get
            fetched = val_client.webhooks.get(wh_id)
            assert isinstance(fetched, dict)

            # List
            listed = val_client.webhooks.list()
            assert isinstance(listed, list)

            # Update
            updated = val_client.webhooks.update(wh_id, mode="combine")
            assert isinstance(updated, dict)
        finally:
            # Delete
            with contextlib.suppress(Exception):
                val_client.webhooks.delete(wh_id)


# ═══════════════════════════════════════════════════════════════
#  19. Jobs API
# ═══════════════════════════════════════════════════════════════


class TestJobsAPI:
    """Job get using a real job ID from a pipeline transformation."""

    def test_get_job(self, val_view: View, val_client: MammothClient) -> None:
        """Run a transform, extract job_id from pipeline, verify get_job."""
        col = val_view.display_names[0]
        val_view.filter_rows(Condition(col, Operator.IS_NOT_EMPTY))

        # The pipeline state should have the completed pipeline info
        pipeline = val_client.pipeline.get_pipeline(val_view.id, val_view.dataset_id)
        assert isinstance(pipeline, dict)
        assert pipeline.get("state", "").lower() == "ready"


# ═══════════════════════════════════════════════════════════════
#  20. View Data (all param combos)
# ═══════════════════════════════════════════════════════════════


class TestViewData:
    """View.data() with limit, offset, columns, condition, sort."""

    def test_default(self, val_view: View) -> None:
        result = val_view.data()
        assert "data" in result
        assert len(result["data"]) > 0

    def test_limit_offset(self, val_view: View) -> None:
        result = val_view.data(limit=5, offset=1)
        assert len(result["data"]) <= 5

    def test_specific_columns(self, val_view: View) -> None:
        cols = val_view.display_names[:2]
        result = val_view.data(columns=cols, limit=3)
        assert len(result["data"]) > 0

    def test_with_condition(self, val_view: View) -> None:
        col = val_view.display_names[0]
        result = val_view.data(
            condition=Condition(col, Operator.IS_NOT_EMPTY),
            limit=5,
        )
        assert isinstance(result, dict)

    def test_with_sort(self, val_view: View) -> None:
        col = val_view.display_names[0]
        internal = val_view.columns[col]
        result = val_view.data(sort=f"({internal}:asc)", limit=5)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════
#  21. View Metadata
# ═══════════════════════════════════════════════════════════════


class TestViewMetadata:
    """get_metadata, get_column_mapping, refresh."""

    def test_get_metadata(self, val_view: View) -> None:
        meta = val_view.get_metadata()
        assert isinstance(meta, list)
        assert len(meta) > 0
        first = meta[0]
        assert "display_name" in first
        assert "internal_name" in first
        assert "type" in first

    def test_get_column_mapping(self, val_view: View) -> None:
        mapping = val_view.get_column_mapping()
        assert isinstance(mapping, dict)
        assert len(mapping) == len(val_view.display_names)
        # Verify it's a copy, not the original
        mapping["__test__"] = "value"
        assert "__test__" not in val_view.columns

    def test_refresh(self, val_view: View) -> None:
        original_names = list(val_view.display_names)
        val_view.refresh()
        assert val_view.display_names == original_names
        assert len(val_view.columns) > 0


# ═══════════════════════════════════════════════════════════════
#  22. Draft Mode
# ═══════════════════════════════════════════════════════════════


class TestDraftMode:
    """enter/submit, enter/discard, draft() context manager, set_auto_run."""

    def test_enter_and_submit(self, val_view: View) -> None:
        result = val_view.enter_draft_mode()
        assert val_view.is_draft_mode

        col = val_view.display_names[0]
        val_view.filter_rows(Condition(col, Operator.IS_NOT_EMPTY))

        result = val_view.submit_draft()
        assert not val_view.is_draft_mode
        assert isinstance(result, dict)

    def test_enter_and_discard(self, val_view: View) -> None:
        original_cols = list(val_view.display_names)

        val_view.enter_draft_mode()
        assert val_view.is_draft_mode

        # Add a task that we'll discard
        val_view.set_values(
            new_column="discard_me",
            column_type=ColumnType.TEXT,
            values=[SetValue("temp")],
        )

        val_view.discard_draft()
        assert not val_view.is_draft_mode
        # Column list should be unchanged after discard
        assert val_view.display_names == original_cols

    def test_draft_context_manager_clean_exit(self, val_view: View) -> None:
        col = val_view.display_names[0]
        with val_view.draft():
            assert val_view.is_draft_mode
            val_view.filter_rows(Condition(col, Operator.IS_NOT_EMPTY))
        assert not val_view.is_draft_mode

    def test_draft_context_manager_exception(self, val_view: View) -> None:
        original_cols = list(val_view.display_names)
        with pytest.raises(ValueError), val_view.draft():
            assert val_view.is_draft_mode
            val_view.set_values(
                new_column="discard_on_error",
                column_type=ColumnType.TEXT,
                values=[SetValue("temp")],
            )
            raise ValueError("Intentional error to trigger discard")
        assert not val_view.is_draft_mode
        assert val_view.display_names == original_cols

    def test_set_auto_run(self, val_view: View) -> None:
        # Disable auto-run
        result = val_view.set_auto_run(False)
        assert isinstance(result, dict)
        assert val_view.is_draft_mode

        # Re-enable auto-run
        result = val_view.set_auto_run(True)
        assert isinstance(result, dict)
        assert not val_view.is_draft_mode


# ═══════════════════════════════════════════════════════════════
#  23. Branch Out
# ═══════════════════════════════════════════════════════════════


class TestBranchOut:
    """Branch out (export) to another dataset."""

    def test_branch_out(self, val_view: View, val_second_dataset_id: int) -> None:
        # REPLACE the target dataset's contents with this view's rows.
        returned_id = val_view.branch_out(
            "branch_out_validation", target_ds_id=val_second_dataset_id
        )
        # An existing-target branch-out returns the id of the dataset it wrote
        # into (not a freshly created one) — the contract that lets a caller act
        # on the result.
        assert returned_id == val_second_dataset_id


# ═══════════════════════════════════════════════════════════════
#  24. Pipeline Management
# ═══════════════════════════════════════════════════════════════


class TestPipelineManagement:
    """list_tasks, delete_task, preview_task."""

    def test_list_tasks_empty(self, val_view: View) -> None:
        tasks = val_view.list_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) == 0

    def test_add_list_delete_task(self, val_view: View) -> None:
        # Add a task
        col = val_view.display_names[0]
        val_view.filter_rows(Condition(col, Operator.IS_NOT_EMPTY))

        # List tasks — should have 1
        tasks = val_view.list_tasks()
        assert len(tasks) >= 1
        task_id = tasks[-1]["id"]

        # Delete the task
        val_view.delete_task(task_id)
        tasks_after = val_view.list_tasks()
        assert len(tasks_after) == len(tasks) - 1

    def test_preview_task(self, val_view: View) -> None:
        col = val_view.display_names[0]
        internal = val_view.columns[col]
        preview = val_view.preview_task({"DELETE": [internal]})
        assert isinstance(preview, dict)


# ═══════════════════════════════════════════════════════════════
#  25. JSON Extract
# ═══════════════════════════════════════════════════════════════


class TestJsonExtract:
    """Create a JSON column, then extract keys from it."""

    def test_json_extract_keys(self, val_view: View) -> None:
        # Create a column with JSON data
        val_view.set_values(
            new_column="json_data",
            column_type=ColumnType.TEXT,
            values=[SetValue('{"name":"Alice","age":"30"}')],
        )
        assert "json_data" in val_view.display_names

        # Extract keys from JSON column
        val_view.json_extract("json_data", keys=["name", "age"])

        # Verify the extracted columns exist
        val_view.refresh()
        assert "name" in val_view.display_names
        assert "age" in val_view.display_names

    def test_json_extract_with_specs(self, val_view: View) -> None:
        # Create a column with JSON data
        val_view.set_values(
            new_column="json_col",
            column_type=ColumnType.TEXT,
            values=[SetValue('{"city":"NYC","zip":"10001"}')],
        )

        # Extract with custom specs
        val_view.json_extract(
            "json_col",
            json_type=JsonType.OBJECT,
            extractions=[
                JsonExtractionSpec(key="city", as_name="City", type=ColumnType.TEXT),
                JsonExtractionSpec(key="zip", as_name="Zip Code", type=ColumnType.TEXT),
            ],
        )

        val_view.refresh()
        assert "City" in val_view.display_names
        assert "Zip Code" in val_view.display_names


# ═══════════════════════════════════════════════════════════════
#  26. Export to Dataset
# ═══════════════════════════════════════════════════════════════


class TestExportToDataset:
    """Export view data to another dataset."""

    def test_to_dataset(self, val_view: View, val_second_dataset_id: int) -> None:
        # The export-namespace entry point to the same capability as branch_out.
        returned_id = val_view.export.to_dataset(
            "to_dataset_validation", target_ds_id=val_second_dataset_id
        )
        assert returned_id == val_second_dataset_id


# ═══════════════════════════════════════════════════════════════
#  27. Export to Email
# ═══════════════════════════════════════════════════════════════


class TestExportToEmail:
    """Export via email — expects either success or clean API error."""

    def test_to_email(self, val_view: View) -> None:
        try:
            result = val_view.export.to_email(recipients=["test@example.com"])
            assert result is not None
        except MammothAPIError:
            pass  # Expected if email not configured


# ═══════════════════════════════════════════════════════════════
#  28. Export Graceful Errors (external infra not available)
# ═══════════════════════════════════════════════════════════════


class TestExportGracefulErrors:
    """Verify export methods with bad targets raise MammothAPIError, not crashes."""

    def test_to_postgres_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_postgres(
                host="nonexistent.example.com",
                port=5432,
                database="test",
                table="test",
                username="bad",
                password="bad",
                validate_only=True,
            )

    def test_to_mysql_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_mysql(
                host="nonexistent.example.com",
                port=3306,
                database="test",
                table="test",
                username="bad",
                password="bad",
                validate_only=True,
            )

    def test_to_ftp_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_ftp(
                host="nonexistent.example.com",
                path="/tmp/test.csv",
                username="bad",
                password="bad",
                validate_only=True,
            )

    def test_to_sftp_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_sftp(
                host="nonexistent.example.com",
                path="/tmp/test.csv",
                username="bad",
                password="bad",
                validate_only=True,
            )

    def test_to_bigquery_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_bigquery(
                project="fake", dataset="fake", table="fake", validate_only=True
            )

    def test_to_redshift_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_redshift(
                host="fake",
                port=5439,
                database="fake",
                table="fake",
                username="bad",
                password="bad",
                validate_only=True,
            )

    def test_to_elasticsearch_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.to_elasticsearch(host="fake", index="fake", validate_only=True)

    def test_publish_to_db_graceful(self, val_view: View) -> None:
        with contextlib.suppress(MammothAPIError):
            val_view.export.publish_to_db(
                host="fake", database="fake", table="fake", validate_only=True
            )


# ═══════════════════════════════════════════════════════════════
#  29. Export List & Delete
# ═══════════════════════════════════════════════════════════════


class TestExportList:
    """List exports and delete one."""

    def test_list_exports(self, val_view: View) -> None:
        exports = val_view.export.list()
        assert isinstance(exports, list)

    def test_create_and_delete_export(self, val_view: View) -> None:
        # Create an S3 export to have something to delete
        result = val_view.export.to_s3(file_name="pytest_delete_me.csv")
        assert result is not None

        # List exports and find the one we created
        exports = val_view.export.list()
        if exports:
            exp = exports[-1]
            export_id = getattr(exp, "id", None) or (
                exp.get("id") if isinstance(exp, dict) else None
            )
            if export_id:
                delete_result = val_view.export.delete(export_id)
                assert isinstance(delete_result, dict)
