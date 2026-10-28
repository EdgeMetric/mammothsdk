"""Read a secret from a file, so it never has to appear on a command line."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError


def refuse_shared_file(path: Path) -> None:
    """Reject a file holding a secret that group or other users can read.

    Args:
        path: The file path.

    Raises:
        CliError: ``insecure_input_file`` on POSIX when the file is group- or
            other-readable.
    """
    if os.name != "posix":
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise CliError(
            code="insecure_input_file",
            message=f"'{path}' is readable by group or other users.",
            exit_status=EXIT_USAGE,
            hint=f"Restrict its permissions, for example: chmod 600 {path}",
        )


def read_secret_file(path: str | Path, *, field: str = "password_file") -> str:
    """Read a secret from a text file, without its trailing newline.

    The error messages name the path and the field, never the contents.

    Args:
        path: The file holding the secret.
        field: The input field the path came from, for error messages.

    Returns:
        The file's text with trailing ``\\n`` and ``\\r`` characters removed.

    Raises:
        CliError: When the file cannot be read as UTF-8 text, holds no secret, or is
            readable by group or other users (``insecure_input_file``).
    """
    location = Path(path).expanduser()
    try:
        refuse_shared_file(location)
        text = location.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"{field} {str(path)!r} cannot be read: {type(exc).__name__}.",
            exit_status=EXIT_USAGE,
            hint=f"Put the secret in a text file and pass its path as {field}.",
            details={"field": field, "path": str(path)},
        ) from exc
    secret = text.rstrip("\r\n")
    if not secret:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"{field} {str(path)!r} is empty.",
            exit_status=EXIT_USAGE,
            hint=f"Write the secret into the file named by {field}.",
            details={"field": field, "path": str(path)},
        )
    return secret
