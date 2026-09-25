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

import sys
from collections.abc import Iterator
from contextlib import contextmanager

from mammoth_cli.context import profiles
from mammoth_cli.context.resolver import ResolvedAuth, resolve_auth, resolve_project
from mammoth_cli.errors.envelope import missing_project_error
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.policy import resolve_policy
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory
from mammoth_cli.services.protocol import MammothService

#: Job-wait budget for commands that start work on the platform (uploads,
#: transforms, exports, deletes). The SDK's 60 s default fits a read; a
#: transform on a real dataset regularly needs more, and agents were told to
#: pass ``--timeout 300`` by hand. Reads keep the SDK default.
DEFAULT_MUTATION_JOB_TIMEOUT = 300.0


def default_job_timeout(command_id: str) -> float | None:
    """The job-wait timeout for ``command_id`` when none was configured."""
    record = command_by_id(command_id) or {}
    if record.get("mutation_class", "read") in (None, "read"):
        return None
    if record.get("wait_policy") in ("always_wait", "start_or_wait", "returns_job"):
        return DEFAULT_MUTATION_JOB_TIMEOUT
    return None


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
    # The spinner renders on stderr, so gate it on stderr being a terminal
    # (stdout may be piped while stderr is still a tty).
    policy = resolve_policy(
        output=invocation.output,
        no_input=invocation.no_input,
        no_progress=invocation.no_progress,
        is_tty=sys.stderr.isatty(),
        color=invocation.color,
    )
    service = factory.build_service(
        auth,
        timeout=invocation.timeout,
        job_timeout=(
            invocation.job_timeout
            if invocation.job_timeout is not None
            else default_job_timeout(invocation.command_id)
        ),
        pipeline_timeout=invocation.pipeline_timeout,
        project_id=resolved_project(invocation),
        profile=invocation.profile or profiles.get_selected(),
        progress=not policy.progress_disabled,
    )
    if invocation.dry_run:
        # The production service exposes the gate; a test double may not, and
        # then the dry run is simply the double's own behaviour.
        if hasattr(service, "gate"):
            from mammoth_cli.runtime.dryrun import make_gate

            service.gate = make_gate(invocation.command_id)
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
    if embedded.active():
        # An embedded call has no profile: the host's saved profiles belong to
        # the host's OS user, not to the user the call runs for.
        return invocation.project
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
