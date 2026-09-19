"""The ``skill`` commands: manage the bundled ``mammoth-cli`` agent skill.

These commands are local: they copy the packaged canonical skill into each
agent's skills directory (Codex, Claude Code, Cursor) at user or project scope,
list or locate installs, and update or remove installer-owned copies. Options
come from the strict ``--input`` document: ``agents`` (a list, or ``["all"]``),
``scope`` (``user`` or ``project``), and ``force`` (a bool). No network access
and no secret is involved.
"""

from __future__ import annotations

import time
from typing import Any

from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.skills import installer

HandlerResult = tuple[Any, dict[str, Any]]


def _options(invocation: Invocation) -> tuple[list[str] | None, str, bool]:
    document = invocation.bound_input()
    agents = document.get("agents")
    agents_list = [str(a) for a in agents] if isinstance(agents, list) else None
    scope = str(document.get("scope", "user"))
    force = bool(document.get("force", False))
    return agents_list, scope, force


def skill_install(invocation: Invocation) -> HandlerResult:
    """Install the bundled skill into the requested agent/scope destinations."""
    agents, scope, force = _options(invocation)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return installer.install(agents, scope, force=force, timestamp=stamp), {}


def skill_update(invocation: Invocation) -> HandlerResult:
    """Update installer-owned skill destinations to the bundled version."""
    agents, scope, force = _options(invocation)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return installer.update(agents, scope, force=force, timestamp=stamp), {}


def skill_uninstall(invocation: Invocation) -> HandlerResult:
    """Remove installer-owned skill destinations (modified copies are kept)."""
    agents, scope, _force = _options(invocation)
    return installer.uninstall(agents, scope), {}


def skill_list(invocation: Invocation) -> HandlerResult:
    """List recorded skill installs and whether each is present and intact."""
    return installer.list_(), {}


def skill_path(invocation: Invocation) -> HandlerResult:
    """Show the canonical skill path and the computed destination paths."""
    agents, scope, _force = _options(invocation)
    return installer.path(agents, scope), {}


def skill_show(invocation: Invocation) -> HandlerResult:
    """Print the bundled SKILL.md, or one reference file, as text."""
    from mammoth_cli.errors.envelope import CODE_RESOURCE_NOT_FOUND, EXIT_NOT_FOUND, CliError
    from mammoth_cli.skills import steering

    document = invocation.load_input() or {}
    file = document.get("file")
    try:
        return steering.show(str(file) if file else None), {}
    except FileNotFoundError as exc:
        raise CliError(
            code=CODE_RESOURCE_NOT_FOUND,
            message=f"'{exc}' is not a file of the bundled skill.",
            exit_status=EXIT_NOT_FOUND,
            hint="Paths are relative to the skill directory, e.g. references/recipes/index.md.",
            recovery_commands=["mammoth skill path"],
        ) from exc


def skill_agents_md_install(invocation: Invocation) -> HandlerResult:
    """Write or refresh the <mammoth-cli> steering block in AGENTS.md (or the given path)."""
    from mammoth_cli.skills import steering

    document = invocation.load_input() or {}
    path = document.get("path")
    return steering.install_steering(str(path) if path else None), {}
