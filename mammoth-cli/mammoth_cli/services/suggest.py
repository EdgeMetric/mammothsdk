"""Did-you-mean suggestions for unknown commands, options and columns.

One small, deterministic matcher shared by the usage-error renderer (an unknown
command), the strict argument check (an unknown option) and the column
resolver (an unknown display name). A case-only difference ranks first, then
the closest spellings by :mod:`difflib` ratio.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Iterable, Sequence

#: How alike two spellings must be (``difflib`` ratio) to be offered.
_CUTOFF = 0.6
#: A command-path word must be this alike to the unknown one to be offered.
_PATH_WORD_CUTOFF = 0.75
#: An option name (dashes stripped) must be this alike to be offered.
_OPTION_CUTOFF = 0.7
_MAX_COMMANDS = 3
#: ``--project3633``: a known flag with its value run into it.
_RUN_ON_VALUE = re.compile(r"^(?P<flag>--[a-z][a-z-]*?)(?P<value>\d[\w.-]*)$")

DISCOVERY_HINT = (
    'To find the command for a goal, describe it: mammoth how "GOAL" (an ordered recipe) '
    'or mammoth schema find "WORDS" (matching commands).'
)


def nearest(value: str, choices: Iterable[str], *, limit: int = 3) -> list[str]:
    """The choices closest to ``value``: exact-but-for-case first, then by spelling."""
    pool = list(dict.fromkeys(str(choice) for choice in choices))
    folded = value.casefold()
    same_case = [choice for choice in pool if choice.casefold() == folded and choice != value]
    by_fold: dict[str, str] = {}
    for choice in pool:
        by_fold.setdefault(choice.casefold(), choice)
    close = [
        by_fold[match]
        for match in difflib.get_close_matches(folded, list(by_fold), n=limit + 2, cutoff=_CUTOFF)
    ]
    ranked = list(dict.fromkeys([*same_case, *close]))
    return [choice for choice in ranked if choice != value][:limit]


def nearest_one(value: str, choices: Iterable[str]) -> str | None:
    """The single closest choice, or None when nothing is close."""
    found = nearest(value, choices, limit=1)
    return found[0] if found else None


def option_suggestion(token: str, known: Sequence[str]) -> dict[str, str] | None:
    """What an unknown option token most likely meant.

    Returns ``{"flag", "value"?, "hint"}`` or None. Recognizes an option and its
    value passed as one argv token (``"--project 3633"`` from a quoted shell
    word, ``--project3633`` typed without the space) and a misspelt flag.
    """
    name = token.split("=", 1)[0]
    head, _, rest = token.strip().partition(" ")
    if rest and head in known:
        return {
            "flag": head,
            "value": rest.strip(),
            "hint": (
                f"'{token}' reached the CLI as one argument. Pass the value separately: "
                f"{head} {rest.strip()} (two arguments; do not quote them together)."
            ),
        }
    run_on = _RUN_ON_VALUE.match(name)
    if run_on and run_on.group("flag") in known:
        flag, value = run_on.group("flag"), run_on.group("value")
        return {
            "flag": flag,
            "value": value,
            "hint": f"Put a space between the option and its value: {flag} {value}.",
        }
    # Compare without the dashes every flag shares, which would make any two look alike.
    bare = {flag.lstrip("-"): flag for flag in known}
    close = difflib.get_close_matches(name.lstrip("-"), list(bare), n=1, cutoff=_OPTION_CUTOFF)
    if close:
        flag = bare[close[0]]
        return {"flag": flag, "hint": f"Did you mean '{flag}'?"}
    return None


def command_suggestions(
    parent: Sequence[str], word: str, paths: Iterable[Sequence[str]]
) -> list[str]:
    """Commands the caller most likely meant when ``word`` is not a command under ``parent``.

    ``paths`` are every command path as words. Candidates, best first: a sibling
    under ``parent`` spelled like ``word``; then any command group or command whose
    own word is ``word`` (or close to it), cut at that word, so ``pipeline`` finds
    ``view pipeline``. Returned as ``mammoth ...`` strings, at most three.
    """
    folded = word.casefold()
    prefix = tuple(parent)
    siblings = sorted(
        {tuple(path[: len(prefix) + 1]) for path in paths if tuple(path[: len(prefix)]) == prefix}
        - {prefix}
    )
    by_name = {path[-1]: path for path in siblings if len(path) == len(prefix) + 1}
    ranked: list[tuple[float, int, tuple[str, ...]]] = []
    for name in difflib.get_close_matches(folded, list(by_name), n=_MAX_COMMANDS, cutoff=_CUTOFF):
        ratio = difflib.SequenceMatcher(None, folded, name).ratio()
        ranked.append((2.0 + ratio, 0, by_name[name]))
    seen: set[tuple[str, ...]] = {candidate for _, _, candidate in ranked}
    for path in paths:
        for index, part in enumerate(path):
            if index < len(prefix) and tuple(path[: index + 1]) == prefix[: index + 1]:
                continue
            ratio = 1.0 if part == folded else difflib.SequenceMatcher(None, folded, part).ratio()
            if ratio < _PATH_WORD_CUTOFF:
                continue
            candidate = tuple(path[: index + 1])
            if candidate in seen:
                continue
            seen.add(candidate)
            ranked.append((ratio, len(candidate), candidate))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [f"mammoth {' '.join(path)}" for _, _, path in ranked[:_MAX_COMMANDS]]
