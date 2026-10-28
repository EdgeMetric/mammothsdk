"""Read a secret from a file, so it never has to appear on a command line."""

from __future__ import annotations

from pathlib import Path

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError


def read_secret_file(path: str | Path, *, field: str = "password_file") -> str:
    """Read a secret from a text file, without its trailing newline.

    The error messages name the path and the field, never the contents.

    Args:
        path: The file holding the secret.
        field: The input field the path came from, for error messages.

    Returns:
        The file's text with trailing ``\\n`` and ``\\r`` characters removed.

    Raises:
        CliError: When the file cannot be read as UTF-8 text or holds no secret.
    """
    location = Path(path).expanduser()
    try:
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
