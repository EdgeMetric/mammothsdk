"""Resolve authentication and project context for one command invocation.

Precedence, per the product contract: explicit secure input to the current
command, then environment variables, then the selected or ``--profile``
profile's saved credentials. The API endpoint additionally falls back to the
``app-eu`` default when nothing supplies a server prefix. Project context
resolves separately: ``--project`` overrides the saved profile project id,
which overrides no project at all.

Environment authentication is all-or-nothing: the three credential variables
(:data:`ENV_API_KEY`, :data:`ENV_API_SECRET`, :data:`ENV_WORKSPACE_ID`) are
only honoured when *all three* are present. Supplying only some of them is a
misconfiguration that raises ``incomplete_environment_auth`` rather than
silently falling back to a saved profile — falling back could operate in a
different workspace than the partial environment implied.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.context.profiles import ProfileRecord
from mammoth_cli.errors.envelope import (
    CODE_INCOMPLETE_ENVIRONMENT_AUTH,
    CODE_INVALID_WORKSPACE_ID,
    EXIT_AUTH,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation

ENV_API_KEY = "MAMMOTH_API_KEY"
# This constant holds the *name* of the secret environment variable, not a
# secret value. The annotation and noqa keep static secret-scanners honest.
ENV_API_SECRET: str = "MAMMOTH_API_SECRET"  # noqa: S105
ENV_WORKSPACE_ID = "MAMMOTH_WORKSPACE_ID"
ENV_SERVER_PREFIX = "MAMMOTH_SERVER_PREFIX"

# The environment credential variables, in canonical order. Environment
# authentication requires every one of these; a partial set is rejected.
ENV_CREDENTIAL_VARS = (ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID)


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
        hint="Log in, or set MAMMOTH_API_KEY, MAMMOTH_API_SECRET, and MAMMOTH_WORKSPACE_ID.",
        recovery_commands=["mammoth auth login"],
    )


def _incomplete_environment_auth_error(missing: list[str]) -> CliError:
    """Build the stable error for a partial environment credential set.

    Args:
        missing: The credential variable names that are absent, in canonical
            order (:data:`ENV_CREDENTIAL_VARS`).
    """
    return CliError(
        code=CODE_INCOMPLETE_ENVIRONMENT_AUTH,
        message=(
            "Incomplete Mammoth environment authentication: set "
            "MAMMOTH_API_KEY, MAMMOTH_API_SECRET, and MAMMOTH_WORKSPACE_ID "
            "together, or set none of them and use a saved profile."
        ),
        exit_status=EXIT_AUTH,
        hint=f"Missing environment variable(s): {', '.join(missing)}.",
        details={"missing": missing},
    )


def _invalid_workspace_env_error(raw: str) -> CliError:
    return CliError(
        code=CODE_INVALID_WORKSPACE_ID,
        message=f"MAMMOTH_WORKSPACE_ID='{raw}' is not a positive integer.",
        exit_status=EXIT_USAGE,
    )


def _endpoint(server_prefix: str | None) -> str:
    """Resolve one endpoint from a server prefix (default ``app-eu``)."""
    return resolve_base_url(server_prefix)


def resolve_auth(
    invocation: Invocation,
    env: Mapping[str, str] | None = None,
    explicit_login: ExplicitLogin | None = None,
) -> ResolvedAuth:
    """Resolve credentials, workspace id, and base url for one invocation.

    Args:
        invocation: The current command's resolved global options.
        env: Environment mapping to read (defaults to ``os.environ``). Kept as
            a parameter so callers never depend on process-global state.
        explicit_login: Ad-hoc credentials that outrank every other source.

    Returns:
        A :class:`ResolvedAuth` with the credentials and endpoint to use.

    Raises:
        CliError: ``incomplete_environment_auth`` when some but not all of the
            three environment credential variables are set;
            ``not_authenticated`` when no source supplies credentials;
            ``invalid_workspace_id`` when ``MAMMOTH_WORKSPACE_ID`` is not a
            positive integer; endpoint errors from :func:`resolve_base_url`.
    """
    environment = env if env is not None else os.environ

    if explicit_login is not None:
        base_url = _endpoint(explicit_login.server_prefix)
        return ResolvedAuth(
            api_key=explicit_login.api_key,
            api_secret=explicit_login.api_secret,
            workspace_id=explicit_login.workspace_id,
            base_url=base_url,
        )

    # Environment authentication is all-or-nothing. If the caller supplied ANY
    # of the three credential variables, they must supply all three; a partial
    # set must never silently fall back to a saved profile (which could operate
    # in a different workspace than the partial environment implied).
    env_values = {name: environment.get(name) for name in ENV_CREDENTIAL_VARS}
    if any(env_values.values()):
        missing = [name for name in ENV_CREDENTIAL_VARS if not env_values[name]]
        if missing:
            raise _incomplete_environment_auth_error(missing)
        env_key = env_values[ENV_API_KEY]
        env_secret = env_values[ENV_API_SECRET]
        env_workspace = env_values[ENV_WORKSPACE_ID]
        assert env_key is not None and env_secret is not None and env_workspace is not None
        try:
            workspace_id = int(env_workspace)
        except ValueError as exc:
            raise _invalid_workspace_env_error(env_workspace) from exc
        if workspace_id <= 0:
            raise _invalid_workspace_env_error(env_workspace)
        base_url = _endpoint(environment.get(ENV_SERVER_PREFIX))
        return ResolvedAuth(env_key, env_secret, workspace_id, base_url)

    profile_name = invocation.profile or profiles.get_selected()
    record = profiles.get_profile(profile_name)
    if record is not None:
        creds = credentials.load_credentials(profile_name)
        if creds is not None:
            api_key, api_secret = creds
            base_url = _endpoint(record.server_prefix)
            return ResolvedAuth(api_key, api_secret, record.workspace_id, base_url)

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
