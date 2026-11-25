"""Handler for ``workflow verify-callback``: a local check of a run callback's signature."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mammoth.workflow_callbacks import DEFAULT_TOLERANCE, callback_problem

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_FIELD,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.secret_files import read_secret_file

CODE_INVALID_SIGNATURE = "invalid_signature"
_FIELDS = ("header", "body_file")
_OPTIONAL_FIELDS = ("secret", "secret_file", "tolerance")


def verify_callback_file(
    header: str,
    body_file: str,
    secret: str | None = None,
    secret_file: str | None = None,
    tolerance: int = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Check a workflow run callback's ``X-Mammoth-Signature`` against the saved body.

    Args:
        header: The ``X-Mammoth-Signature`` header value (``t=...,v1=...``).
        body_file: Path to the request body exactly as received.
        secret: The run's ``callback_secret``.
        secret_file: Path to a file holding the secret, in place of ``secret``.
        tolerance: Most seconds the timestamp may be from now (0 skips the check).

    Returns:
        ``{"valid": bool, "reason": str | None}``.

    Raises:
        CliError: Usage errors: neither or both secrets, a bad tolerance, an unreadable file.
    """
    if (secret is None) == (secret_file is None):
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="Pass exactly one of 'secret' and 'secret_file'.",
            exit_status=EXIT_USAGE,
            hint="Prefer secret_file, so the secret stays out of the shell history.",
        )
    if isinstance(tolerance, bool) or not isinstance(tolerance, int) or tolerance < 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"'tolerance' must be whole seconds, 0 or more, got {tolerance!r}.",
            exit_status=EXIT_USAGE,
        )
    key = secret if secret is not None else read_secret_file(str(secret_file), field="secret_file")
    try:
        body = Path(body_file).expanduser().read_bytes()
    except OSError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"body_file {body_file!r} cannot be read: {type(exc).__name__}.",
            exit_status=EXIT_USAGE,
            details={"field": "body_file", "path": body_file},
        ) from exc
    reason = callback_problem(key, header, body, tolerance=tolerance or None)
    return {"valid": reason is None, "reason": reason}


def workflow_verify_callback(invocation: Invocation) -> HandlerResult:
    """Check a saved workflow run callback's signature locally. Exits non-zero when invalid."""
    document = invocation.load_input() or {}
    missing = [field for field in _FIELDS if not document.get(field)]
    if missing:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{missing[0]}' input field.",
            exit_status=EXIT_USAGE,
        )
    kwargs = {f: document[f] for f in (*_FIELDS, *_OPTIONAL_FIELDS) if f in document}
    data = verify_callback_file(**kwargs)
    if not data["valid"]:
        raise CliError(
            code=CODE_INVALID_SIGNATURE,
            message=f"The callback signature is not valid: {data['reason']}.",
            exit_status=EXIT_API,
            hint=(
                "Check that the body file holds the raw bytes as received, the header is the "
                "X-Mammoth-Signature value, and the secret is that run's callback_secret."
            ),
            details=data,
        )
    return data, {"profile": invocation.profile}
