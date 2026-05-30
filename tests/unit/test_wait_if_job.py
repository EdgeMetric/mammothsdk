"""Unit tests for _wait_if_job() centralized job detection and waiting."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mammoth.client import MammothClient
from mammoth.view import View

from .conftest import SAMPLE_DATASET_ID, SAMPLE_VIEW_DATA

# ── Helpers ──────────────────────────────────────────────────


def _make_client() -> MammothClient:
    """Create a MammothClient with mocked HTTP and jobs."""
    with patch("mammoth.client.requests.Session"):
        client = MammothClient(
            api_key="test-key",
            api_secret="test-secret",
            workspace_id=1,
        )
    client.project_id = 100
    client._request_json = MagicMock(return_value={})
    client.jobs = MagicMock()
    client.jobs.wait_for_job = MagicMock(
        return_value={"status": "success", "response": {"rows": [1, 2, 3]}}
    )
    return client


# ── _wait_if_job core logic ──────────────────────────────────


class TestWaitIfJobPatterns:
    """Test that _wait_if_job detects all 3 job response schemas."""

    def setup_method(self):
        self.client = _make_client()

    def test_pattern_job_id(self):
        """Pattern 1: {"job_id": N} (ObjectJobSchema)."""
        response = {"job_id": 42}
        result = self.client._wait_if_job(response)
        self.client.jobs.wait_for_job.assert_called_once_with(42, timeout=60, poll_interval=2)
        assert result == {"rows": [1, 2, 3]}

    def test_pattern_job_dict(self):
        """Pattern 2: {"job": {"id": N}} (JobResponse)."""
        response = {"job": {"id": 99, "status": "processing"}}
        result = self.client._wait_if_job(response)
        self.client.jobs.wait_for_job.assert_called_once_with(99, timeout=60, poll_interval=2)
        assert result == {"rows": [1, 2, 3]}

    def test_pattern_response_job_schema(self):
        """Pattern 3: {"id": N, "status": "processing"} (ResponseJobSchema)."""
        response = {"id": 77, "status": "processing"}
        result = self.client._wait_if_job(response)
        self.client.jobs.wait_for_job.assert_called_once_with(77, timeout=60, poll_interval=2)
        assert result == {"rows": [1, 2, 3]}

    def test_pattern_response_job_schema_success(self):
        """Pattern 3 also triggers on status=success."""
        response = {"id": 77, "status": "success"}
        self.client._wait_if_job(response)
        self.client.jobs.wait_for_job.assert_called_once()

    def test_pattern_response_job_schema_failure(self):
        """Pattern 3 also triggers on status=failure."""
        response = {"id": 77, "status": "failure"}
        self.client._wait_if_job(response)
        self.client.jobs.wait_for_job.assert_called_once()

    def test_pattern_response_job_schema_error(self):
        """Pattern 3 also triggers on status=error."""
        response = {"id": 77, "status": "error"}
        self.client._wait_if_job(response)
        self.client.jobs.wait_for_job.assert_called_once()


class TestWaitIfJobPassthrough:
    """Test that non-job responses pass through unchanged."""

    def setup_method(self):
        self.client = _make_client()

    def test_plain_dict(self):
        """Regular data dict passes through without job waiting."""
        data = {"columns": ["a", "b"], "rows": [[1, 2]]}
        result = self.client._wait_if_job(data)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data

    def test_empty_dict(self):
        result = self.client._wait_if_job({})
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == {}

    def test_dict_with_id_but_no_status(self):
        """A dict with 'id' but no 'status' is NOT a job reference."""
        data = {"id": 42, "name": "my_view"}
        result = self.client._wait_if_job(data)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data

    def test_dict_with_id_and_unknown_status(self):
        """A dict with 'id' + unrecognized status is NOT a job reference."""
        data = {"id": 42, "status": "active"}
        result = self.client._wait_if_job(data)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data

    def test_job_key_is_not_dict(self):
        """If 'job' key is a string/int (not a dict), skip."""
        data = {"job": "some_string"}
        result = self.client._wait_if_job(data)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data


class TestWaitIfJobTimeoutForwarding:
    """Test timeout and poll_interval forwarding."""

    def setup_method(self):
        self.client = _make_client()

    def test_custom_timeout(self):
        self.client._wait_if_job({"job_id": 1}, timeout=120)
        self.client.jobs.wait_for_job.assert_called_once_with(1, timeout=120, poll_interval=2)

    def test_custom_poll_interval(self):
        self.client._wait_if_job({"job_id": 1}, poll_interval=5)
        self.client.jobs.wait_for_job.assert_called_once_with(1, timeout=60, poll_interval=5)

    def test_uses_client_job_timeout_as_default(self):
        self.client.job_timeout = 300
        self.client._wait_if_job({"job_id": 1})
        self.client.jobs.wait_for_job.assert_called_once_with(1, timeout=300, poll_interval=2)

    def test_completed_job_without_response_key(self):
        """When completed job has no 'response' key, return the whole job dict."""
        self.client.jobs.wait_for_job.return_value = {"status": "success", "id": 1}
        result = self.client._wait_if_job({"job_id": 1})
        assert result == {"status": "success", "id": 1}


# ── Integration: dataviews.get_data / query_data ─────────────


class TestDataviewsJobWaiting:
    """Test that dataviews methods delegate to _wait_if_job."""

    def setup_method(self):
        self.client = _make_client()
        self.client.project_id = 100

    def test_get_data_with_job_response(self):
        self.client._request_json = MagicMock(return_value={"job_id": 55})
        result = self.client.dataviews.get_data(dataset_id=10, dataview_id=20)
        self.client.jobs.wait_for_job.assert_called_once_with(55, timeout=60, poll_interval=2)
        assert result == {"rows": [1, 2, 3]}

    def test_get_data_without_job(self):
        data = {"columns": [], "rows": []}
        self.client._request_json = MagicMock(return_value=data)
        result = self.client.dataviews.get_data(dataset_id=10, dataview_id=20)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data

    def test_get_data_custom_timeout(self):
        self.client._request_json = MagicMock(return_value={"job_id": 55})
        self.client.dataviews.get_data(dataset_id=10, dataview_id=20, timeout=120, poll_interval=5)
        self.client.jobs.wait_for_job.assert_called_once_with(55, timeout=120, poll_interval=5)

    def test_query_data_with_job_response(self):
        self.client._request_json = MagicMock(return_value={"id": 66, "status": "processing"})
        result = self.client.dataviews.query_data(dataset_id=10, dataview_id=20)
        self.client.jobs.wait_for_job.assert_called_once()
        assert result == {"rows": [1, 2, 3]}

    def test_query_data_without_job(self):
        data = {"columns": [], "rows": [[1]]}
        self.client._request_json = MagicMock(return_value=data)
        result = self.client.dataviews.query_data(dataset_id=10, dataview_id=20)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data


# ── Integration: pipeline methods ────────────────────────────


class TestPipelineJobWaiting:
    """Test that pipeline methods delegate to _wait_if_job."""

    def setup_method(self):
        self.client = _make_client()
        # We need a real PipelineAPI, so don't mock pipeline
        from mammoth.api.pipeline import PipelineAPI

        self.client.pipeline = PipelineAPI(self.client)

    def test_add_task_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 101, "status": "processing"}}
        )
        result = self.client.pipeline.add_task(
            dataview_id=20, task_spec={"TYPE": "SET"}, dataset_id=10
        )
        self.client.jobs.wait_for_job.assert_called_once_with(101, timeout=60, poll_interval=2)
        assert result == {"rows": [1, 2, 3]}

    def test_delete_task_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 102, "status": "processing"}}
        )
        self.client.pipeline.delete_task(dataview_id=20, task_id=5, dataset_id=10)
        self.client.jobs.wait_for_job.assert_called_once()

    def test_update_task_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 103, "status": "processing"}}
        )
        self.client.pipeline.update_task(
            dataview_id=20, task_id=5, task_spec={"TYPE": "SET"}, dataset_id=10
        )
        self.client.jobs.wait_for_job.assert_called_once()

    def test_preview_task_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 104, "status": "processing"}}
        )
        self.client.pipeline.preview_task(dataview_id=20, task_spec={"TYPE": "SET"}, dataset_id=10)
        self.client.jobs.wait_for_job.assert_called_once()

    def test_draft_mode_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 105, "status": "processing"}}
        )
        self.client.pipeline.draft_mode(dataview_id=20, command="enter", dataset_id=10)
        self.client.jobs.wait_for_job.assert_called_once()

    def test_add_task_no_job_passthrough(self):
        """When pipeline returns no job reference, pass through."""
        data = {"task_id": 5, "TYPE": "SET"}
        self.client._request_json = MagicMock(return_value=data)
        result = self.client.pipeline.add_task(
            dataview_id=20, task_spec={"TYPE": "SET"}, dataset_id=10
        )
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data


# ── Integration: view._add_task no double-waiting ────────────


class TestViewAddTaskSimplified:
    """Test that view._add_task() no longer double-waits."""

    def setup_method(self):
        self.client = _make_client()
        # Real PipelineAPI + real DataviewsAPI for refresh()
        from mammoth.api.dataviews import DataviewsAPI
        from mammoth.api.pipeline import PipelineAPI

        self.client.pipeline = PipelineAPI(self.client)
        self.client.dataviews = DataviewsAPI(self.client)

    def test_add_task_waits_once(self):
        """pipeline.add_task waits for job; then wait_for_pipeline waits for readiness."""

        def counting_request_json(method, url, **kwargs):
            if "/pipeline/tasks" in url and method == "POST":
                return {"job": {"id": 200, "status": "processing"}}
            if url.endswith("/pipeline") and method == "GET":
                return {"state": "ready"}
            # refresh GET requests
            return SAMPLE_VIEW_DATA

        self.client._request_json = MagicMock(side_effect=counting_request_json)

        view = View(self.client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view._add_task({"TYPE": "SET"})

        # wait_for_job called exactly once (by pipeline.add_task)
        self.client.jobs.wait_for_job.assert_called_once_with(200, timeout=60, poll_interval=2)


# ── Integration: ai methods ──────────────────────────────────


class TestAIJobWaiting:
    """Test that AI methods delegate to _wait_if_job."""

    def setup_method(self):
        self.client = _make_client()
        from mammoth.api.ai import AIAPI

        self.client.ai = AIAPI(self.client)
        # Mock _find_dataset_for_dataview to avoid HTTP
        self.client.pipeline = MagicMock()
        self.client.pipeline._find_dataset_for_dataview = MagicMock(return_value=10)

    def test_generate_profile_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 301, "status": "processing"}}
        )
        self.client.ai.generate_profile(dataview_id=20)
        self.client.jobs.wait_for_job.assert_called_once()

    def test_generate_sql_waits(self):
        self.client._request_json = MagicMock(return_value={"id": 302, "status": "processing"})
        self.client.ai.generate_sql(intent="total sales")
        self.client.jobs.wait_for_job.assert_called_once()

    def test_get_suggestions_waits(self):
        self.client._request_json = MagicMock(return_value={"job_id": 303})
        self.client.ai.get_suggestions()
        self.client.jobs.wait_for_job.assert_called_once()

    def test_generate_data_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 304, "status": "processing"}}
        )
        self.client.ai.generate_data(dataview_id=20, config={"rows": 100})
        self.client.jobs.wait_for_job.assert_called_once()

    def test_query_gen_waits(self):
        self.client._request_json = MagicMock(
            return_value={"job": {"id": 305, "status": "processing"}}
        )
        self.client.ai.query_gen(connector_key="pg", connection_key="conn1", prompt="show tables")
        self.client.jobs.wait_for_job.assert_called_once()


# ── Integration: datasets.get_data refactored ────────────────


class TestDatasetsGetDataRefactored:
    """Test that datasets.get_data uses _wait_if_job."""

    def setup_method(self):
        self.client = _make_client()
        from mammoth.api.datasets import DatasetsAPI

        self.client.datasets = DatasetsAPI(self.client)

    def test_get_data_job_id_pattern(self):
        self.client._request_json = MagicMock(return_value={"job_id": 401})
        result = self.client.datasets.get_data(dataset_id=10)
        self.client.jobs.wait_for_job.assert_called_once_with(401, timeout=300, poll_interval=2)
        assert result == {"rows": [1, 2, 3]}

    def test_get_data_no_job(self):
        data = {"columns": [], "rows": []}
        self.client._request_json = MagicMock(return_value=data)
        result = self.client.datasets.get_data(dataset_id=10)
        self.client.jobs.wait_for_job.assert_not_called()
        assert result == data

    def test_get_data_custom_timeout(self):
        self.client._request_json = MagicMock(return_value={"job_id": 402})
        self.client.datasets.get_data(dataset_id=10, timeout=600, poll_interval=5)
        self.client.jobs.wait_for_job.assert_called_once_with(402, timeout=600, poll_interval=5)
