"""Offline SDK contract tests for dashboard collections (mvc ``apiv2/collections``)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def _api(answer: object = None) -> tuple[DashboardsAPI, MagicMock]:
    client = MagicMock()
    client._request_json = AsyncMock(return_value=answer)
    return DashboardsAPI(client), client


async def test_list_collections_reads_the_top_level_route() -> None:
    api, client = _api({"collections": []})
    assert await api.list_collections() == {"collections": []}
    client._request_json.assert_called_once_with("GET", "/collections")


async def test_list_collections_for_a_dashboard_reads_the_holding_collections() -> None:
    api, client = _api({"collections": []})
    await api.list_collections(dashboard_id=42)
    client._request_json.assert_called_once_with("GET", "/collections/for-dashboard/42")


async def test_get_collection_reads_one() -> None:
    api, client = _api({"id": 9, "dashboards": []})
    await api.get_collection(9)
    client._request_json.assert_called_once_with("GET", "/collections/9")


async def test_create_collection_posts_the_project_name_and_dashboards() -> None:
    api, client = _api({"id": 9})
    await api.create_collection(" QA collection ", 180, dashboard_ids=[42, 43])
    client._request_json.assert_called_once_with(
        "POST",
        "/collections",
        json={
            "project_id": 180,
            "name": "QA collection",
            "description": None,
            "dashboard_ids": [42, 43],
        },
    )


async def test_create_collection_may_start_empty() -> None:
    api, client = _api({"id": 9})
    await api.create_collection("QA collection", 180)
    assert client._request_json.call_args.kwargs["json"]["dashboard_ids"] == []


@pytest.mark.parametrize(
    ("name", "project_id", "dashboard_ids"),
    [("  ", 180, None), ("QA", 0, None), ("QA", True, None), ("QA", 180, [0]), ("QA", 180, "42")],
)
async def test_create_collection_refuses_bad_input_without_request(
    name: str, project_id: object, dashboard_ids: object
) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        await api.create_collection(name, project_id, dashboard_ids=dashboard_ids)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


async def test_update_collection_sends_only_the_given_fields() -> None:
    api, client = _api({"id": 9})
    await api.update_collection(9, name="Board pack", order=[43, 42])
    client._request_json.assert_called_once_with(
        "PATCH", "/collections/9", json={"name": "Board pack", "order": [43, 42]}
    )


async def test_update_collection_refuses_an_empty_change_without_request() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="at least one"):
        await api.update_collection(9)
    client._request_json.assert_not_called()


async def test_delete_collection_deletes_by_id() -> None:
    api, client = _api(None)
    await api.delete_collection(9)
    client._request_json.assert_called_once_with("DELETE", "/collections/9")


async def test_add_to_collection_never_emails_members() -> None:
    api, client = _api({"added": [42], "notified": 0})
    assert await api.add_to_collection(9, [42]) == {"added": [42], "notified": 0}
    client._request_json.assert_called_once_with(
        "POST", "/collections/9/dashboards", json={"dashboard_ids": [42], "notify": False}
    )


@pytest.mark.parametrize("dashboard_ids", [[], [0], [True], "42", None])
async def test_add_to_collection_refuses_bad_ids_without_request(dashboard_ids: object) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError):
        await api.add_to_collection(9, dashboard_ids)  # type: ignore[arg-type]
    client._request_json.assert_not_called()


async def test_remove_from_collection_deletes_the_link() -> None:
    api, client = _api(None)
    await api.remove_from_collection(9, 42)
    client._request_json.assert_called_once_with("DELETE", "/collections/9/dashboards/42")


@pytest.mark.parametrize(("collection_id", "dashboard_id"), [(0, 42), (9, 0), (True, 42)])
async def test_remove_from_collection_refuses_bad_ids_without_request(
    collection_id: object, dashboard_id: object
) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="positive"):
        await api.remove_from_collection(collection_id, dashboard_id)  # type: ignore[arg-type]
    client._request_json.assert_not_called()
