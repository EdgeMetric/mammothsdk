"""Every `mammoth ...` command shown in the docs must route and parse.

Recurring bug class: a documented example that no longer matches the CLI --
``folder create Reports`` (rejected ``unexpected_argument``), ``workspace delete
9 --confirm 9`` (bad flag shape), or a command that silently stopped accepting a
positional. Copy-pasting the docs then fails with a usage error.

This test extracts every command example from the shipped docs and runs it
through the real ``mammoth`` entry point, logged out, so no live API or
credentials are involved. A command is allowed to fail for a *semantic* reason
(not authenticated, needs confirmation, resource not found, needs --input) --
those are exit states the docs describe. It must NOT fail because the example is
malformed: an unknown command, an unexpected argument, or an unknown option.
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_DOCS = Path(__file__).resolve().parents[2] / "docs"

# Ambient credentials are stripped so every subprocess starts logged out and
# fails fast (never touching the network) for auth-required commands.
_MAMMOTH_ENV = ("MAMMOTH_API_KEY", "MAMMOTH_API_SECRET",
                "MAMMOTH_WORKSPACE_ID", "MAMMOTH_SERVER_PREFIX", "CI")

# Error codes that mean the DOCUMENTED EXAMPLE ITSELF is malformed. Any of these
# is a test failure; every other non-zero exit is an accepted semantic outcome.
_PARSE_ERROR_CODES = frozenset({
    "unexpected_argument",
    "no_such_command",
    "no_such_option",
    "missing_argument",
    "missing_option",
    "unknown_command",
})

# Skip lines that are not a single self-contained CLI invocation.
_SHELL_META = ("|", ">", "<", "$", "`", "&&", ";", "#", "*")


def _looks_like_placeholder(token: str) -> bool:
    # Angle-bracket placeholders are pre-filtered; catch bare ALL-CAPS ids like
    # ID / FILE / TARGET that docs use as fill-ins rather than runnable values.
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]{1,}", token))


def _extract_commands() -> list[tuple[str, str]]:
    """Return (source_file, command_line) for every runnable `mammoth ...` example."""
    found: list[tuple[str, str]] = []
    for md in sorted(_DOCS.rglob("*.md")):
        in_fence = False
        for raw in md.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                continue
            line = stripped.lstrip("$ ").strip()
            if not line.startswith("mammoth "):
                continue
            if any(meta in line for meta in _SHELL_META):
                continue
            try:
                tokens = shlex.split(line)
            except ValueError:
                continue
            if any(_looks_like_placeholder(t) for t in tokens[1:]):
                continue
            found.append((md.name, line))
    return found


_COMMANDS = _extract_commands()


def test_docs_contain_command_examples() -> None:
    # Guard against the extractor silently matching nothing (e.g. a docs move).
    assert len(_COMMANDS) >= 10, f"only found {len(_COMMANDS)} doc commands"


@pytest.mark.parametrize(
    "source, command",
    _COMMANDS,
    ids=[f"{src}:{cmd}" for src, cmd in _COMMANDS],
)
def test_documented_command_routes_and_parses(source: str, command: str, tmp_path: Path) -> None:
    import os
    tokens = shlex.split(command)
    assert tokens[0] == "mammoth", command
    args = tokens[1:]
    if "--no-input" not in args:
        args.append("--no-input")
    if "--output" not in args and "-o" not in args:
        args += ["--output", "json"]

    env = dict(os.environ)
    for key in _MAMMOTH_ENV:
        env.pop(key, None)
    env["TERMINAL_WIDTH"] = env["COLUMNS"] = "1000"
    env["XDG_CONFIG_HOME"] = str(tmp_path)

    proc = subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *args],
        capture_output=True, text=True, timeout=45, env=env,
    )
    if proc.returncode == 0:
        return  # offline command succeeded

    # Non-zero: it must be a semantic outcome, not a malformed-example parse error.
    code = None
    try:
        code = json.loads(proc.stderr)["error"]["code"]
    except Exception:  # noqa: BLE001
        pass
    assert code is not None, (
        f"[{source}] `{command}` failed without a JSON error envelope "
        f"(exit {proc.returncode}); likely an unrouted usage error.\n"
        f"stderr:\n{proc.stderr[:500]}"
    )
    assert code not in _PARSE_ERROR_CODES, (
        f"[{source}] documented example `{command}` is malformed: {code}\n"
        f"stderr:\n{proc.stderr[:500]}"
    )
