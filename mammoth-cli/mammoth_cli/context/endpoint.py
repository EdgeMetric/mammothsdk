"""Resolve the Mammoth API base url from a server prefix.

A server prefix is the only endpoint input the CLI exposes; it maps to
``https://PREFIX.mammoth.io/api/v2`` with default ``app``. There is no
public base-url override: the supported configuration surface is exactly the
API key, API secret, workspace id, and this optional one-label server prefix.
"""

from __future__ import annotations

import re

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

DEFAULT_SERVER_PREFIX = "app"

# One DNS label: 1-63 characters, alphanumeric, internal hyphens only. This
# rejects schemes, dots, slashes, query strings, fragments, ports, and
# whitespace by construction.
_DNS_LABEL_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def invalid_server_prefix_error(prefix: str) -> CliError:
    """Build the stable error for a malformed server prefix.

    Args:
        prefix: The rejected candidate prefix.

    Returns:
        A ``invalid_server_prefix`` :class:`CliError` (exit status 2).
    """
    return CliError(
        code="invalid_server_prefix",
        message=f"'{prefix}' is not a valid server prefix.",
        exit_status=EXIT_USAGE,
        hint="Use one DNS label, for example 'app'.",
    )


def resolve_base_url(server_prefix: str | None) -> str:
    """Resolve the API base url from a server prefix.

    Args:
        server_prefix: A one-label server prefix (for example ``"app"``),
            or None to use the default ``app``.

    Returns:
        The resolved API base url.

    Raises:
        CliError: ``invalid_server_prefix`` when the prefix is not one valid
            DNS label.
    """
    prefix = server_prefix if server_prefix is not None else DEFAULT_SERVER_PREFIX
    if not _DNS_LABEL_RE.match(prefix):
        raise invalid_server_prefix_error(prefix)
    return f"https://{prefix}.mammoth.io/api/v2"
