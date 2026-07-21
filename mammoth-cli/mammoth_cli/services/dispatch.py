"""Resolve a manifest ``sdk_symbol`` to a bound public SDK method.

Each reviewed command manifest names the exact public SDK method that backs
it, for example ``mammoth.api.projects.ProjectsAPI.list``. This module locates
the sub-client instance on a :class:`mammoth.client.MammothClient` whose class
matches the symbol's penultimate segment and returns the named bound method.
Resolution is by public class name and public method name only; a private
(``_``-prefixed) target is refused, so the CLI can never reach a private SDK
member through the generic dispatch path.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from mammoth_cli.errors.envelope import EXIT_API, CliError


def _unresolved_error(sdk_symbol: str) -> CliError:
    return CliError(
        code="sdk_symbol_unresolved",
        message=f"No public SDK method backs the symbol '{sdk_symbol}'.",
        exit_status=EXIT_API,
        hint="This is an internal manifest/SDK mismatch; please report it.",
        details={"sdk_symbol": sdk_symbol},
    )


def resolve_sdk_method(client: object, sdk_symbol: str) -> Callable[..., Any]:
    """Return the bound public SDK method named by ``sdk_symbol``.

    Args:
        client: The SDK client whose sub-client attributes are searched.
        sdk_symbol: A dotted symbol ``...<ClassName>.<method>`` naming a public
            method on one of the client's sub-clients.

    Returns:
        The bound method ready to call with keyword arguments.

    Raises:
        CliError: ``sdk_symbol_unresolved`` when the symbol is malformed, names
            a class no sub-client provides, targets a private member, or names
            a method the matched sub-client does not expose.
    """
    parts = sdk_symbol.split(".")
    if len(parts) < 2:
        raise _unresolved_error(sdk_symbol)
    class_name, method_name = parts[-2], parts[-1]
    if method_name.startswith("_"):
        raise _unresolved_error(sdk_symbol)

    sub_client = next(
        (
            value
            for value in vars(client).values()
            if type(value).__name__ == class_name
        ),
        None,
    )
    if sub_client is None:
        raise _unresolved_error(sdk_symbol)

    method = getattr(sub_client, method_name, None)
    if method is None or not callable(method):
        raise _unresolved_error(sdk_symbol)
    return cast("Callable[..., Any]", method)
