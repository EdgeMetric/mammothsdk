"""The ``completion`` commands: show or install shell tab-completion.

``completion show`` prints the activation snippet for a shell (deterministic,
side-effect free). ``completion install`` appends that snippet to the shell's
startup file, idempotently, and reports the path. Both resolve the shell from a
positional argument, the ``--input`` ``shell`` field, or the ``$SHELL``
environment variable, and never prompt.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]

# click/Typer complete-var for the ``mammoth`` program.
_COMPLETE_VAR = "_MAMMOTH_COMPLETE"
_SUPPORTED = ("bash", "zsh", "fish")


def _snippet(shell: str) -> str:
    if shell == "fish":
        return f"{_COMPLETE_VAR}=fish_source mammoth | source"
    return f'eval "$({_COMPLETE_VAR}={shell}_source mammoth)"'


def _rc_path(shell: str) -> Path:
    home = Path.home()
    if shell == "bash":
        return home / ".bashrc"
    if shell == "zsh":
        return home / ".zshrc"
    return home / ".config" / "fish" / "config.fish"


def _resolve_shell(invocation: Invocation) -> str:
    document = invocation.load_input() or {}
    candidate = (
        (invocation.extra_args[0] if invocation.extra_args else None)
        or document.get("shell")
        or os.path.basename(os.environ.get("SHELL", ""))
    )
    shell = str(candidate).strip().lower()
    if shell not in _SUPPORTED:
        raise CliError(
            code="unsupported_shell",
            message=f"Cannot generate completion for shell '{candidate or ''}'.",
            exit_status=EXIT_USAGE,
            hint=f"Pass one of: {', '.join(_SUPPORTED)}.",
        )
    return shell


def completion_show(invocation: Invocation) -> HandlerResult:
    """Print the completion activation snippet for a shell."""
    shell = _resolve_shell(invocation)
    return {"shell": shell, "script": _snippet(shell)}, {}


def completion_install(invocation: Invocation) -> HandlerResult:
    """Append the completion snippet to the shell startup file, idempotently."""
    shell = _resolve_shell(invocation)
    snippet = _snippet(shell)
    rc_path = _rc_path(shell)
    rc_path.parent.mkdir(parents=True, exist_ok=True)
    existing = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
    added = snippet not in existing
    if added:
        prefix = "" if existing.endswith("\n") or not existing else "\n"
        with rc_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{prefix}# Mammoth CLI completion\n{snippet}\n")
    return {
        "shell": shell,
        "path": str(rc_path),
        "added": added,
        "detail": "installed" if added else "already present",
    }, {}
