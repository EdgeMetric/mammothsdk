"""Unit tests for the ConnectorsAPI client.

The server decodes every ``{connector_key}`` path segment under
``/workspaces/{ws}/connectors/...`` as standard base64 (see
``apiv2/apiv2/common/utils.py::decode_connector_key`` in mvc-service), matching
the web app's ``btoa(key)`` encoding (``mm-frontend/src/constants/connectors.js``).
The SDK must send the base64-encoded key on the wire while callers keep
passing the plain ``name_key`` (e.g. ``"bigquery"``, as returned by
``connector list``).
"""

from __future__ import annotations

import base64
from unittest.mock import MagicMock

from mammoth.api.connectors import ConnectorsAPI


def _b64(key: str) -> str:
    return base64.b64encode(key.encode("utf-8")).decode("ascii")


def _make_api() -> tuple[ConnectorsAPI, MagicMock]:
    mock_client = MagicMock()
    mock_client.workspace_id = 2
    mock_client.project_id = 100
    api = ConnectorsAPI(mock_client)
    return api, mock_client


class TestConnectorsAPIGet:
    def test_get_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"name_key": "bigquery"}
        api.get("bigquery")
        mock_client._request_json.assert_called_once_with(
            "GET", f"/workspaces/2/connectors/{_b64('bigquery')}"
        )

    def test_get_returns_response(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"name_key": "bigquery"}
        assert api.get("bigquery") == {"name_key": "bigquery"}


class TestConnectorsAPIListConnections:
    def test_list_connections_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request.return_value = []
        api.list_connections("postgres")
        mock_client._request.assert_called_once_with(
            "GET",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}/connections",
        )


class TestConnectorsAPICreateConnection:
    def test_create_connection_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"connection_key": "c1"}
        api.create_connection("postgres", config={"hostname": "h"})
        mock_client._request_json.assert_called_once_with(
            "POST",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}/connections",
            json={"hostname": "h"},
        )


class TestConnectorsAPIGetConnection:
    def test_get_connection_encodes_connector_key_not_connection_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.get_connection("postgres", "conn_key")
        mock_client._request_json.assert_called_once_with(
            "GET",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}/connections/conn_key",
        )


class TestConnectorsAPIUpdateConnection:
    def test_update_connection_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.update_connection("postgres", "conn_key", credentials={"password": "x"})
        mock_client._request_json.assert_called_once_with(
            "PATCH",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}/connections/conn_key",
            json={"patch": [{"op": "replace", "path": "connection", "value": {"password": "x"}}]},
        )


class TestConnectorsAPIDeleteConnection:
    def test_delete_connection_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete_connection("postgres", "conn_key")
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}/connections/conn_key",
        )


class TestConnectorsAPIDsConfigs:
    def test_list_ds_configs_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request.return_value = []
        api.list_ds_configs("postgres", "conn_key")
        mock_client._request.assert_called_once_with(
            "GET",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}"
            "/connections/conn_key/ds_configs",
        )

    def test_create_ds_config_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.create_ds_config("postgres", "conn_key", query="select 1")
        mock_client._request_json.assert_called_once_with(
            "POST",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}"
            "/connections/conn_key/ds_configs",
            json={"validate": True, "data_sample": False, "query": "select 1"},
        )

    def test_get_ds_config_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.get_ds_config("postgres", "conn_key", "ds1")
        mock_client._request_json.assert_called_once_with(
            "GET",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}"
            "/connections/conn_key/ds_configs/ds1",
        )

    def test_delete_ds_config_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete_ds_config("postgres", "conn_key", "ds1")
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}"
            "/connections/conn_key/ds_configs/ds1",
        )

    def test_ds_config_delete_all_encodes_connector_key(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.ds_config_delete_all("postgres", "conn_key", ["ds1", "ds2"])
        mock_client._request_json.assert_called_once_with(
            "DELETE",
            f"/workspaces/2/projects/100/connectors/{_b64('postgres')}"
            "/connections/conn_key/ds_configs",
            params={"config_ids": "ds1,ds2"},
        )


class TestConnectorsAPIUnaffectedRoutes:
    """Routes with no ``{connector_key}`` path segment must stay untouched."""

    def test_list_is_not_encoded(self):
        api, mock_client = _make_api()
        mock_client._request.return_value = []
        api.list()
        mock_client._request.assert_called_once_with("GET", "/workspaces/2/connectors")

    def test_active_connectors_is_not_encoded(self):
        api, mock_client = _make_api()
        mock_client._request.return_value = []
        api.active_connectors()
        mock_client._request.assert_called_once_with("GET", "/workspaces/2/active_connectors")
