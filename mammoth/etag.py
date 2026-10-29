"""Conditional GETs: send back the ``ETag`` a read returned, reuse the body on a 304.

The API gives an ``ETag`` on the reads it can validate cheaply (workspaces, projects,
folders, datasets, views, browse and resource listings) and answers ``304 Not Modified``,
with no body, when the resource has not changed since. The server changes the tag on
every change event, a pipeline's status and row count included, so a 304 never hides
a change.

:class:`ETagCache` is the port: the client asks it for the tag and body of a URL it read
before, and gives it each new one. :class:`MemoryETagCache` keeps them for the life of
the client; a caller that runs many short processes (the CLI) can pass a store that
survives them.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Protocol

#: A body larger than this is not kept: a 304 for it would save less than it costs.
MAX_BODY_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class CachedResponse:
    """A body the server sent with an ``ETag``, kept to answer a later 304."""

    etag: str
    content: bytes
    #: The response headers worth replaying (``Content-Type``), by lower-case name.
    headers: dict[str, str] = field(default_factory=dict)


class ETagCache(Protocol):
    """Where a client keeps the bodies it can revalidate with ``If-None-Match``."""

    def get(self, key: str) -> CachedResponse | None:
        """Return the response kept for ``key``.

        Args:
            key: The full request URL, query string included.

        Returns:
            The kept response, or None when there is none.
        """

    def put(self, key: str, response: CachedResponse) -> None:
        """Keep ``response`` for ``key``, replacing any earlier one.

        Args:
            key: The full request URL, query string included.
            response: The tag and body to keep.
        """

    def clear(self) -> None:
        """Drop everything kept; the client calls it before each write it sends."""


class MemoryETagCache:
    """An :class:`ETagCache` in memory, bounded by entries and bytes, least recently used first.

    One cache may serve many callers through :meth:`scoped` views: a process that serves
    many users keeps one budget for all of them, and each user sees only their own bodies.

    Args:
        max_entries: How many bodies to keep.
        max_bytes: How many body bytes to keep in all.
    """

    def __init__(self, max_entries: int = 256, max_bytes: int = 64 * 1024 * 1024) -> None:
        self._entries: OrderedDict[str, CachedResponse] = OrderedDict()
        self._max_entries = max_entries
        self._max_bytes = max_bytes
        self._bytes = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> CachedResponse | None:
        """Return the response kept for ``key``; see :meth:`ETagCache.get`."""
        with self._lock:
            found = self._entries.get(key)
            if found is not None:
                self._entries.move_to_end(key)
            return found

    def put(self, key: str, response: CachedResponse) -> None:
        """Keep ``response`` for ``key``; see :meth:`ETagCache.put`."""
        if len(response.content) > min(MAX_BODY_BYTES, self._max_bytes):
            return
        with self._lock:
            old = self._entries.pop(key, None)
            if old is not None:
                self._bytes -= len(old.content)
            self._entries[key] = response
            self._bytes += len(response.content)
            while len(self._entries) > self._max_entries or self._bytes > self._max_bytes:
                _, dropped = self._entries.popitem(last=False)
                self._bytes -= len(dropped.content)

    def clear(self) -> None:
        """Drop everything kept; see :meth:`ETagCache.clear`."""
        with self._lock:
            self._entries.clear()
            self._bytes = 0

    def discard_prefix(self, prefix: str) -> None:
        """Drop every body whose key starts with ``prefix``.

        Args:
            prefix: The key prefix, such as a :meth:`scoped` view's scope.
        """
        with self._lock:
            for key in [key for key in self._entries if key.startswith(prefix)]:
                self._bytes -= len(self._entries.pop(key).content)

    def scoped(self, scope: str) -> ETagCache:
        """Return a view of this cache that sees only the bodies kept under ``scope``.

        Args:
            scope: A name for one caller, such as a digest of their credential. Keep it
                free of secrets; it prefixes the keys.

        Returns:
            An :class:`ETagCache` whose ``clear`` drops only this scope's bodies.
        """
        return _ScopedETagCache(self, f"{scope}\0")


class _ScopedETagCache:
    """One caller's share of a :class:`MemoryETagCache`."""

    def __init__(self, shared: MemoryETagCache, prefix: str) -> None:
        self._shared = shared
        self._prefix = prefix

    def get(self, key: str) -> CachedResponse | None:
        return self._shared.get(self._prefix + key)

    def put(self, key: str, response: CachedResponse) -> None:
        self._shared.put(self._prefix + key, response)

    def clear(self) -> None:
        self._shared.discard_prefix(self._prefix)
