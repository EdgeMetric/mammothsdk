"""Resolve authentication and project context for one command invocation.

Authentication requires a login. Credentials come from an explicit secure
input to the current command (a prompt or a permission-checked ``--input``
file), or from the selected or ``--profile`` profile's saved credentials.
There is no environment-variable credential path: ``mammoth auth login`` is the
only way to establish credentials. The API endpoint falls back to the ``app``
default when a profile supplies no server prefix. Project context resolves
separately: ``--project`` overrides the saved profile project id, which
overrides no project at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.context.profiles import ProfileRecord
from mammoth_cli.errors.envelope import (
    CODE_INVALID_WORKSPACE_ID,
    EXIT_AUTH,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation


@dataclass(frozen=True)
class ExplicitLogin:
    """Ad-hoc credentials supplied directly to :func:`resolve_auth`.

    Never populated from an ordinary CLI argument. Only from a secure prompt,
    stdin, or a permission-checked file the caller already validated.

    Attributes:
        api_key: The Mammoth API key.
        api_secret: The Mammoth API secret.
        workspace_id: The Mammoth workspace id.
        server_prefix: A one-label server prefix, or None.
    """

    api_key: str
    api_secret: str
    workspace_id: int
    server_prefix: str | None = None


@dataclass(frozen=True)
class ResolvedAuth:
    """Fully resolved credentials and endpoint for one command invocation.

    Attributes:
        api_key: The Mammoth API key.
        api_secret: The Mammoth API secret.
        workspace_id: The Mammoth workspace id.
        base_url: The resolved API base url.
    """

    api_key: str
    api_secret: str
    workspace_id: int
    base_url: str


def not_authenticated_error() -> CliError:
    """Build the stable error for a command with no available credentials."""
    return CliError(
        code="not_authenticated",
        message="No Mammoth credentials are available for this command.",
        exit_status=EXIT_AUTH,
        hint="Log in first: run 'mammoth auth login' (or 'mammoth auth login --input creds.json').",
        recovery_commands=["mammoth auth login"],
    )


def _require_positive_workspace(workspace_id: int, *, source: str) -> int:
    """Return ``workspace_id`` if positive, else raise ``invalid_workspace_id``.

    A single choke point so every credential source -- environment, explicit
    login, and a saved profile -- rejects a non-positive workspace id, rather
    than only the environment path.

    Args:
        workspace_id: The candidate workspace id.
        source: A short phrase naming where the id came from, for the message.
    """
    if workspace_id <= 0:
        raise CliError(
            code=CODE_INVALID_WORKSPACE_ID,
            message=f"The {source} workspace id must be a positive integer, got {workspace_id}.",
            exit_status=EXIT_USAGE,
        )
    return workspace_id


def _endpoint(server_prefix: str | None) -> str:
    """Resolve one endpoint from a server prefix (default ``app``)."""
    return resolve_base_url(server_prefix)


def resolve_auth(
    invocation: Invocation,
    explicit_login: ExplicitLogin | None = None,
) -> ResolvedAuth:
    """Resolve credentials, workspace id, and base url for one invocation.

    Credentials come from an explicit login (a secure prompt or ``--input``
    document handed to :func:`resolve_auth` by ``auth login``), otherwise from
    the selected or ``--profile`` saved profile. There is no environment
    credential path; ``mammoth auth login`` is the only way to authenticate.

    Args:
        invocation: The current command's resolved global options.
        explicit_login: Ad-hoc credentials that outrank the saved profile.

    Returns:
        A :class:`ResolvedAuth` with the credentials and endpoint to use.

    Raises:
        CliError: ``not_authenticated`` when no source supplies credentials;
            ``invalid_workspace_id`` when the resolved workspace id is not a
            positive integer; endpoint errors from :func:`resolve_base_url`.
    """
    if explicit_login is not None:
        base_url = _endpoint(explicit_login.server_prefix)
        return ResolvedAuth(
            api_key=explicit_login.api_key,
            api_secret=explicit_login.api_secret,
            workspace_id=_require_positive_workspace(
                explicit_login.workspace_id, source="login"
            ),
            base_url=base_url,
        )

    profile_name = invocation.profile or profiles.get_selected()
    record = profiles.get_profile(profile_name)
    if record is not None:
        creds = credentials.load_credentials(profile_name)
        if creds is not None:
            api_key, api_secret = creds
            base_url = _endpoint(record.server_prefix)
            return ResolvedAuth(
                api_key,
                api_secret,
                _require_positive_workspace(record.workspace_id, source="profile"),
                base_url,
            )

    raise not_authenticated_error()


def resolve_project(invocation: Invocation, profile: ProfileRecord | None) -> int | None:
    """Resolve the active project id for one invocation.

    Args:
        invocation: The current command's resolved global options.
        profile: The relevant profile record, or None.

    Returns:
        ``--project`` when given, else the profile's saved project id, else
        None. The caller decides whether a missing project id is fatal.
    """
    if invocation.project is not None:
        return invocation.project
    if profile is not None:
        return profile.project_id
    return None
