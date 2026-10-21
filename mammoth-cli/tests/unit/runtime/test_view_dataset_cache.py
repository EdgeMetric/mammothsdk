"""The on-disk view -> dataset cache and the SDK hook that uses it."""

from __future__ import annotations

import asyncio
import json
import stat
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from mammoth.api.pipeline import PipelineAPI

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.runtime import view_dataset_cache as vdc


def _auth(token: str = "mm_a") -> ResolvedAuth:
    return ResolvedAuth(None, None, 7, "https://x.example", api_token=token)


@pytest.fixture
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(vdc, "cache_dir", lambda: tmp_path)
    monkeypatch.delenv(vdc.VIEW_DATASET_CACHE_ENV, raising=False)
    return tmp_path


def test_store_round_trips_with_owner_only_file(cache: Path) -> None:
    store = vdc.store_for(_auth(), "p")
    assert store is not None
    assert store.get(7, 1, 290) is None
    store.put(7, 1, 290, 424)
    again = vdc.store_for(_auth(), "p")
    assert again is not None
    assert again.get(7, 1, 290) == 424
    (file,) = cache.glob("view-datasets-*.json")
    assert stat.S_IMODE(file.stat().st_mode) == 0o600
    assert not list(cache.glob("*.tmp"))


def test_tokens_never_share_entries(cache: Path) -> None:
    a, b = vdc.store_for(_auth("mm_a"), "p"), vdc.store_for(_auth("mm_b"), "p")
    assert a is not None
    assert b is not None
    a.put(7, 1, 290, 424)
    assert b.get(7, 1, 290) is None
    assert len(list(cache.glob("view-datasets-*.json"))) == 1


def test_drop_forgets_and_forget_clears(cache: Path) -> None:
    store = vdc.store_for(_auth(), None)
    assert store is not None
    store.put(7, 1, 1, 2)
    store.put(7, 1, 3, 4)
    store.drop(7, 1, 1)
    fresh = vdc.store_for(_auth(), None)
    assert fresh is not None
    assert fresh.get(7, 1, 1) is None
    assert fresh.get(7, 1, 3) == 4
    vdc.forget_view_datasets()
    assert not list(cache.glob("view-datasets-*.json"))


@pytest.mark.parametrize("value", ["0", "false", "no", "OFF"])
def test_env_opt_out(cache: Path, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(vdc.VIEW_DATASET_CACHE_ENV, value)
    assert vdc.store_for(_auth(), None) is None


def test_forwarded_headers_have_no_cache(cache: Path) -> None:
    auth = ResolvedAuth(None, None, 7, "https://x.example", api_token="mm_a", headers={"A": "b"})
    assert vdc.store_for(auth, None) is None


def test_corrupt_file_reads_as_empty(cache: Path) -> None:
    store = vdc.store_for(_auth(), None)
    assert store is not None
    store.put(7, 1, 1, 2)
    (file,) = cache.glob("view-datasets-*.json")
    file.write_text("{not json", encoding="utf-8")
    fresh = vdc.store_for(_auth(), None)
    assert fresh is not None
    assert fresh.get(7, 1, 1) is None


def test_entries_are_capped(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vdc, "MAX_ENTRIES", 3)
    store = vdc.store_for(_auth(), None)
    assert store is not None
    for n in range(1, 6):
        store.put(7, 1, n, n + 100)
    (file,) = cache.glob("view-datasets-*.json")
    assert list(json.loads(file.read_text())["entries"]) == ["1:3", "1:4", "1:5"]


class _Browse:
    def __init__(self) -> None:
        self.calls = 0

    async def resource_get(self, kind: str, rid: int, **_: Any) -> dict[str, Any]:
        self.calls += 1
        return {"resource": {"dataset": {"id": 424}}}


def _pipeline(store: Any) -> tuple[PipelineAPI, _Browse]:
    browse = _Browse()
    client = SimpleNamespace(
        browse=browse, workspace_id=7, project_id=1, dataview_dataset_store=store
    )
    api = PipelineAPI.__new__(PipelineAPI)
    api._client = client  # type: ignore[assignment]
    api._dataview_dataset_cache = {}
    api._stored_resolutions = set()
    return api, browse


def test_sdk_uses_store_then_forgets(cache: Path) -> None:
    api, browse = _pipeline(vdc.store_for(_auth(), None))
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    assert browse.calls == 1
    # A second process: memory is empty, the disk answers.
    api2, browse2 = _pipeline(vdc.store_for(_auth(), None))
    assert asyncio.run(api2._find_dataset_for_dataview(290)) == 424
    assert browse2.calls == 0
    assert api2.stored_dataview_resolutions() == frozenset({290})
    api2.forget_dataview_dataset(290)
    assert api2.stored_dataview_resolutions() == frozenset()
    assert asyncio.run(api2._find_dataset_for_dataview(290)) == 424
    assert browse2.calls == 1


def test_failing_store_is_an_empty_store() -> None:
    class Broken:
        def get(self, *a: int) -> int:
            raise OSError

        def put(self, *a: int) -> None:
            raise OSError

        def drop(self, *a: int) -> None:
            raise OSError

    api, _ = _pipeline(Broken())
    assert asyncio.run(api._find_dataset_for_dataview(290)) == 424
    api.forget_dataview_dataset(290)
