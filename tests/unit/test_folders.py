"""Unit tests for the FoldersAPI client, in particular ``move``'s id resolution.

``FoldersAPI.move`` sends the folder-move PATCH body straight to
``/workspaces/{ws}/projects/{proj}/folders``, whose ``from`` field is matched
against ``Resource.resource_id`` server-side -- a different number from a
dataset's or view's own id. ``dataset_ids``/``view_ids`` resolve those object
ids to resource ids via the bulk resource-lookup endpoint before building the
request; ``resource_ids`` stays available for callers that already have a
resource id (see T2-J-013).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mammoth.api.folders import FoldersAPI
from mammoth.exceptions import MammothValidationError

_FOLDERS_URL = "/workspaces/2/projects/100/folders"
_BULK_URL = "/workspaces/2/projects/100/resources/bulk"


def _make_api() -> tuple[FoldersAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = FoldersAPI(mock_client)
    return api, mock_client


class TestFoldersAPIMoveResourceIds:
    """Backward-compatible path: caller already has resource ids."""

    def test_move_with_resource_ids(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"job_id": 1}
        api.move(resource_ids=["8"], target_folder_resource_id="3445", project_id=100)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            _FOLDERS_URL,
            json={"patch": [{"op": "move", "from": [8], "path": 3445}]},
        )

    def test_move_to_root(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"job_id": 1}
        api.move(resource_ids=["8"], project_id=100)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            _FOLDERS_URL,
            json={"patch": [{"op": "move", "from": [8], "path": "root"}]},
        )

    def test_move_no_ids_at_all_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="resource_ids.*dataset_ids.*view_ids"):
            api.move(project_id=100)

    def test_move_bad_resource_id_raises(self):
        api, _ = _make_api()
        with pytest.raises(MammothValidationError, match="resource_ids"):
            api.move(resource_ids=["not-an-int"], project_id=100)


class TestFoldersAPIMoveDatasetViewIds:
    """dataset_ids/view_ids: the obvious agent call, resolved server-side ids."""

    def test_move_with_dataset_ids_resolves_resource_id(self):
        api, mock_client = _make_api()
        mock_client._request_json.side_effect = [
            {"resources": [{"resource_type": "datasource", "object_id": 1407, "resource_id": 55}]},
            {"job_id": 1},
        ]
        api.move(dataset_ids=[1407], target_folder_resource_id="3445", project_id=100)

        bulk_call, patch_call = mock_client._request_json.call_args_list
        assert bulk_call.args == ("POST", _BULK_URL)
        assert bulk_call.kwargs["json"] == {"ids": [{"type": "datasource", "id": 1407}]}
        assert bulk_call.kwargs["operation_effect"] == "read"
        assert patch_call.args == (
            "PATCH",
            _FOLDERS_URL,
        )
        assert patch_call.kwargs["json"] == {"patch": [{"op": "move", "from": [55], "path": 3445}]}

    def test_move_with_view_ids_resolves_resource_id(self):
        api, mock_client = _make_api()
        mock_client._request_json.side_effect = [
            {"resources": [{"resource_type": "dataview", "object_id": 42, "resource_id": 9}]},
            {"job_id": 1},
        ]
        api.move(view_ids=[42], target_folder_resource_id="root", project_id=100)

        bulk_call = mock_client._request_json.call_args_list[0]
        assert bulk_call.kwargs["json"] == {"ids": [{"type": "dataview", "id": 42}]}

    def test_move_merges_resource_ids_and_dataset_ids(self):
        api, mock_client = _make_api()
        mock_client._request_json.side_effect = [
            {"resources": [{"resource_type": "datasource", "object_id": 1407, "resource_id": 55}]},
            {"job_id": 1},
        ]
        api.move(
            resource_ids=["8"],
            dataset_ids=[1407],
            target_folder_resource_id="3445",
            project_id=100,
        )
        patch_call = mock_client._request_json.call_args_list[1]
        assert patch_call.kwargs["json"]["patch"][0]["from"] == [8, 55]

    def test_move_unresolvable_dataset_id_raises_loudly(self):
        api, mock_client = _make_api()
        # Bulk endpoint silently omits ids it couldn't find or the caller
        # can't access -- the wire evidence of the wrong-id-kind bug.
        mock_client._request_json.return_value = {"resources": []}
        with pytest.raises(MammothValidationError, match="dataset 1407"):
            api.move(dataset_ids=[1407], project_id=100)

    def test_move_partial_resolution_reports_only_the_missing_id(self):
        api, mock_client = _make_api()
        mock_client._request_json.side_effect = [
            {"resources": [{"resource_type": "datasource", "object_id": 1407, "resource_id": 55}]},
        ]
        with pytest.raises(MammothValidationError, match="dataset 999"):
            api.move(dataset_ids=[1407, 999], project_id=100)
