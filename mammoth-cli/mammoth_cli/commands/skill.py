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
    document = invocation.load_input() or {}
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
