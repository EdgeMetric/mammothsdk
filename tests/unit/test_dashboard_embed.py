"""Offline contract tests for the dashboard embed SDK bindings (CLI GAP)."""

from unittest.mock import MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    return DashboardsAPI(client), client


def test_embed_config_get_reads_settings() -> None:
    api, client = _api()
    client._request_json.return_value = {
        "mode": "key",
        "allowed_origins": [],
        "appearance": {},
        "embed_url": "https://app.mammoth.io/api/v3/embed/abc",
        "sdk_url": "https://app.mammoth.io/embed-assets/sdk.v1.js",
        "published": True,
        "public": False,
        "access_key": "k_123",
    }
    result = api.embed_config_get(7)
    assert result.mode == "key"
    assert result.access_key == "k_123"
    client._request_json.assert_called_once_with("GET", "/dashboards/7/embed/config")


@pytest.mark.parametrize("dashboard_id", [0, -1, True])
def test_embed_config_get_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.embed_config_get(dashboard_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_config_set_puts_exact_wire_shape() -> None:
    api, client = _api()
    client._request_json.return_value = {
        "mode": "signed",
        "allowed_origins": ["https://intranet.example.com"],
        "appearance": {},
        "embed_url": "https://app.mammoth.io/api/v3/embed/abc",
        "sdk_url": "https://app.mammoth.io/embed-assets/sdk.v1.js",
        "published": True,
        "public": False,
    }
    result = api.embed_config_set(
        7,
        mode="signed",
        allow_any_origin=False,
        allowed_origins=["https://intranet.example.com"],
    )
    assert result.allowed_origins == ["https://intranet.example.com"]
    client._request_json.assert_called_once_with(
        "PUT",
        "/dashboards/7/embed/config",
        json={
            "params": {
                "mode": "signed",
                "allow_any_origin": False,
                "allowed_origins": ["https://intranet.example.com"],
                "appearance": {},
                "snippet": {},
            }
        },
    )


@pytest.mark.parametrize("dashboard_id", [0, -1, True])
def test_embed_config_set_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.embed_config_set(dashboard_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_config_set_rejects_too_many_origins() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        api.embed_config_set(7, allowed_origins=[f"https://s{i}.example.com" for i in range(21)])
    client._request_json.assert_not_called()


def test_embed_key_rotate_posts_keep_previous_default() -> None:
    api, client = _api()
    client._request_json.return_value = {"key": "k_new", "rotated_at": "2026-09-26T00:00:00Z"}
    result = api.embed_key_rotate(7)
    assert result.key == "k_new"
    client._request_json.assert_called_once_with(
        "POST", "/dashboards/7/embed/key", json={"params": {"keep_previous": True}}
    )


def test_embed_key_rotate_forwards_keep_previous_false() -> None:
    api, client = _api()
    client._request_json.return_value = {"key": "k_new"}
    api.embed_key_rotate(7, keep_previous=False)
    client._request_json.assert_called_once_with(
        "POST", "/dashboards/7/embed/key", json={"params": {"keep_previous": False}}
    )


@pytest.mark.parametrize("dashboard_id", [0, -1, True])
def test_embed_key_rotate_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.embed_key_rotate(dashboard_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_usage_get_reads_registry() -> None:
    api, client = _api()
    client._request_json.return_value = {"origins": [], "active_origins": 0}
    result = api.embed_usage_get(7)
    assert result.active_origins == 0
    client._request_json.assert_called_once_with("GET", "/dashboards/7/embed/usage")


@pytest.mark.parametrize("dashboard_id", [0, -1, True])
def test_embed_usage_get_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.embed_usage_get(dashboard_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_origin_revoke_deletes_with_origin_body() -> None:
    api, client = _api()
    client._request_json.return_value = {
        "mode": "key",
        "allowed_origins": [],
        "appearance": {},
        "embed_url": "https://app.mammoth.io/api/v3/embed/abc",
        "sdk_url": "https://app.mammoth.io/embed-assets/sdk.v1.js",
        "published": True,
        "public": False,
    }
    api.embed_origin_revoke(7, "https://old.example.com")
    client._request_json.assert_called_once_with(
        "DELETE",
        "/dashboards/7/embed/origin",
        json={"params": {"origin": "https://old.example.com"}},
    )


@pytest.mark.parametrize("dashboard_id", [0, -1, True])
def test_embed_origin_revoke_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.embed_origin_revoke(dashboard_id, "https://old.example.com")  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_origin_revoke_rejects_empty_origin() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="origin"):
        api.embed_origin_revoke(7, "")
    client._request_json.assert_not_called()


def test_embed_preview_token_create_mints_token() -> None:
    api, client = _api()
    client._request_json.return_value = {
        "token": "t_abc",
        "expires_at": 1234567890,
        "embed_url": "https://app.mammoth.io/api/v3/embed/abc",
    }
    result = api.embed_preview_token_create(7, claims={"region": ["East"]})
    assert result.token == "t_abc"
    client._request_json.assert_called_once_with(
        "POST",
        "/dashboards/7/embed/preview-token",
        json={"params": {"claims": {"region": ["East"]}}},
    )


@pytest.mark.parametrize("dashboard_id", [0, -1, True])
def test_embed_preview_token_create_rejects_invalid_dashboard_id(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="dashboard_id"):
        api.embed_preview_token_create(dashboard_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_secret_rotate_posts_workspace_secret() -> None:
    api, client = _api()
    client._request_json.return_value = {"secret": "s_abc", "token_ttl": 300, "rotated_at": None}
    result = api.embed_secret_rotate(3)
    assert result.secret == "s_abc"
    client._request_json.assert_called_once_with("POST", "/workspaces/3/embed/secret")


@pytest.mark.parametrize("workspace_id", [0, -1, True])
def test_embed_secret_rotate_rejects_invalid_workspace_id(workspace_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="workspace_id"):
        api.embed_secret_rotate(workspace_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_embed_lifetime_set_puts_token_ttl() -> None:
    api, client = _api()
    client._request_json.return_value = {"token_ttl": 900}
    result = api.embed_lifetime_set(3, 900)
    assert result.token_ttl == 900
    client._request_json.assert_called_once_with(
        "PUT", "/workspaces/3/embed/lifetime", json={"params": {"token_ttl": 900}}
    )


@pytest.mark.parametrize("workspace_id", [0, -1, True])
def test_embed_lifetime_set_rejects_invalid_workspace_id(workspace_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="workspace_id"):
        api.embed_lifetime_set(workspace_id, 900)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


@pytest.mark.parametrize("token_ttl", [59, 3601, 0, -1])
def test_embed_lifetime_set_rejects_out_of_range_ttl(token_ttl: int) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="token_ttl"):
        api.embed_lifetime_set(3, token_ttl)
    client._request_json.assert_not_called()
