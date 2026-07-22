"""Unit tests for the PipelineVersionsAPI client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.pipeline_versions import PipelineVersionsAPI
from mammoth.exceptions import MammothValidationError

_BASE = "/workspaces/2/projects/100/datasets/1/dataviews/9/pipeline/versions"


def _make_api() -> tuple[PipelineVersionsAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = PipelineVersionsAPI(mock_client)
    return api, mock_client


class TestPipelineVersionsAPIList:
    def test_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"versions": []}
        api.list(dataset_id=1, dataview_id=9)
        mock_client._request_json.assert_called_once_with("GET", _BASE, params=None)

    def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"versions": []}
        api.list(
            dataset_id=1,
            dataview_id=9,
            fields="__standard",
            sort="(id:asc)",
            limit=10,
            offset=5,
            name="v1",
        )
        mock_client._request_json.assert_called_once_with(
            "GET",
            _BASE,
            params={
                "fields": "__standard",
                "sort": "(id:asc)",
                "limit": 10,
                "offset": 5,
                "name": "v1",
            },
        )

    def test_list_invalid_dataset_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataset_id"):
            api.list(dataset_id=0, dataview_id=9)


class TestPipelineVersionsAPIGet:
    def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 3}
        result = api.get(dataset_id=1, dataview_id=9, version_id=3)
        mock_client._request_json.assert_called_once_with("GET", f"{_BASE}/3", params=None)
        assert result == {"id": 3}

    def test_get_invalid_version_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="version_id"):
            api.get(dataset_id=1, dataview_id=9, version_id=0)


class TestPipelineVersionsAPIApply:
    def test_apply(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready"}
        api.apply(dataset_id=1, dataview_id=9, version_id=3)
        mock_client._request_json.assert_called_once_with("POST", f"{_BASE}/3")

    def test_apply_invalid_version_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="version_id"):
            api.apply(dataset_id=1, dataview_id=9, version_id=-1)


class TestPipelineVersionsAPIUpdate:
    def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update(dataset_id=1, dataview_id=9, version_id=3, body={"name": "renamed"})
        mock_client._request_json.assert_called_once_with(
            "PATCH", f"{_BASE}/3", json={"name": "renamed"}
        )


class TestPipelineVersionsAPIDelete:
    def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete(dataset_id=1, dataview_id=9, version_id=3)
        mock_client._request_json.assert_called_once_with("DELETE", f"{_BASE}/3")

    def test_delete_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="project_id"):
            api.delete(dataset_id=1, dataview_id=9, version_id=3, project_id=-5)


class TestPipelineVersionsAPIProjectRequired:
    def test_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = PipelineVersionsAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            api.list(dataset_id=1, dataview_id=9)
