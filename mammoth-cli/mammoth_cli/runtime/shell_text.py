"""Render an argument list as a command to paste into this platform's shell."""

from __future__ import annotations

import os
import re
import shlex
import subprocess

WINDOWS = os.name == "nt"
#: What cmd.exe or PowerShell reads as syntax outside quotes; ``list2cmdline`` quotes only spaces.
_WINDOWS_SYNTAX = re.compile(r"[<>|&^(),;=@{}']")


def shell_join(arguments: list[str]) -> str:
    """Join arguments into one command line, quoted for this platform's shell.

    Args:
        arguments: The command and its arguments, unquoted.

    Returns:
        The command line: POSIX quoting, or on Windows double quotes.
    """
    if not WINDOWS:
        return shlex.join(arguments)
    return " ".join(_windows_quote(argument) for argument in arguments)


def _windows_quote(argument: str) -> str:
    quoted = subprocess.list2cmdline([argument])
    if quoted.startswith('"') or not _WINDOWS_SYNTAX.search(argument):
        return quoted
    return f'"{quoted}"'
