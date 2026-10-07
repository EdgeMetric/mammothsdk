"""Known CLI bugs the fuzz harness finds. Each is an xfail, never a silent pass.

A failing case that matches an entry here is reported as XFAIL naming the bug.
Each entry also has a canary reproducer that runs ``xfail(strict=True)``: when the
CLI is fixed the canary passes unexpectedly, the suite turns red, and the entry
is deleted in the fixing PR. A failure that matches no entry fails the suite.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tests.fuzz.harness import Case, PtyRow


@dataclass(frozen=True)
class KnownBug:
    key: str
    summary: str
    matches: Callable[[str, str, list[str]], bool]
    canary: Case | PtyRow | None


def _all(problems: list[str], needle: str) -> bool:
    return all(needle in p for p in problems)


# Found by the first full fuzz run. No canary yet: a fixing PR deletes its entry
# and the matching rows turn green; until then the rows stay XFAIL in the report.
KNOWN_BUGS: list[KnownBug] = [
    KnownBug(
        "prompt-abort-api-error",
        "Ctrl-C, EOF or an invalid answer at a prompt ends as api_error 'failed unexpectedly'",
        lambda command, label, problems: label.startswith("pty")
        and _all(problems, "failed unexpectedly"),
        None,
    ),
    KnownBug(
        "prompt-hang",
        "an empty Enter at the auth login method prompt leaves the process alive",
        lambda command, label, problems: label.startswith("pty") and _all(problems, "hang:"),
        None,
    ),
    KnownBug(
        "unknown-flag-ignored",
        "auth status, config list/path and context project clear/status exit 0 on an unknown flag",
        lambda command, label, problems: any("silently accepted" in p for p in problems),
        None,
    ),
    KnownBug(
        "unknown-flag-unnamed",
        "an unknown or misspelled flag is reported as another error that never names the flag",
        lambda command, label, problems: not label.startswith("pty")
        and _all(problems, "does not name the bad input"),
        None,
    ),
]


def match(command: str, label: str, problems: list[str]) -> KnownBug | None:
    for bug in KNOWN_BUGS:
        if bug.matches(command, label, problems):
            return bug
    return None
