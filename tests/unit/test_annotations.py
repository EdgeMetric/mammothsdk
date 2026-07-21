"""Unit tests for the Annotations API client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.annotations import AnnotationsAPI
from mammoth.exceptions import MammothValidationError


def _make_api() -> tuple[AnnotationsAPI, MagicMock]:
    """Create an AnnotationsAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = AnnotationsAPI(mock_client)
    return api, mock_client


class TestAnnotationsAPIList:
    def test_list_no_filters(self):
        api, mock_client = _make_api()
        mock_client._request_list.return_value = [{"id": 1}]
        result = api.list()
        mock_client._request_list.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/annotations",
            params=None,
        )
        assert result == [{"id": 1}]

    def test_list_with_filters(self):
        api, mock_client = _make_api()
        mock_client._request_list.return_value = []
        api.list(target_type="dataview", target_id=42)
        mock_client._request_list.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/annotations",
            params={"target_type": "dataview", "target_id": 42},
        )

    def test_list_invalid_target_type(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="target_type"):
            api.list(target_type="bogus")

    def test_list_explicit_project_id(self):
        api, mock_client = _make_api()
        mock_client._request_list.return_value = []
        api.list(project_id=7)
        path = mock_client._request_list.call_args[0][1]
        assert path == "/workspaces/2/projects/7/annotations"


class TestAnnotationsAPICreate:
    def test_create(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        result = api.create(target_type="dataview", target_id=42, body="hello")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/annotations",
            json={"target_type": "dataview", "target_id": 42, "body": "hello"},
        )
        assert result == {"id": 1}

    def test_create_invalid_target_type(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="target_type"):
            api.create(target_type="bogus", target_id=42, body="hello")

    def test_create_non_positive_target_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="target_id"):
            api.create(target_type="dataview", target_id=0, body="hello")

    def test_create_empty_body(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="body"):
            api.create(target_type="dataview", target_id=42, body="")


class TestAnnotationsAPIDelete:
    def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete(5)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/workspaces/2/projects/100/annotations/5"
        )

    def test_delete_non_positive_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="annotation_id"):
            api.delete(0)


class TestAnnotationsAPIUpdate:
    def test_update_status(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"status": "resolved"}
        result = api.update(5, status="resolved")
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/annotations/5",
            json={"status": "resolved"},
        )
        assert result["status"] == "resolved"

    def test_update_invalid_status(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="status"):
            api.update(5, status="bogus")

    def test_update_non_positive_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="annotation_id"):
            api.update(0, status="open")


class TestAnnotationsAPICommentAdd:
    def test_comment_add(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1, "body": "hi"}
        result = api.comment_add(5, body="hi")
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/annotations/5/comments",
            json={"body": "hi"},
        )
        assert result["body"] == "hi"

    def test_comment_add_empty_body(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="body"):
            api.comment_add(5, body="")

    def test_comment_add_non_positive_id(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="annotation_id"):
            api.comment_add(0, body="hi")


class TestAnnotationsAPIProjectRequired:
    def test_list_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = AnnotationsAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            api.list()
