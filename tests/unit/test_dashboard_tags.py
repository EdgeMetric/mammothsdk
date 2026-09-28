"""Offline SDK contract tests for the approved dashboard-tag subset."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def _api() -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    return DashboardsAPI(client), client


async def test_list_tags_uses_release_route() -> None:
    api, client = _api()
    client._request_json = AsyncMock(return_value={"tags": [{"id": 7, "name": "Revenue"}]})
    assert await api.list_tags() == {"tags": [{"id": 7, "name": "Revenue"}]}
    client._request_json.assert_called_once_with("GET", "/dashboards/tags")


async def test_rename_tag_uses_release_body_and_route() -> None:
    api, client = _api()
    client._request_json = AsyncMock(return_value={"id": 7, "name": "Sales"})
    await api.rename_tag(7, "Sales")
    client._request_json.assert_called_once_with(
        "PATCH", "/dashboards/tags/7", json={"name": "Sales"}
    )


@pytest.mark.parametrize("tag_id", [0, -1, True, "7"])
async def test_rename_tag_rejects_invalid_id_without_request(tag_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        await api.rename_tag(tag_id, {"name": "Sales"})
    client._request_json.assert_not_called()


async def test_rename_tag_rejects_blank_name_without_request() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="non-blank"):
        await api.rename_tag(7, "  ")
    client._request_json.assert_not_called()


async def test_set_tags_uses_release_body_and_allows_empty_list() -> None:
    api, client = _api()
    client._request_json = AsyncMock(return_value={"id": 7, "tags": []})
    await api.set_tags(7, [])
    client._request_json.assert_called_once_with("PUT", "/dashboards/7/tags", json={"tags": []})


@pytest.mark.parametrize("dashboard_id", [0, -1, True, "7"])
async def test_set_tags_rejects_invalid_id_without_request(dashboard_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        await api.set_tags(dashboard_id, ["Revenue"])
    client._request_json.assert_not_called()


async def test_set_tags_rejects_a_tag_that_is_not_a_name_without_request() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        await api.set_tags(7, ["Revenue", 7])  # type: ignore[list-item]
    client._request_json.assert_not_called()


async def test_set_tags_passes_a_repeated_tag_to_the_route() -> None:
    # The route files the dashboard under each name it is given and is
    # idempotent about it, so a repeat is its business, not the SDK's.
    api, client = _api()
    client._request_json = AsyncMock(return_value={"id": 7, "tags": ["Revenue"]})

    await api.set_tags(7, ["Revenue", "Revenue"])

    client._request_json.assert_called_once_with(
        "PUT", "/dashboards/7/tags", json={"tags": ["Revenue", "Revenue"]}
    )


async def test_delete_tag_uses_release_route() -> None:
    api, client = _api()
    client._request_json = AsyncMock(return_value=None)
    assert await api.delete_tag(7) is None
    client._request_json.assert_called_once_with("DELETE", "/dashboards/tags/7")


@pytest.mark.parametrize("tag_id", [0, -1, True, "7"])
async def test_delete_tag_rejects_invalid_id_without_request(tag_id: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        await api.delete_tag(tag_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


async def test_merge_tag_uses_release_route_and_body() -> None:
    api, client = _api()
    client._request_json = AsyncMock(return_value={"id": 456})
    await api.merge_tag(123, 456)
    client._request_json.assert_called_once_with(
        "POST", "/dashboards/tags/123/merge", json={"target_id": 456}
    )


@pytest.mark.parametrize("source, target", [(0, 456), (123, 0), (123, 123), (True, 456)])
async def test_merge_tag_rejects_invalid_ids_without_request(source: object, target: int) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        await api.merge_tag(source, target)  # type: ignore[arg-type]
    client._request_json.assert_not_called()
