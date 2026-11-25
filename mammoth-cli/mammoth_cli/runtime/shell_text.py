"""Render a command to paste into this platform's shell."""

from __future__ import annotations

import json
import os
import re
import shlex
from typing import Any

WINDOWS = os.name == "nt"
#: What cmd.exe or PowerShell reads as syntax outside double quotes.
_WINDOWS_SYNTAX = re.compile(r"[\s<>|&^(),;=@{}'!]|^$")
#: What one of them still expands or ends on inside double quotes.
_WINDOWS_UNQUOTABLE = re.compile(r'["$`%“”„]')
_ERR_WINDOWS_QUOTE = "no quoting of this holds in both cmd.exe and PowerShell: {0!r}"


def shell_join(arguments: list[str]) -> str:
    """Join arguments into one command line, quoted for this platform's shell.

    Args:
        arguments: The command and its arguments, unquoted.

    Returns:
        The command line: POSIX quoting, or on Windows double quotes.

    Raises:
        ValueError: On Windows, if an argument holds a character that double quotes do not
            protect in both shells, or the command word needs quotes (PowerShell reads a quoted
            first word as a string, not a command).
    """
    if not WINDOWS:
        return shlex.join(arguments)
    words = [_windows_quote(argument) for argument in arguments]
    if words and words[0].startswith('"'):
        raise ValueError(_ERR_WINDOWS_QUOTE.format(arguments[0]))
    return " ".join(words)


def command_with_input(command: list[str], document: dict[str, Any]) -> dict[str, Any]:
    """The result fields that name a command and the ``--input`` document it takes.

    Args:
        command: The command words, without ``--input``.
        document: The document to pass.

    Returns:
        ``next``, ready to paste. JSON cannot be quoted for cmd.exe and PowerShell alike, so on
        Windows ``next`` takes a file and ``next_input`` is the document to put in it.
    """
    if WINDOWS:
        return {"next": f"{shell_join(command)} --input FILE.json", "next_input": document}
    return {"next": shell_join([*command, "--input", json.dumps(document)])}


def _windows_quote(argument: str) -> str:
    if _WINDOWS_UNQUOTABLE.search(argument):
        raise ValueError(_ERR_WINDOWS_QUOTE.format(argument))
    return f'"{argument}"' if _WINDOWS_SYNTAX.search(argument) else argument
