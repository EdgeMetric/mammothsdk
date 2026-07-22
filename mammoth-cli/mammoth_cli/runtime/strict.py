"""Strict argument and input validation shared by every command.

The generic Typer leaf accepts unknown options and surplus positionals so that
handlers can read their own positionals from ``ctx.args``. That permissiveness
must not reach the user: a misspelled option or an unknown request-document key
has to fail loudly instead of being silently ignored.

This module centralizes two checks, both driven by the command's reviewed
backing SDK signature (see :mod:`mammoth_cli.services.argspec`):

* :func:`validate_extra_args` rejects any trailing token that looks like an
  option — the generic leaf never declares command-specific options, so any
  ``-``/``--`` token in ``ctx.args`` is by definition unrecognized.
* :func:`validate_input_fields` rejects any ``--input`` document key the
  backing method cannot accept.

Both no-op when the command has no resolvable signature, so bespoke and
not-yet-backed commands keep their prior behavior rather than being guessed at.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.argspec import accepted_field_names

_OPTION_PREFIX = "-"


def _sdk_symbol(command_id: str) -> str | None:
    """Return the backing SDK symbol for a command id, or None if unrecorded."""
    record = command_by_id(command_id)
    if record is None:
        return None
    symbol = record.get("sdk_symbol")
    return str(symbol) if symbol else None


def validate_extra_args(command_id: str, extra_args: Iterable[str]) -> None:
    """Reject trailing tokens that are unrecognized options.

    Args:
        command_id: The manifest command id being invoked.
        extra_args: The trailing tokens Typer collected for the command.

    Raises:
        CliError: ``unknown_option`` with :data:`EXIT_USAGE` when a token begins
            with ``-`` (and is not the bare ``-`` stdin sentinel), since the
            generic leaf declares no command-specific options for it to match.
    """
    for token in extra_args:
        if token.startswith(_OPTION_PREFIX) and token != _OPTION_PREFIX:
            raise CliError(
                code="unknown_option",
                message=f"Unknown option '{token}' for '{command_id.replace('.', ' ')}'.",
                exit_status=EXIT_USAGE,
                hint="Check the command schema with 'mammoth schema get'.",
                details={"option": token},
            )


def validate_input_fields(command_id: str, document: dict[str, Any] | None) -> None:
    """Reject ``--input`` document keys the backing SDK method cannot accept.

    Args:
        command_id: The manifest command id being invoked.
        document: The parsed ``--input`` mapping, or None when none was given.

    Raises:
        CliError: ``unknown_input_field`` with :data:`EXIT_USAGE` when a key is
            not a parameter of the command's backing method. No-op when the
            command has no resolvable signature or the method accepts arbitrary
            keyword arguments.
    """
    if not document:
        return
    symbol = _sdk_symbol(command_id)
    if symbol is None:
        return
    accepted = accepted_field_names(symbol)
    if accepted is None:
        return
    unknown = sorted(key for key in document if key not in accepted)
    if unknown:
        raise CliError(
            code="unknown_input_field",
            message=(
                f"Unknown input field(s) for '{command_id.replace('.', ' ')}': "
                f"{', '.join(unknown)}."
            ),
            exit_status=EXIT_USAGE,
            hint=f"Accepted fields: {', '.join(sorted(accepted)) or '(none)'}.",
            details={"unknown": unknown, "accepted": sorted(accepted)},
        )
