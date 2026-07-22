"""Resolve the Mammoth API base url from a server prefix or an expert override.

A server prefix is the only endpoint input most users need; it maps to
``https://PREFIX.mammoth.io/api/v2`` with default ``app-eu``. An expert
``base-url`` is a separate, non-authentication runtime override for custom
deployments. A profile or command cannot set both at once.
"""

from __future__ import annotations

import re

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

DEFAULT_SERVER_PREFIX = "app-eu"

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
        hint="Use one DNS label, for example 'app-eu'.",
    )


def conflicting_endpoint_error() -> CliError:
    """Build the stable error for a server-prefix/base-url conflict.

    Returns:
        A ``conflicting_endpoint`` :class:`CliError` (exit status 2).
    """
    return CliError(
        code="conflicting_endpoint",
        message="A profile or command cannot set both --server-prefix and --base-url.",
        exit_status=EXIT_USAGE,
        hint="Pass only one of --server-prefix or --base-url.",
    )


def resolve_base_url(server_prefix: str | None, base_url: str | None) -> str:
    """Resolve the API base url from a server prefix or an expert base url.

    Args:
        server_prefix: A one-label server prefix (for example ``"app-eu"``),
            or None to use the default.
        base_url: An expert base-url override, or None.

    Returns:
        The resolved API base url.

    Raises:
        CliError: ``conflicting_endpoint`` when both arguments are given;
            ``invalid_server_prefix`` when the prefix is not one valid DNS
            label.
    """
    if server_prefix is not None and base_url is not None:
        raise conflicting_endpoint_error()
    if base_url is not None:
        return base_url
    prefix = server_prefix if server_prefix is not None else DEFAULT_SERVER_PREFIX
    if not _DNS_LABEL_RE.match(prefix):
        raise invalid_server_prefix_error(prefix)
    return f"https://{prefix}.mammoth.io/api/v2"
