"""Systematic guard against handler/schema positional drift (review findings #1, #5).

The drift bug has one shape: a command handler reads a resource id from a
*positional* argument, but that positional is not registered in
:mod:`mammoth_cli.services.positionals`. The consequences are that the command is
uninvokable (the surplus positional is rejected by strict validation) *and* the
id is still advertised as an ``--input`` field the handler never reads.

An earlier version of this test scanned only for two exact helper spellings
(``_require_int_positional`` / ``_require_string_positional``). That was too
narrow and let the *same* bug re-escape review twice:

* ``schema get`` / ``capability get`` read the id via ``registry._require_arg``
  (a differently-named helper) -> zero positionals registered -> uninvokable.
* eight ``support`` create/register verbs read it via
  ``_require_positional_or_field`` -> the positional form was rejected outright.

So this test now derives the invariant from *every* required-positional idiom in
the codebase, matching any ``_require_<...>(invocation, ...)`` call. Each such
call means the handler will read a positional at some index, so that index must
correspond to a registered positional. It is a fast static check (it reads
handler source; it invokes nothing), so it catches a *new* command that
introduces the same drift, not just the ones already fixed.
"""

from __future__ import annotations

import inspect
import re

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.services.positionals import resolve_positionals

# Every required-positional reader is a helper named ``_require_*`` taking
# ``invocation`` as its first argument. We match the family generically rather
# than enumerating spellings, so a new helper name cannot silently slip past.
# Matched names in the tree today: ``_require_arg``, ``_require_int_positional``,
# ``_require_string_positional``, ``_require_str_positional``,
# ``_require_int_positional_at``, ``_require_string_positional_at``,
# ``_require_positional_or_field``.
_REQUIRE_CALL = re.compile(r"_require_([a-z_]+)\(\s*invocation\b([^)]*)\)")
# The ``_at`` helpers take an explicit index. Its argument order is inconsistent
# across modules (``(invocation, 0, name)`` vs ``(invocation, name, 1)``), so we
# take the first integer literal appearing among the arguments.
_FIRST_INT = re.compile(r"\b(\d+)\b")

# Helper-name substrings that identify a positional reader. ``arg`` covers
# ``registry._require_arg``; ``positional`` covers every ``*_positional*`` and
# ``positional_or_field`` variant.
_POSITIONAL_HELPER_MARKERS = ("arg", "positional")


def _required_positional_count(source: str) -> int:
    """Return how many leading positionals a handler's source requires.

    Derived from the highest positional index the handler reads via any
    ``_require_*(invocation, ...)`` helper, plus one (indices are zero-based).
    Returns 0 when the handler reads no positional.
    """
    indices: list[int] = []
    for helper_name, arguments in _REQUIRE_CALL.findall(source):
        if not any(marker in helper_name for marker in _POSITIONAL_HELPER_MARKERS):
            continue
        if "_at" in helper_name:
            match = _FIRST_INT.search(arguments)
            indices.append(int(match.group(1)) if match else 0)
        else:
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
                f"{command_id}: handler reads positional index {need - 1} but only "
                f"{len(registered)} positional(s) registered -> command is uninvokable "
                f"(the surplus positional is rejected) and the id is silently advertised "
                f"as an --input field"
            )
    assert not offenders, "handler/schema positional drift:\n" + "\n".join(offenders)


if __name__ == "__main__":
    test_every_handler_positional_is_registered()
    print("ok")
