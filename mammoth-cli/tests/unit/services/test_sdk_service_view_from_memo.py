"""A write's View is built from the view metadata read ahead of it, not fetched again."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.sdk_service import SdkMammothService

AUTH = ResolvedAuth(
    api_key="key",
    api_secret="secret",
    workspace_id=4,
    base_url="https://unused.invalid/api/v2",
)
READ = "mammoth.api.dataviews.DataviewsAPI.get"
METADATA = {
    "id": 2,
    "name": "v",
    "metadata": [{"display_name": "sales", "internal_name": "column_2", "type": "NUMERIC"}],
}


@pytest.fixture
def service() -> Iterator[SdkMammothService]:
    instance = SdkMammothService(AUTH)
    instance._client.set_project_id(9)
    try:
        yield instance
    finally:
        instance.close()


def _fetches(service: SdkMammothService, monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    fetched: list[Any] = []

    async def get(view_id: int, dataset_id: int | None = None) -> Any:
        from mammoth.view import View

        fetched.append((view_id, dataset_id))
        return View(service._client, {**METADATA, "name": "fetched"}, dataset_id or 0)

    monkeypatch.setattr(service._client.views, "get", get)
    return fetched


def test_the_view_comes_from_the_read_made_ahead(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetched = _fetches(service, monkeypatch)
    service.memo.store(READ, {"dataset_id": 1, "dataview_id": 2, "project_id": 9}, METADATA)

    assert service.call_view(2, "name", dataset_id=1) == "v"
    assert service.call_view(2, "display_names", dataset_id=1) == ["sales"]
    # Only the first write found the read; the write cleared it, so the second fetched.
    assert fetched == [(2, 1)]


def test_without_a_read_ahead_the_view_is_fetched(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetched = _fetches(service, monkeypatch)
    service.memo.store(READ, {"dataset_id": 1, "dataview_id": 3}, METADATA)  # another view

    assert service.call_view(2, "name", dataset_id=1) == "fetched"
    assert fetched == [(2, 1)]
