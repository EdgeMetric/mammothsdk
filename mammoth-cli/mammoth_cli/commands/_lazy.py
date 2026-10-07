"""A read-only table of callables imported on first lookup.

The command tree names about 600 handlers across 40 command modules. Importing
them all to build ``--help``, to suggest a close command name or to run one
command cost seconds; a table of ``"module:attribute"`` strings costs nothing
until an entry is looked up.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Iterator, Mapping
from typing import Any


class LazyTable[T: Callable[..., Any]](Mapping[str, T]):
    """Map a key to a callable named by a ``"module:attribute"`` string."""

    def __init__(self, targets: Mapping[str, str]) -> None:
        self._targets = targets
        self._loaded: dict[str, T] = {}

    def __getitem__(self, key: str) -> T:
        if key in self._loaded:
            return self._loaded[key]
        module_name, _, attribute = self._targets[key].partition(":")
        value: T = getattr(importlib.import_module(module_name), attribute)
        self._loaded[key] = value
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self._targets)

    def __len__(self) -> int:
        return len(self._targets)

    def __contains__(self, key: object) -> bool:
        return key in self._targets
