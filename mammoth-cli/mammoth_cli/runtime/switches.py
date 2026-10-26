"""Environment switches that turn a local cache off."""

from __future__ import annotations

import os

_OFF = frozenset({"0", "false", "no", "off"})


def switched_on(name: str) -> bool:
    """Read an on-by-default switch from the environment.

    Args:
        name: The environment variable, such as ``MAMMOTH_CLI_ETAG_CACHE``.

    Returns:
        False when the variable is 0, false, no or off (any case); True otherwise.
    """
    return os.environ.get(name, "1").strip().lower() not in _OFF
