"""Unit tests for the DerivativesAPI client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.derivatives import DerivativesAPI
from mammoth.exceptions import MammothValidationError

_BASE = "/workspaces/2/projects/100/datasets/1/dataviews/9/derivatives"


def _make_api() -> tuple[DerivativesAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = DerivativesAPI(mock_client)
    return api, mock_client


class TestDerivativesAPIList:
    def test_list(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"derivatives": []}
        api.list(dataset_id=1, dataview_id=9)
        mock_client._request_json.assert_called_once_with("GET", _BASE)

    def test_list_invalid_dataset_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataset_id"):
            api.list(dataset_id=0, dataview_id=9)


class TestDerivativesAPICreate:
    def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 4}
        api.create(dataset_id=1, dataview_id=9, body={"type": "summary"})
        mock_client._request_json.assert_called_once_with("POST", _BASE, json={"type": "summary"})

    def test_create_invalid_dataview_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="dataview_id"):
            api.create(dataset_id=1, dataview_id=-1, body={})


class TestDerivativesAPIData:
    def test_data(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"rows": []}
        api.data(dataset_id=1, dataview_id=9, derivative_id=4, body={"limit": 10})
        mock_client._request_json.assert_called_once_with(
            "POST", f"{_BASE}/4/data", json={"limit": 10}
        )

    def test_data_invalid_derivative_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="derivative_id"):
            api.data(dataset_id=1, dataview_id=9, derivative_id=0, body={})


class TestDerivativesAPIUpdate:
    def test_update(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update(dataset_id=1, dataview_id=9, derivative_id=4, body={"name": "renamed"})
        mock_client._request_json.assert_called_once_with(
            "PATCH", f"{_BASE}/4", json={"name": "renamed"}
        )


class TestDerivativesAPIDelete:
    def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete(dataset_id=1, dataview_id=9, derivative_id=4)
        mock_client._request_json.assert_called_once_with("DELETE", f"{_BASE}/4")

    def test_delete_invalid_project_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="project_id"):
            api.delete(dataset_id=1, dataview_id=9, derivative_id=4, project_id=-5)


class TestDerivativesAPIProjectRequired:
    def test_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = DerivativesAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            api.list(dataset_id=1, dataview_id=9)
