"""One service per credential set for the length of one command run.

Kept apart from :mod:`mammoth_cli.runtime.session` so the executor can open the scope without
importing the SDK for commands that never call the API.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from contextvars import ContextVar
from typing import Any

#: The services one command run has opened so far, by the options that distinguish them;
#: ``None`` outside :func:`shared_services`.
SHARED: ContextVar[dict[tuple[Any, ...], Any] | None] = ContextVar("SHARED", default=None)


#: Answers that cannot change while a service is open (the projects its credential is
#: pinned to), by ``id`` of the service; ``None`` outside :func:`shared_services`.
FIXED_ANSWERS: ContextVar[dict[int, Any] | None] = ContextVar("FIXED_ANSWERS", default=None)


#: The credentials one ``mammoth run`` has resolved so far, by profile; ``None`` outside
#: :func:`remembering_auth`.
AUTH_MEMO: ContextVar[dict[tuple[Any, ...], Any] | None] = ContextVar("AUTH_MEMO", default=None)


@contextmanager
def remembering_auth() -> Iterator[dict[tuple[Any, ...], Any]]:
    """Resolve each profile's credentials once for the length of this block.

    Every line of a ``mammoth run`` resolves its credentials like a single command does
    (keyring, profile file, environment token). The answer cannot change within one
    run, so the first line's is reused; ``clear()`` drops it after a line that changes
    credentials.
    """
    memo: dict[tuple[Any, ...], Any] = {}
    token = AUTH_MEMO.set(memo)
    try:
        yield memo
    finally:
        AUTH_MEMO.reset(token)


@contextmanager
def shared_services() -> Iterator[None]:
    """Let every :func:`open_service` in this block reuse one service per credential set.

    A command's handler, its verify step and its state read-back each opened their own
    service, and each new service starts a new connection (DNS, TCP, TLS: about half a
    second against the hosted API) and a new token lookup. Inside this block the first
    open builds the service and the later ones, whose reads follow the write, take the
    same one over its warm connection. The services are closed when the block ends.
    """
    if SHARED.get() is not None:
        yield
        return
    opened: dict[tuple[Any, ...], Any] = {}
    token = SHARED.set(opened)
    answers = FIXED_ANSWERS.set({})
    try:
        yield
    finally:
        FIXED_ANSWERS.reset(answers)
        SHARED.reset(token)
        for service in opened.values():
            # Closing must not hide the command's own result.
            with suppress(Exception):
                service.close()
