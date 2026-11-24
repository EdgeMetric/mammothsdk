"""Render a command to paste into this platform's shell."""

from __future__ import annotations

import json
import os
import re
import shlex
from typing import Any

WINDOWS = os.name == "nt"
#: What cmd.exe or PowerShell reads as syntax outside double quotes.
_WINDOWS_SYNTAX = re.compile(r"[\s<>|&^(),;=@{}'`$!]|^$")
_ERR_WINDOWS_QUOTE = "no quoting of a double quote holds in both cmd.exe and PowerShell: {0!r}"


def shell_join(arguments: list[str]) -> str:
    """Join arguments into one command line, quoted for this platform's shell.

    Args:
        arguments: The command and its arguments, unquoted.

    Returns:
        The command line: POSIX quoting, or on Windows double quotes.

    Raises:
        ValueError: On Windows, if an argument holds a double quote.
    """
    if not WINDOWS:
        return shlex.join(arguments)
    return " ".join(_windows_quote(argument) for argument in arguments)


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
    if '"' in argument:
        raise ValueError(_ERR_WINDOWS_QUOTE.format(argument))
    return f'"{argument}"' if _WINDOWS_SYNTAX.search(argument) else argument
