"""Per-call state for an in-process (embedded) invocation.

:func:`mammoth_cli.embed.invoke` runs a command inside a host process that may
run several commands at once, each for a different user. The login and the
captured envelope therefore live in a :class:`contextvars.ContextVar`, never in
``os.environ`` or a profile file: each thread (or task) sees only its own.
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable, Iterable
from concurrent.futures import Executor
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mammoth_cli.context.resolver import ExplicitLogin


@dataclass
class EmbeddedCall:
    """The login for one embedded call and the envelope it produced."""

    login: ExplicitLogin
    envelopes: list[dict[str, Any]] = field(default_factory=list)
    #: Refuse commands the production server does not serve yet, and hide them from discovery.
    hide_pending: bool = False
    #: Text written to ``sys.stdout`` / ``sys.stderr`` while the call ran, by stream name.
    stray: dict[str, list[str]] = field(default_factory=lambda: {"stdout": [], "stderr": []})


_CURRENT: ContextVar[EmbeddedCall | None] = ContextVar("mammoth_cli_embedded", default=None)


def current() -> EmbeddedCall | None:
    """The embedded call running in this context, or None for a normal CLI run."""
    return _CURRENT.get()


def active() -> bool:
    """Whether this context runs an embedded call."""
    return _CURRENT.get() is not None


def hides_pending() -> bool:
    """Whether this embedded call refuses and hides commands pending a server release."""
    call = _CURRENT.get()
    return call is not None and call.hide_pending


def capture(envelope: dict[str, Any]) -> bool:
    """Keep ``envelope`` for the embedded caller; False when not embedded."""
    call = _CURRENT.get()
    if call is None:
        return False
    call.envelopes.append(envelope)
    return True


def enter(call: EmbeddedCall) -> Any:
    """Make ``call`` current; returns the token for :func:`leave`."""
    return _CURRENT.set(call)


def leave(token: Any) -> None:
    """Restore the context that was current before :func:`enter`."""
    _CURRENT.reset(token)


def pool_map[T, R](pool: Executor, fn: Callable[[T], R], items: Iterable[T]) -> list[R]:
    """``pool.map(fn, items)`` with each worker running in a copy of this context.

    A pool thread does not inherit context variables, so without this an
    embedded call's workers would fall back to the host's own profile login.
    The copies are taken here, in the calling thread, one per item (a context
    cannot be entered by two threads at once).
    """
    jobs = [(copy_context(), item) for item in items]
    return list(pool.map(lambda job: job[0].run(fn, job[1]), jobs))


class _RoutedStream:
    """A ``sys.stdout`` / ``sys.stderr`` stand-in that keeps an embedded call's text out.

    ``contextlib.redirect_stdout`` swaps the stream for the whole process, so one
    call's redirect would catch the host's other threads (and theirs, this
    call's). This proxy is installed once and decides per write: in a context that
    runs an embedded call the text goes to that call's buffer, anywhere else to the
    stream that was there before. Like a real text stream it refuses bytes (Click
    probes with ``write(b"")`` to tell text from binary), and its ``buffer`` is routed
    the same way, so no write path reaches the host's stream from inside a call.
    Everything else (``isatty``, ``encoding``, ``fileno``...) is the real stream's.
    """

    def __init__(self, real: Any, name: str) -> None:
        self._real = real
        self._name = name
        self._buffer = _RoutedBuffer(real, name)

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError(f"write() argument must be str, not {type(text).__name__}")
        call = _CURRENT.get()
        if call is None:
            return int(self._real.write(text))
        call.stray[self._name].append(text)
        return len(text)

    def writelines(self, lines: Iterable[str]) -> None:
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        if _CURRENT.get() is None:
            self._real.flush()

    @property
    def buffer(self) -> Any:
        if not hasattr(self._real, "buffer"):
            raise AttributeError("buffer")
        return self._buffer

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


class _RoutedBuffer:
    """The ``buffer`` of a :class:`_RoutedStream`: bytes are decoded into the call's text."""

    def __init__(self, real: Any, name: str) -> None:
        self._real = real
        self._name = name

    def write(self, data: bytes) -> int:
        call = _CURRENT.get()
        if call is None:
            return int(self._real.buffer.write(data))
        call.stray[self._name].append(bytes(data).decode("utf-8", errors="replace"))
        return len(data)

    def flush(self) -> None:
        if _CURRENT.get() is None:
            self._real.buffer.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real.buffer, name)


_INSTALL_LOCK = threading.Lock()


def install_stream_guards() -> None:
    """Route embedded calls' stdout and stderr to their buffers; safe to call repeatedly.

    Idempotent and thread-safe. A stream someone else swapped in since the last call
    (a test's capture, a ``redirect_stdout`` that ended) is wrapped again, so every
    embedded call starts guarded.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if stream is not None and not isinstance(stream, _RoutedStream):
            with _INSTALL_LOCK:
                stream = getattr(sys, name)
                if stream is not None and not isinstance(stream, _RoutedStream):
                    setattr(sys, name, _RoutedStream(stream, name))
