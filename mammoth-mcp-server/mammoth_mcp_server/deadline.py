"""The one deadline every wait in a tool call shares.

A client gives up on a tool call after about a minute. A call that waits on two
jobs of a minute each would answer nobody, and the model, told nothing, would
make the call again. So the clock starts with the call's first client, and every
wait in the call spends from it.
"""

import time
from contextvars import ContextVar

from .consts import TOOL_CALL_SECONDS

# Each tool call runs in a context of its own, so each has its own deadline.
_deadline: ContextVar[float | None] = ContextVar("tool_call_deadline", default=None)


def start_the_clock() -> None:
    """Start this tool call's clock, unless it has started already."""
    if _deadline.get() is None:
        _deadline.set(time.monotonic() + TOOL_CALL_SECONDS)


def seconds_left() -> float:
    """How long this tool call may still wait."""
    start_the_clock()
    deadline = _deadline.get()
    assert deadline is not None
    return max(0.0, deadline - time.monotonic())
