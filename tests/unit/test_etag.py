"""Reads that came with an ETag are revalidated with If-None-Match; a 304 reuses the body."""

from __future__ import annotations

import httpx

from mammoth import MammothClient
from mammoth.etag import CachedResponse, MemoryETagCache


class _Server:
    """A resource whose tag changes when ``change()`` is called; answers 304 on a match."""

    def __init__(self) -> None:
        self.version = 1
        self.seen: list[httpx.Request] = []

    def change(self) -> None:
        self.version += 1

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        if request.method != "GET":
            return httpx.Response(200, json={"ok": True})
        tag = f'W/"v{self.version}"'
        if request.headers.get("if-none-match") == tag:
            return httpx.Response(304, headers={"etag": tag})
        return httpx.Response(200, json={"version": self.version}, headers={"etag": tag})


def _client(server: _Server) -> tuple[MammothClient, httpx.AsyncClient]:
    shared = httpx.AsyncClient(transport=httpx.MockTransport(server))
    return MammothClient(api_token="mm_etag", workspace_id=7, http_client=shared), shared


class TestConditionalReads:
    async def test_second_read_sends_the_tag_and_a_304_returns_the_kept_body(self) -> None:
        server = _Server()
        client, shared = _client(server)
        assert await client.request_json("GET", "/projects") == {"version": 1}
        assert await client.request_json("GET", "/projects") == {"version": 1}
        assert "if-none-match" not in server.seen[0].headers
        assert server.seen[1].headers["if-none-match"] == 'W/"v1"'
        await shared.aclose()

    async def test_a_changed_resource_is_read_again(self) -> None:
        server = _Server()
        client, shared = _client(server)
        await client.request_json("GET", "/projects")
        server.change()
        assert await client.request_json("GET", "/projects") == {"version": 2}
        await shared.aclose()

    async def test_query_strings_are_kept_apart(self) -> None:
        server = _Server()
        client, shared = _client(server)
        await client.request_json("GET", "/projects", params={"offset": 0})
        await client.request_json("GET", "/projects", params={"offset": 100})
        assert "if-none-match" not in server.seen[1].headers
        await shared.aclose()

    async def test_a_write_forgets_every_kept_body(self) -> None:
        server = _Server()
        client, shared = _client(server)
        await client.request_json("GET", "/projects")
        await client.request_json("POST", "/projects", json={"name": "x"})
        await client.request_json("GET", "/projects")
        assert "if-none-match" not in server.seen[2].headers
        await shared.aclose()

    async def test_none_turns_conditional_reads_off(self) -> None:
        server = _Server()
        client, shared = _client(server)
        client.etag_cache = None
        await client.request_json("GET", "/projects")
        await client.request_json("GET", "/projects")
        assert "if-none-match" not in server.seen[1].headers
        await shared.aclose()

    async def test_a_response_without_a_tag_is_not_kept(self) -> None:
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json={"ok": True})

        shared = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        client = MammothClient(api_token="mm_etag", workspace_id=7, http_client=shared)
        await client.request_json("GET", "/jobs/1")
        await client.request_json("GET", "/jobs/1")
        assert "if-none-match" not in seen[1].headers
        await shared.aclose()


def test_memory_cache_drops_the_least_recently_used() -> None:
    cache = MemoryETagCache(max_entries=2)
    for key in ("a", "b"):
        cache.put(key, CachedResponse(etag=key, content=b"{}"))
    assert cache.get("a") is not None  # "a" is now the most recent
    cache.put("c", CachedResponse(etag="c", content=b"{}"))
    assert cache.get("b") is None
    assert cache.get("a") is not None and cache.get("c") is not None


def test_memory_cache_keeps_within_its_byte_budget() -> None:
    cache = MemoryETagCache(max_bytes=10)
    cache.put("a", CachedResponse(etag="a", content=b"123456"))
    cache.put("b", CachedResponse(etag="b", content=b"123456"))
    assert cache.get("a") is None and cache.get("b") is not None
    cache.put("c", CachedResponse(etag="c", content=b"x" * 11))
    assert cache.get("c") is None


def test_scopes_share_a_budget_but_never_bodies() -> None:
    shared = MemoryETagCache()
    alice, bob = shared.scoped("alice"), shared.scoped("bob")
    alice.put("/projects", CachedResponse(etag="t", content=b"alice's"))
    assert bob.get("/projects") is None
    bob.put("/projects", CachedResponse(etag="t", content=b"bob's"))
    alice.clear()
    assert alice.get("/projects") is None
    found = bob.get("/projects")
    assert found is not None and found.content == b"bob's"
