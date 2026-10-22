"""A host-owned event loop and HTTP pool shared by embedded calls.

By default every :func:`mammoth_cli.embed.invoke` builds its own SDK client, event
loop and connection pool, so every call pays a new TCP + TLS handshake. A host
that runs many calls (a server-side agent with a thread pool) can create one
:class:`EmbedRuntime` and pass it as ``invoke(..., runtime=runtime)``: all calls then
send their requests through one ``httpx.AsyncClient`` that lives on one long-lived
loop thread, and keep-alive connections are reused across calls and users.

The shared client holds no credentials and no cookies. Each call's own
``Authorization`` / ``X-API-*`` headers, forwarded ``Cookie`` and run id are added
to that call's requests by its own ``MammothClient`` (``default_headers``), so two
users on one runtime never see each other's. An SDK too old to do that is not
shared with: the call falls back to its own client, as without a runtime.
"""

from __future__ import annotations

import asyncio
import atexit
import inspect
import threading
from concurrent.futures import Future
from typing import Any


def sdk_takes_default_headers() -> bool:
    """Whether the installed SDK's client takes ``default_headers`` (after mammoth-io 0.8.48)."""
    from mammoth.client import MammothClient

    return "default_headers" in inspect.signature(MammothClient.__init__).parameters


def sdk_can_share_a_client() -> bool:
    """Whether the installed SDK keeps every per-client header off a shared ``http_client``.

    The SDK that accepts ``default_headers`` sends credentials and forwarded headers on
    each request. Older ones write them to ``session.headers``, which a shared client
    would carry to every other user.
    """
    from mammoth import client as sdk_client
    from mammoth.client import MammothClient

    return (
        sdk_takes_default_headers()
        and "http_client" in inspect.signature(MammothClient.__init__).parameters
        and hasattr(sdk_client, "shared_http_client")
    )


class EmbedRuntime:
    """One daemon loop thread and one cookie-less ``httpx.AsyncClient`` for many calls.

    Safe to use from any number of threads. :meth:`close` stops it; the process-wide
    one from :func:`shared_pool` is also closed at interpreter exit.
    """

    def __init__(
        self,
        *,
        max_connections: int = 100,
        max_keepalive_connections: int = 32,
        keepalive_expiry: float = 30.0,
        timeout: float = 60.0,
    ) -> None:
        """Start the loop thread and open the shared client on it.

        Args:
            max_connections: Most connections open at once; extra requests wait.
            max_keepalive_connections: Idle connections kept for reuse.
            keepalive_expiry: Seconds an idle connection is kept. Keep it below the
                server's own idle timeout.
            timeout: Fallback timeout in seconds for a request that names none. The SDK
                sets its own per request.
        """
        self._lock = threading.Lock()
        self._closed = False
        #: The shared pool, or None when the installed SDK cannot build one safely.
        self.http_client: Any = None
        if sdk_can_share_a_client():
            from mammoth.client import shared_http_client

            self.http_client = shared_http_client(
                timeout=timeout,
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
                keepalive_expiry=keepalive_expiry,
            )
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._serve, name="mammoth-embed-runtime", daemon=True
        )
        self._thread.start()

    def _serve(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    @property
    def is_open(self) -> bool:
        """False once :meth:`close` has run."""
        return not self._closed

    @property
    def shares_safely(self) -> bool:
        """Whether a call may send its requests through this runtime's client."""
        return self.is_open and self.http_client is not None and sdk_can_share_a_client()

    def run(self, work: Any) -> Any:
        """Run one awaitable on the runtime's loop and return its result.

        Blocks the calling thread (never the loop) until it is done. Interrupting the
        wait cancels the work.

        Raises:
            RuntimeError: The runtime is closed.
        """
        if self._closed:
            if inspect.iscoroutine(work):
                work.close()
            raise RuntimeError("the embed runtime is closed")
        if not inspect.iscoroutine(work):
            work = _await(work)
        future: Future[Any] = asyncio.run_coroutine_threadsafe(work, self._loop)
        try:
            return future.result()
        except BaseException:
            future.cancel()
            raise

    def close(self) -> None:
        """Close the shared client and stop the loop thread. Safe to call twice."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        try:
            if self.http_client is not None:
                asyncio.run_coroutine_threadsafe(self.http_client.aclose(), self._loop).result(10)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(10)
            if not self._thread.is_alive():
                self._loop.close()

    def __enter__(self) -> EmbedRuntime:
        """Use the runtime as a context manager that closes it on exit."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the runtime."""
        self.close()


async def _await(work: Any) -> Any:
    return await work


_SHARED: EmbedRuntime | None = None
_SHARED_LOCK = threading.Lock()


def shared_pool() -> EmbedRuntime:
    """The process-wide :class:`EmbedRuntime`, created on first use and closed at exit.

    A new one is made if the previous was closed with :func:`close_shared_pool`.
    """
    global _SHARED
    with _SHARED_LOCK:
        if _SHARED is None or not _SHARED.is_open:
            _SHARED = EmbedRuntime()
        return _SHARED


def close_shared_pool() -> None:
    """Close the process-wide runtime, if one was made."""
    global _SHARED
    with _SHARED_LOCK:
        runtime, _SHARED = _SHARED, None
    if runtime is not None:
        runtime.close()


atexit.register(close_shared_pool)

__all__ = [
    "EmbedRuntime",
    "close_shared_pool",
    "sdk_can_share_a_client",
    "sdk_takes_default_headers",
    "shared_pool",
]
