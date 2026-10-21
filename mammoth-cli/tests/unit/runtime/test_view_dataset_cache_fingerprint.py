"""The cache file is named by everything that decides what a credential may see."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.runtime import view_dataset_cache as vdc

BASE = ResolvedAuth(None, None, 7, "https://x.example", api_token="mm_a")


@pytest.fixture
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(vdc, "cache_dir", lambda: tmp_path)
    monkeypatch.delenv(vdc.VIEW_DATASET_CACHE_ENV, raising=False)
    return tmp_path


@pytest.mark.parametrize(
    "auth, profile",
    [
        (ResolvedAuth(None, None, 8, "https://x.example", api_token="mm_a"), "p"),
        (ResolvedAuth(None, None, 7, "https://y.example", api_token="mm_a"), "p"),
        (ResolvedAuth(None, None, 7, "https://x.example", api_token="mm_b"), "p"),
        (BASE, "q"),
    ],
    ids=["workspace", "server", "token", "profile"],
)
def test_credentials_differing_in_one_part_never_share_entries(
    cache: Path, auth: ResolvedAuth, profile: str
) -> None:
    first = vdc.store_for(BASE, "p")
    other = vdc.store_for(auth, profile)
    assert first is not None
    assert other is not None
    first.put(7, 1, 290, 424)
    assert other.get(auth.workspace_id, 1, 290) is None
    other.put(auth.workspace_id, 1, 290, 999)
    assert first.get(7, 1, 290) == 424
    assert len(list(cache.glob("view-datasets-*.json"))) == 2
