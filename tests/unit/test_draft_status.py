"""Unit tests for ``PipelineAPI.get_draft_status``.

Regression under test: the pinned OpenAPI spec (``mammoth-cli/spec/openapi/
openapi.json``, schema ``PipelineInfo``) defines the dataview pipeline field
``draft_mode`` as a top-level string enum ``["off", "clean", "dirty", null]``
on the ``GET .../pipeline`` response (the exact payload ``get_pipeline``
returns). "clean" or "dirty" mean the dataview IS in draft ("dirty" = there
are unsaved changes); "off" or null/absent mean it is NOT in draft.

Before the fix, ``get_draft_status`` only recognised ``draft_mode``/``draft``
when it was a dict (checking ``.active``/``.is_draft``) or read boolean
``is_draft``/``in_draft_mode`` fields. A server response with the string
enum ``draft_mode: "dirty"`` matched none of those branches, so
``is_draft`` was wrongly reported as ``False``.

These tests exercise the *real* ``PipelineAPI.get_pipeline`` and
``get_draft_status`` code paths end to end. Only the HTTP boundary
(``client._request_json``) is faked, following the same seam used by
``tests/unit/test_pipeline_versions.py`` for this API sub-client.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from mammoth.api.pipeline import PipelineAPI

WORKSPACE_ID = 2
PROJECT_ID = 100
DATASET_ID = 1
DATAVIEW_ID = 9


def _make_api() -> tuple[PipelineAPI, MagicMock]:
    """Build a real ``PipelineAPI`` bound to a mocked client transport.

    Returns:
        Tuple of (api, mock_client). ``mock_client._request_json`` is the
        only faked seam — ``get_pipeline``/``get_draft_status`` run for real.
    """
    mock_client = MagicMock()
    mock_client.workspace_id = WORKSPACE_ID
    mock_client.project_id = PROJECT_ID
    api = PipelineAPI(mock_client)
    return api, mock_client


class TestGetDraftStatusStringEnum:
    """Server returns ``draft_mode`` as the OpenAPI string enum."""

    def test_dirty_is_draft_true(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready", "draft_mode": "dirty"}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is True
        assert result["dataview_id"] == DATAVIEW_ID
        assert result["draft"] == "dirty"

    def test_clean_is_draft_true(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready", "draft_mode": "clean"}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is True
        assert result["draft"] == "clean"

    def test_off_is_draft_false(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready", "draft_mode": "off"}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is False
        assert result["draft"] == "off"

    def test_absent_is_draft_false(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready"}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is False
        assert result["draft"] is None

    def test_null_is_draft_false(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready", "draft_mode": None}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is False
        assert result["draft"] is None


class TestGetDraftStatusCompatibilityFallbacks:
    """Legacy/alternate shapes must keep working alongside the enum fix."""

    def test_dict_draft_section_active_true(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {
            "state": "ready",
            "draft": {"active": True},
        }

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is True
        assert result["draft"] == {"active": True}

    def test_dict_draft_section_is_draft_true(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {
            "state": "ready",
            "draft_mode": {"is_draft": True},
        }

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is True

    def test_bool_is_draft_true(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready", "is_draft": True}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is True

    def test_bool_in_draft_mode_true(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready", "in_draft_mode": True}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is True

    def test_no_draft_fields_is_draft_false(self) -> None:
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"state": "ready"}

        result = api.get_draft_status(DATAVIEW_ID, dataset_id=DATASET_ID)

        assert result["is_draft"] is False
        assert result["draft"] is None
