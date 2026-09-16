"""Offline SDK contract tests for the approved dashboard-tag subset."""

from unittest.mock import MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    return DashboardsAPI(client), client


def test_list_tags_uses_release_route() -> None:
    api, client = _api()
    client._request_json.return_value = {"tags": [{"id": 7, "name": "Revenue"}]}
    assert api.list_tags() == {"tags": [{"id": 7, "name": "Revenue"}]}
    client._request_json.assert_called_once_with("GET", "/dashboards/tags")


def test_rename_tag_uses_release_body_and_route() -> None:
    api, client = _api()
    client._request_json.return_value = {"id": 7, "name": "Sales"}
    api.rename_tag(7, "Sales")
    client._request_json.assert_called_once_with(
        "PATCH", "/dashboards/tags/7", json={"name": "Sales"}
    )


@pytest.mark.parametrize("tag_id", [0, -1, True, "7"])
def test_rename_tag_rejects_invalid_id_without_request(tag_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        api.rename_tag(tag_id, {"name": "Sales"})
    client._request_json.assert_not_called()


def test_rename_tag_rejects_blank_name_without_request() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="non-blank"):
        api.rename_tag(7, "  ")
    client._request_json.assert_not_called()


def test_set_tags_uses_release_body_and_allows_empty_list() -> None:
    api, client = _api()
    client._request_json.return_value = {"id": 7, "tags": []}
    api.set_tags(7, [])
    client._request_json.assert_called_once_with(
        "PUT", "/dashboards/7/tags", json={"tags": []}
    )


@pytest.mark.parametrize("dashboard_id", [0, -1, True, "7"])
def test_set_tags_rejects_invalid_id_without_request(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        api.set_tags(dashboard_id, ["Revenue"])
    client._request_json.assert_not_called()


@pytest.mark.parametrize("tags", [["Revenue", "Revenue"], ["Revenue", 7]])
def test_set_tags_rejects_duplicate_or_invalid_values_without_request(tags: list[object]) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        api.set_tags(7, tags)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_delete_tag_uses_release_route() -> None:
    api, client = _api()
    client._request_json.return_value = None
    assert api.delete_tag(7) is None
    client._request_json.assert_called_once_with("DELETE", "/dashboards/tags/7")


@pytest.mark.parametrize("tag_id", [0, -1, True, "7"])
def test_delete_tag_rejects_invalid_id_without_request(tag_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        api.delete_tag(tag_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


def test_merge_tag_uses_release_route_and_body() -> None:
    api, client = _api()
    client._request_json.return_value = {"id": 456}
    api.merge_tag(123, 456)
    client._request_json.assert_called_once_with(
        "POST", "/dashboards/tags/123/merge", json={"target_id": 456}
    )


@pytest.mark.parametrize("source, target", [(0, 456), (123, 0), (123, 123), (True, 456)])
def test_merge_tag_rejects_invalid_ids_without_request(source: object, target: int) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        api.merge_tag(source, target)  # type: ignore[arg-type]
    client._request_json.assert_not_called()
