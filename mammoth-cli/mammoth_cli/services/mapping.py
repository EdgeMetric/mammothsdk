"""Map raw Mammoth SDK exceptions to the stable CLI error envelope.

Every SDK exception a service method can raise passes through
:func:`map_sdk_exception` before it reaches a command, so the CLI never
renders a Python traceback or SDK-specific message shape to an agent.
"""

from __future__ import annotations

from mammoth.exceptions import MammothAPIError, MammothAuthError, MammothError

from mammoth_cli.errors.envelope import (
    EXIT_API,
    EXIT_AUTH,
    EXIT_NOT_FOUND,
    EXIT_RETRYABLE,
    CliError,
)

_RETRYABLE_MESSAGE_HINTS = ("timeout", "connection error", "request error")


def map_sdk_exception(exc: Exception) -> CliError:
    """Translate one SDK exception into a stable :class:`CliError`.

    Args:
        exc: The exception raised by a public SDK call.

    Returns:
        A :class:`CliError` with a mapped code and exit status:
        ``authentication_failed`` (exit 4) for invalid credentials,
        ``resource_not_found`` (exit 5) for a 404 response,
        ``retryable_error`` (exit 7) for a network or timeout failure, and
        ``api_error`` (exit 1) for every other API or SDK error.
    """
    if isinstance(exc, MammothAuthError):
        return CliError(
            code="authentication_failed",
            message="Mammoth rejected the provided credentials.",
            exit_status=EXIT_AUTH,
            hint="Check the API key, secret, and workspace id.",
            recovery_commands=["mammoth auth login"],
        )
    if isinstance(exc, MammothAPIError):
        status = exc.status_code
        message = str(exc)
        if status == 404:
            return CliError(
                code="resource_not_found",
                message="The requested Mammoth resource does not exist.",
                exit_status=EXIT_NOT_FOUND,
                hint="Check the resource id.",
            )
        lowered = message.lower()
        if status is None and any(hint in lowered for hint in _RETRYABLE_MESSAGE_HINTS):
            return CliError(
                code="retryable_error",
                message="A network or timeout error occurred while calling Mammoth.",
                exit_status=EXIT_RETRYABLE,
                hint="Retry the command.",
                retryable=True,
            )
        return CliError(
            code="api_error",
            message=message,
            exit_status=EXIT_API,
            details={"status_code": status} if status is not None else {},
        )
    if isinstance(exc, MammothError):
        return CliError(code="api_error", message=str(exc), exit_status=EXIT_API)
    return CliError(code="api_error", message=str(exc), exit_status=EXIT_API, retryable=True)
