"""ETag'd bodies kept on disk between commands, one directory per credential."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest
from mammoth.etag import CachedResponse

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.runtime import embedded, etag_store
from mammoth_cli.runtime.embed_pool import EmbedRuntime
from mammoth_cli.runtime.etag_store import DiskETagStore

URL = "https://app.example/api/v2/workspaces/2/projects?limit=100"


def _body(tag: str = 'W/"v1"') -> CachedResponse:
    return CachedResponse(
        etag=tag, content=b'{"projects": []}', headers={"content-type": "application/json"}
    )


def test_a_kept_body_reads_back_owner_only(tmp_path: Path) -> None:
    store = DiskETagStore(tmp_path / "etags-x")
    assert store.get(URL) is None
    store.put(URL, _body())
    assert store.get(URL) == _body()
    (kept,) = (tmp_path / "etags-x").glob("*.etag")
    assert stat.S_IMODE(kept.stat().st_mode) == 0o600


def test_a_new_body_replaces_the_old_and_clear_drops_all(tmp_path: Path) -> None:
    store = DiskETagStore(tmp_path / "etags-x")
    store.put(URL, _body())
    store.put(URL, _body('W/"v2"'))
    found = store.get(URL)
    assert found is not None and found.etag == 'W/"v2"'
    store.clear()
    assert store.get(URL) is None


def test_a_damaged_file_reads_as_nothing(tmp_path: Path) -> None:
    store = DiskETagStore(tmp_path / "etags-x")
    store.put(URL, _body())
    (kept,) = (tmp_path / "etags-x").glob("*.etag")
    kept.write_bytes(b"not json\n{}")
    assert store.get(URL) is None


def test_the_oldest_files_go_past_the_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(etag_store, "MAX_ENTRIES", 2)
    store = DiskETagStore(tmp_path / "etags-x")
    for page in range(3):
        store.put(f"{URL}&offset={page}", _body())
    assert len(list((tmp_path / "etags-x").glob("*.etag"))) == 2


def test_store_for_is_per_credential_and_can_be_switched_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(etag_store, "cache_dir", lambda: tmp_path)
    first = ResolvedAuth(None, None, 2, "https://app.example/api/v2", api_token="mm_one")
    second = ResolvedAuth(None, None, 2, "https://app.example/api/v2", api_token="mm_two")
    one, two = etag_store.store_for(first, "p"), etag_store.store_for(second, "p")
    assert one is not None and two is not None
    one.put(URL, _body())
    assert two.get(URL) is None
    etag_store.forget_etags()
    assert one.get(URL) is None
    monkeypatch.setenv(etag_store.ETAG_CACHE_ENV, "off")
    assert etag_store.store_for(first, "p") is None


def test_caller_scope_names_the_credential_not_the_run() -> None:
    def auth(**headers: str) -> ResolvedAuth:
        return ResolvedAuth(None, None, 2, "https://app.example/api/v2", headers=headers)

    alice = etag_store.caller_scope(auth(Cookie="session=a", **{"X-Mammoth-Agent-Run": "r1"}))
    again = etag_store.caller_scope(auth(Cookie="session=a", **{"X-Mammoth-Agent-Run": "r2"}))
    bob = etag_store.caller_scope(auth(Cookie="session=b"))
    assert alice is not None and alice == again and alice != bob
    assert etag_store.caller_scope(auth(**{"X-Mammoth-Agent-Run": "r1"})) is None
    token = ResolvedAuth(None, None, 2, "https://app.example/api/v2", api_token="mm_x")
    assert etag_store.caller_scope(token) is not None


def test_an_embedded_call_uses_its_scope_of_the_runtime_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(embedded, "active", lambda: True)
    runtime = EmbedRuntime()
    try:
        alice = ResolvedAuth(None, None, 2, "https://app.example/api/v2", api_token="mm_a")
        bob = ResolvedAuth(None, None, 2, "https://app.example/api/v2", api_token="mm_b")
        first, second = (etag_store.cache_for(a, None, runtime) for a in (alice, bob))
        assert first is not None and second is not None
        first.put(URL, _body())
        assert second.get(URL) is None
        again = etag_store.cache_for(alice, None, runtime)
        assert again is not None and again.get(URL) == _body()
        assert etag_store.cache_for(alice, None, None) is None
    finally:
        runtime.close()
