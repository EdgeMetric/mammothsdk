"""Systematic guard against handler/schema positional drift (review finding #5).

The drift bug (``project.get``, ``data-app user remove``, ``ai condition
generate``, ``ai expression generate``, ``folder delete``) has one shape: a
command handler reads a resource id from a *positional* argument, but that
positional is not registered in :mod:`mammoth_cli.services.positionals`. The
consequences are that the command is uninvokable (the surplus positional is
rejected by strict validation) *and* the id is still advertised as an ``--input``
field the handler never reads.

Rather than enumerate the known offenders, this test derives the invariant
directly from the handlers: every positional index a handler *requires* (via the
``_require_*_positional``/``_require_*_positional_at`` helpers) must correspond to
a registered positional for that command. It is a fast static check -- it reads
handler source, it does not invoke anything -- so it catches a *new* command that
introduces the same drift, not just the ones already fixed.
"""

from __future__ import annotations

import inspect
import re

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.services.positionals import resolve_positionals

# ``_require_int_positional_at(invocation, N, ...)`` / string variant: the handler
# reads the positional at index N, so at least N+1 positionals must be registered.
_REQUIRE_AT = re.compile(r"_require_(?:int|string)_positional_at\(\s*invocation\s*,\s*(\d+)")
# ``_require_int_positional(invocation, ...)`` / string variant: index 0.
_REQUIRE_ZERO = re.compile(r"_require_(?:int|string)_positional\(\s*invocation\b")


def _required_positional_count(source: str) -> int:
    """Return how many leading positionals a handler's source requires."""
    indices = [int(match) for match in _REQUIRE_AT.findall(source)]
    if _REQUIRE_ZERO.search(source):
        indices.append(0)
    return max(indices) + 1 if indices else 0


def test_every_handler_positional_is_registered() -> None:
    offenders: list[str] = []
    for command_id, handler in HANDLERS.items():
        try:
            source = inspect.getsource(handler)
        except (OSError, TypeError):  # pragma: no cover - builtins have no source
            continue
        need = _required_positional_count(source)
        if need == 0:
            continue
        registered = resolve_positionals(command_id)
        if len(registered) < need:
            offenders.append(
                f"{command_id}: handler requires {need} positional(s) but only "
                f"{len(registered)} registered -> command is uninvokable and the "
                f"id is silently advertised as an --input field"
            )
    assert not offenders, "handler/schema positional drift:\n" + "\n".join(offenders)


if __name__ == "__main__":
    test_every_handler_positional_is_registered()
    print("ok")
