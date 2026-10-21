"""Capture the envelope one ``mammoth run`` line produces instead of printing it.

``mammoth run`` executes each line of a JSON Lines file through the normal command
path (parsing, validation, confirmation, dry run, handler, executor), inside one
process. The executor hands every envelope it would print to :func:`capture`; while a
line runs, the envelope is kept here and the run command writes it, with the line
number, to the one stdout stream. Nothing else about the command changes.

The scope is a :class:`~contextvars.ContextVar`, so it follows the line into any
helper thread that copies the context and never leaks to a later command.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_CURRENT: ContextVar[list[dict[str, Any]] | None] = ContextVar("mammoth_cli_line", default=None)


def active() -> bool:
    """Whether a ``run`` line is executing in this context."""
    return _CURRENT.get() is not None


def capture(envelope: dict[str, Any]) -> bool:
    """Keep ``envelope`` for the running line; False when no line is running."""
    kept = _CURRENT.get()
    if kept is None:
        return False
    kept.append(envelope)
    return True


@contextmanager
def capturing() -> Iterator[list[dict[str, Any]]]:
    """Collect the envelopes of one line; the list fills while the block runs."""
    kept: list[dict[str, Any]] = []
    token = _CURRENT.set(kept)
    try:
        yield kept
    finally:
        _CURRENT.reset(token)
