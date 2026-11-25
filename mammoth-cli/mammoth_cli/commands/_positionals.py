"""Positional argument readers shared by command handlers."""

from __future__ import annotations

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation


def require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Parse the positional argument at ``index`` as an int.

    Args:
        invocation: The command invocation.
        index: The argument's position after the command path, from 0.
        name: What the argument is, for the error text.

    Returns:
        The argument as an int.

    Raises:
        CliError: ``missing_argument`` or ``invalid_argument``.
    """
    if len(invocation.extra_args) <= index:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    raw = invocation.extra_args[index]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc
