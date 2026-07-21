"""Build an authenticated service and resolve project context for a handler.

A networked command handler receives only an
:class:`~mammoth_cli.runtime.invocation.Invocation`. It calls
:func:`open_service` to obtain a closed-on-exit
:class:`~mammoth_cli.services.protocol.MammothService` bound to the resolved
credentials, and :func:`require_project` / :func:`resolved_project` for the
active project id. Tests substitute the service by monkeypatching
:func:`mammoth_cli.services.factory.build_service`; nothing here touches the
network directly.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from mammoth_cli.context import profiles
from mammoth_cli.context.resolver import ResolvedAuth, resolve_auth, resolve_project
from mammoth_cli.errors.envelope import missing_project_error
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory
from mammoth_cli.services.protocol import MammothService


@contextmanager
def open_service(invocation: Invocation) -> Iterator[tuple[MammothService, ResolvedAuth]]:
    """Yield an authenticated service and the resolved auth, closing on exit.

    Args:
        invocation: The current command's resolved global options.

    Yields:
        A ``(service, auth)`` pair; the service is closed when the block exits.

    Raises:
        CliError: From authentication resolution when no credentials are
            available or the endpoint cannot be resolved.
    """
    auth = resolve_auth(invocation)
    service = factory.build_service(
        auth, timeout=invocation.timeout, project_id=resolved_project(invocation)
    )
    try:
        yield service, auth
    finally:
        service.close()


def resolved_project(invocation: Invocation) -> int | None:
    """Return the active project id for ``invocation`` (``--project`` or profile).

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The resolved project id, or None when none is set.
    """
    profile_name = invocation.profile or profiles.get_selected()
    return resolve_project(invocation, profiles.get_profile(profile_name))


def require_project(invocation: Invocation) -> int:
    """Return the active project id, or raise a stable ``project_required`` error.

    Args:
        invocation: The current command's resolved global options.

    Returns:
        The resolved positive project id.

    Raises:
        CliError: ``project_required`` when no project id is set.
    """
    project_id = resolved_project(invocation)
    if project_id is None:
        raise missing_project_error()
    return project_id
