"""Unit tests for webhook models and API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mammoth.api.webhooks import WebhooksAPI
from mammoth.models.webhooks import WebhookCreate, WebhookInfo, WebhookMode

# ---------------------------------------------------------------------------
# WebhookMode enum
# ---------------------------------------------------------------------------


class TestWebhookMode:
    def test_values(self):
        assert WebhookMode.REPLACE == "replace"
        assert WebhookMode.COMBINE == "combine"

    def test_string_serialisation(self):
        assert str(WebhookMode.REPLACE) == "WebhookMode.REPLACE"
        assert WebhookMode.REPLACE.value == "replace"

    def test_from_string(self):
        assert WebhookMode("replace") is WebhookMode.REPLACE
        assert WebhookMode("combine") is WebhookMode.COMBINE


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TestWebhookModels:
    def test_webhook_info_defaults(self):
        info = WebhookInfo()
        assert info.id is None
        assert info.name is None
        assert info.mode is None
        assert info.uri is None
        assert info.ds_id is None
        assert info.origins is None
        assert info.secret is None

    def test_webhook_info_from_api(self):
        data = {
            "id": 8,
            "name": "test",
            "mode": "replace",
            "uri": "/webhook/data/nHC1zIl97JzgDMopgcfpOgLV",
            "ds_id": 535,
            "origins": "*",
            "secret": "V36QXDxGiwSa",
        }
        info = WebhookInfo(**data)
        assert info.id == 8
        assert info.name == "test"
        assert info.mode == "replace"
        assert info.uri == "/webhook/data/nHC1zIl97JzgDMopgcfpOgLV"
        assert info.ds_id == 535
        assert info.origins == "*"
        assert info.secret == "V36QXDxGiwSa"

    def test_webhook_info_extra_fields(self):
        info = WebhookInfo(id=1, future_field="hello")
        assert info.id == 1
        assert info.future_field == "hello"  # type: ignore[attr-defined]

    def test_webhook_create_defaults(self):
        spec = WebhookCreate()
        assert spec.name == "Generic Webhook"
        assert spec.mode == WebhookMode.REPLACE
        assert spec.folder_resource_id is None
        assert spec.origins == "*"
        assert spec.is_secure is False

    def test_webhook_create_custom(self):
        spec = WebhookCreate(
            name="My Webhook",
            mode=WebhookMode.COMBINE,
            folder_resource_id="label_42",
            origins="https://example.com",
            is_secure=True,
        )
        assert spec.name == "My Webhook"
        assert spec.mode == WebhookMode.COMBINE
        assert spec.folder_resource_id == "label_42"
        assert spec.origins == "https://example.com"
        assert spec.is_secure is True


# ---------------------------------------------------------------------------
# WebhooksAPI
# ---------------------------------------------------------------------------


def _make_api() -> tuple[WebhooksAPI, MagicMock]:
    """Create a WebhooksAPI with a mocked client."""
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = WebhooksAPI(mock_client)
    return api, mock_client


class TestWebhooksAPIList:
    def test_list_default_params(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"webhooks": []}
        result = api.list()
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/webhooks",
            params={"limit": 50, "offset": 0},
        )
        assert result == []

    def test_list_custom_params(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"webhooks": [{"id": 1}]}
        result = api.list(limit=10, offset=5)
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/webhooks",
            params={"limit": 10, "offset": 5},
        )
        assert result == [{"id": 1}]

    def test_list_fallback_response_format(self):
        api, mock_client = _make_api()
        # If response has no "webhooks" key and is a dict
        mock_client._request_json.return_value = {"something": "else"}
        result = api.list()
        assert result == []


class TestWebhooksAPICreate:
    def test_create_defaults(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 1}
        api.create()
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/workspaces/2/projects/100/webhooks",
            json={
                "name": "Generic Webhook",
                "mode": "replace",
                "origins": "*",
                "is_secure": False,
            },
        )

    def test_create_with_enum(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 2}
        api.create(name="Test", mode=WebhookMode.COMBINE, is_secure=True)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["name"] == "Test"
        assert call_json["mode"] == "combine"
        assert call_json["is_secure"] is True

    def test_create_with_folder(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 3}
        api.create(folder_resource_id="label_42")
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json["folder_resource_id"] == "label_42"

    def test_create_without_folder_omits_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 4}
        api.create()
        call_json = mock_client._request_json.call_args[1]["json"]
        assert "folder_resource_id" not in call_json


class TestWebhooksAPIUpdate:
    def test_update_mode(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update(5, mode=WebhookMode.COMBINE)
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            "/workspaces/2/projects/100/webhooks/5",
            json={"patch": [{"op": "replace", "path": "mode", "value": "combine"}]},
        )

    def test_update_multiple_fields(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update(5, mode="replace", origins="https://example.com", is_secure=True)
        call_json = mock_client._request_json.call_args[1]["json"]
        patch = call_json["patch"]
        assert len(patch) == 3
        paths = {p["path"] for p in patch}
        assert paths == {"mode", "origins", "is_secure"}

    def test_update_no_fields_sends_empty_patch(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update(5)
        call_json = mock_client._request_json.call_args[1]["json"]
        assert call_json == {"patch": []}


class TestWebhooksAPISendData:
    def test_send_data_post(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"status": "ok"}
        result = api.send_data("nHC1zIl97J", {"col1": "val1"})
        mock_client._request_json.assert_called_once_with(
            "POST",
            "/webhooks/data/nHC1zIl97J",
            json={"col1": "val1"},
        )
        assert result == {"status": "ok"}

    def test_send_data_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"status": "ok"}
        result = api.send_data_get("nHC1zIl97J", params={"col1": "val1"})
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/webhooks/data/nHC1zIl97J",
            params={"col1": "val1"},
        )
        assert result == {"status": "ok"}

    def test_send_data_no_project_prefix(self):
        """send_data should NOT include workspace/project in the path."""
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.send_data("abc123", {"key": "val"})
        path = mock_client._request_json.call_args[0][1]
        assert path == "/webhooks/data/abc123"
        assert "/workspaces/" not in path


class TestWebhooksAPIGet:
    def test_get(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 5, "name": "test"}
        result = api.get(5)
        mock_client._request_json.assert_called_once_with(
            "GET",
            "/workspaces/2/projects/100/webhooks/5",
        )
        assert result["id"] == 5


class TestWebhooksAPIDelete:
    def test_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete(5)
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            "/workspaces/2/projects/100/webhooks/5",
        )


class TestWebhooksAPIProjectRequired:
    def test_list_requires_project(self):
        mock_client = MagicMock()
        mock_client.workspace_id = 2
        mock_client.project_id = None
        api = WebhooksAPI(mock_client)
        with pytest.raises(ValueError, match="project_id must be set"):
            api.list()
