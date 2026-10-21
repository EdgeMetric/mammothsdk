"""Reads fetched together ahead of a write, handed back to the checks that need them.

A view transform checks the view several times before it writes (what the step would
change, the row count before, the column types), and each check used to fetch the same
record again, one round trip after another. :func:`prefetch` fetches the records once, all at
once; a service then answers the same call from here until the write starts, when
:meth:`ReadMemo.clear` drops them so nothing read after the write can be stale.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

from mammoth_cli.errors.envelope import CliError

#: Arguments that do not change which record a read returns.
_IGNORED = frozenset({"project_id"})


class ReadMemo:
    """Answers of reads made ahead of a write, kept until the write starts."""

    def __init__(self) -> None:
        self._answers: dict[tuple[str, tuple[tuple[str, str], ...]], Any] = {}

    @staticmethod
    def _key(symbol: str, kwargs: dict[str, Any]) -> tuple[str, tuple[tuple[str, str], ...]]:
        items = sorted((k, repr(v)) for k, v in kwargs.items() if k not in _IGNORED)
        return symbol, tuple(items)

    def store(self, symbol: str, kwargs: dict[str, Any], value: Any) -> None:
        self._answers[self._key(symbol, kwargs)] = value

    def lookup(self, symbol: str, kwargs: dict[str, Any]) -> tuple[bool, Any]:
        """``(True, copy of the answer)`` when this exact read was made ahead."""
        key = self._key(symbol, kwargs)
        if key not in self._answers:
            return False, None
        return True, copy.deepcopy(self._answers[key])

    def clear(self) -> None:
        self._answers.clear()


def prefetch(service: Any, calls: Sequence[tuple[str, dict[str, Any]]]) -> list[Any]:
    """Run independent reads together and remember the ones that succeeded.

    Returns one result per call, in order: the value, or the ``CliError`` that call raised.
    A service with no memo (a stand-in) still gets the reads run together.
    """
    results: list[Any] = service.call_many(list(calls))
    memo = getattr(service, "memo", None)
    if isinstance(memo, ReadMemo):
        for (symbol, kwargs), result in zip(calls, results, strict=True):
            if not isinstance(result, CliError):
                memo.store(symbol, kwargs, result)
    return results


def remember(service: Any, symbol: str, kwargs: dict[str, Any], value: Any) -> None:
    """Keep a read just made so the next identical one is answered from it."""
    memo = getattr(service, "memo", None)
    if isinstance(memo, ReadMemo):
        memo.store(symbol, kwargs, value)


def forget(service: Any) -> None:
    """Drop every remembered read (the reads that follow must see the service as it is)."""
    memo = getattr(service, "memo", None)
    if isinstance(memo, ReadMemo):
        memo.clear()
