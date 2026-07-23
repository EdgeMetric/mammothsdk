"""Contract: every recovery command in an error envelope is agent-runnable.

An autonomous agent runs recovery commands non-interactively and parses JSON.
So every recovery command string emitted by an error builder MUST carry both
``--output json`` (as adjacent tokens) and ``--no-input``. The single allowed
exception is the interactive auth login command (``mammoth auth login``), which
is inherently interactive and cannot be made non-interactive.

This test scans every public CliError builder in ``errors.envelope`` that
populates ``recovery_commands`` so a future builder that forgets the flags
fails loudly here.
"""

from __future__ import annotations

import ast
import inspect
import shlex
from pathlib import Path

import pytest

from mammoth_cli.errors import envelope

AUTH_LOGIN_PREFIX = "mammoth auth login"

# The installed package root (…/mammoth_cli), scanned statically below.
_PKG_ROOT = Path(envelope.__file__).resolve().parents[1]


def _has_adjacent_output_json(tokens: list[str]) -> bool:
    for first, second in zip(tokens, tokens[1:]):
        if first == "--output" and second == "json":
            return True
    return False


def _discover_recovery_commands() -> list[tuple[str, str]]:
    """Call every public envelope builder and collect (builder, command) pairs.

    Builders that need arguments are invoked with values that force
    ``recovery_commands`` to be populated (notably ``timeout_error`` needs a
    ``job_id``). Builders that cannot be called generically are skipped only if
    they never set recovery commands.
    """

    # Explicit invocations for builders that require arguments to populate
    # recovery_commands. Keep this table exhaustive for such builders.
    explicit: dict[str, object] = {
        "timeout_error": envelope.timeout_error(job_id="55123", command="job"),
        "missing_project_error": envelope.missing_project_error(),
    }

    pairs: list[tuple[str, str]] = []
    seen_builders: set[str] = set()

    for name, error in explicit.items():
        seen_builders.add(name)
        assert isinstance(error, envelope.CliError)
        assert error.recovery_commands, f"{name} must populate recovery_commands"
        for cmd in error.recovery_commands:
            pairs.append((name, cmd))

    # Scan the module for any other public builder returning a CliError that
    # populates recovery_commands, so a newly added builder is covered too.
    for name, obj in inspect.getmembers(envelope, inspect.isfunction):
        if name.startswith("_") or name in seen_builders:
            continue
        if obj.__module__ != envelope.__name__:
            continue
        sig = inspect.signature(obj)
        # Only call builders we can satisfy with no required positional args.
        required = [
            p
            for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
            and p.kind
            in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        if required:
            continue
        try:
            result = obj()
        except Exception:  # pragma: no cover - defensive; builder needs args
            continue
        if not isinstance(result, envelope.CliError):
            continue
        for cmd in result.recovery_commands:
            pairs.append((name, cmd))

    return pairs


_RECOVERY_COMMANDS = _discover_recovery_commands()


def test_recovery_commands_discovered() -> None:
    """Sanity: the scan found the known builders' recovery commands."""
    builders = {name for name, _ in _RECOVERY_COMMANDS}
    assert "missing_project_error" in builders
    assert "timeout_error" in builders
    # missing_project_error emits 2, timeout_error emits 2 -> at least 4.
    assert len(_RECOVERY_COMMANDS) >= 4


@pytest.mark.parametrize(
    ("builder", "command"),
    _RECOVERY_COMMANDS,
    ids=[f"{name}:{cmd}" for name, cmd in _RECOVERY_COMMANDS],
)
def test_recovery_command_is_agent_safe(builder: str, command: str) -> None:
    tokens = shlex.split(command)
    assert tokens, f"{builder} emitted an empty recovery command"

    if command.startswith(AUTH_LOGIN_PREFIX):
        # Interactive auth login is the single allowed exception.
        return

    assert _has_adjacent_output_json(
        tokens
    ), f"{builder} recovery command missing adjacent '--output json': {command!r}"
    assert "--no-input" in tokens, f"{builder} recovery command missing '--no-input': {command!r}"


# --- Exhaustive static scan across the whole package -----------------------
#
# The dynamic scan above only reaches errors.envelope. Recovery commands are
# also produced elsewhere (confirm.py, resolver.py, credentials.py, the command
# modules, service layers). This AST scan finds EVERY recovery-command string
# literal in the package -- list elements of a ``recovery_commands=[...]``
# keyword and arguments to a ``recovery.append(...)`` call -- so no producer
# escapes the contract, whichever module it lives in.


def _skeleton(node: ast.expr) -> str | None:
    """Return the literal skeleton of a str/f-string node, else None.

    For an f-string, runtime-interpolated parts are replaced with a sentinel
    that carries no flags, so the presence checks below see only the literal
    text the author wrote (which is where the flags must live).
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append(" \x00 ")  # interpolated value: opaque, flag-free
        return "".join(parts)
    return None


def _iter_recovery_command_literals() -> list[tuple[str, str]]:
    """Every (location, command-skeleton) recovery literal in the package."""
    found: list[tuple[str, str]] = []
    for path in sorted(_PKG_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(_PKG_ROOT.parent)
        for node in ast.walk(tree):
            # recovery_commands=[ ... ] keyword argument.
            if isinstance(node, ast.keyword) and node.arg == "recovery_commands":
                if isinstance(node.value, ast.List):
                    for element in node.value.elts:
                        skel = _skeleton(element)
                        if skel is not None:
                            found.append((f"{rel}", skel))
            # <name-containing-'recovery'>.append( ... )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append"
                and isinstance(node.func.value, ast.Name)
                and "recovery" in node.func.value.id
                and node.args
            ):
                skel = _skeleton(node.args[0])
                if skel is not None:
                    found.append((f"{rel}", skel))
    return found


_RECOVERY_LITERALS = _iter_recovery_command_literals()


def test_static_scan_reaches_multiple_modules() -> None:
    """Sanity: the AST scan sees producers beyond errors.envelope."""
    modules = {loc for loc, _ in _RECOVERY_LITERALS}
    assert any("envelope.py" in m for m in modules), modules
    # The scan must cover more than one module (auth-login producers live in
    # resolver.py, context.py, config.py, credentials.py, service layers).
    assert len(modules) >= 2, modules


@pytest.mark.parametrize(
    ("location", "command"),
    _RECOVERY_LITERALS,
    ids=[f"{loc}:{cmd}" for loc, cmd in _RECOVERY_LITERALS],
)
def test_every_recovery_literal_is_agent_safe(location: str, command: str) -> None:
    # A placeholder command (e.g. "mammoth ... --yes") is never runnable.
    assert "..." not in command, (
        f"{location}: non-executable placeholder recovery command: {command!r}"
    )

    if command.startswith(AUTH_LOGIN_PREFIX):
        # Interactive auth login (and its --storage variants) is the exception.
        return

    assert "--output json" in command, (
        f"{location}: recovery command missing '--output json': {command!r}"
    )
    assert "--no-input" in command, (
        f"{location}: recovery command missing '--no-input': {command!r}"
    )
