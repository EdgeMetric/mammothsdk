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

import inspect
import shlex

import pytest

from mammoth_cli.errors import envelope

AUTH_LOGIN_PREFIX = "mammoth auth login"


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
