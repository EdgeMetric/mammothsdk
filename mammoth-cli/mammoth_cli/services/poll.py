"""The gaps between the checks of a read-back that waits for a write to settle."""

from __future__ import annotations

from collections.abc import Iterator

#: The first gap: most writes have settled by the second check.
POLL_FIRST_DELAY_S = 0.1


def poll_delays(total: float, cap: float) -> Iterator[float]:
    """Gaps that start at ``POLL_FIRST_DELAY_S``, grow like the SDK's pipeline wait and
    stop at ``cap``; they add up to ``total`` (the last one is cut to fit)."""
    # Imported here: the pipeline module is the SDK's heaviest and most commands never poll.
    from mammoth.api.pipeline import PIPELINE_POLL_GROWTH

    delay = POLL_FIRST_DELAY_S
    left = total
    while left > 0:
        gap = min(delay, cap, left)
        yield gap
        left -= gap
        delay *= PIPELINE_POLL_GROWTH
