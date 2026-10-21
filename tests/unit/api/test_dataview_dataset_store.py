"""PipelineAPI consults ``client.dataview_dataset_store`` before asking the API."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from mammoth.api.pipeline import PipelineAPI


class _Browse:
    def __init__(self) -> None:
        self.calls = 0

    async def resource_get(self, kind: str, rid: int, **_: Any) -> dict[str, Any]:
        self.calls += 1
        return {"resource": {"dataset": {"id": 424}}}


class _Store:
    def __init__(self, known: dict[tuple[int, int, int], int] | None = None) -> None:
        self.known = dict(known or {})
        self.dropped: list[tuple[int, int, int]] = []

    def get(self, workspace_id: int, project_id: int, dataview_id: int) -> int | None:
        return self.known.get((workspace_id, project_id, dataview_id))

    def put(self, workspace_id: int, project_id: int, dataview_id: int, dataset_id: int) -> None:
        self.known[(workspace_id, project_id, dataview_id)] = dataset_id

    def drop(self, workspace_id: int, project_id: int, dataview_id: int) -> None:
        self.dropped.append((workspace_id, project_id, dataview_id))
        self.known.pop((workspace_id, project_id, dataview_id), None)


def _api(store: Any) -> tuple[PipelineAPI, _Browse]:
    browse = _Browse()
    client = SimpleNamespace(
        browse=browse, workspace_id=7, project_id=1, dataview_dataset_store=store
    )
    return PipelineAPI(client), browse  # type: ignore[arg-type]


def test_a_stored_answer_skips_the_lookup() -> None:
    api, browse = _api(_Store({(7, 1, 290): 424}))
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert browse.calls == 0
    assert api.stored_dataview_resolutions() == frozenset({290})


def test_an_api_answer_is_stored_and_not_marked_as_stored() -> None:
    store = _Store()
    api, browse = _api(store)
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert browse.calls == 1
    assert store.known == {(7, 1, 290): 424}
    assert api.stored_dataview_resolutions() == frozenset()


def test_forget_drops_memory_and_store() -> None:
    store = _Store({(7, 1, 290): 424})
    api, browse = _api(store)
    asyncio.run(api._find_dataset_for_dataview(290))
    api.forget_dataview_dataset(290)
    assert store.dropped == [(7, 1, 290)]
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert browse.calls == 1


def test_a_nonsense_stored_value_is_ignored() -> None:
    api, browse = _api(_Store({(7, 1, 290): -5}))
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert browse.calls == 1


def test_no_store_behaves_as_before() -> None:
    api, browse = _api(None)
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert browse.calls == 1
