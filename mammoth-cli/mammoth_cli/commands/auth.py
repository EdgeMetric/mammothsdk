"""Bespoke `auth` command family: login, status, logout.

Authentication has exactly three required inputs (API key, API secret,
workspace id) and one optional input (server prefix, default ``app``).
Authentication always requires a login; there is no environment credential
path. These commands never accept a secret as an ordinary command-line value:
the API key and secret come from a hidden TTY prompt or a permission-checked
JSON/YAML login document read through the shared ``--input`` option.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import Any, cast

import typer
from pydantic import ValidationError

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.context.resolver import (
    ResolvedAuth,
    resolve_auth,
)
from mammoth_cli.contracts.auth import LoginRequest
from mammoth_cli.errors.envelope import (
    CODE_AUTHENTICATION_FAILED,
    CODE_CONFIRMATION_DECLINED,
    CODE_CONFIRMATION_REQUIRED,
    CODE_INVALID_WORKSPACE_ID,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.policy import MACHINE_OUTPUTS
from mammoth_cli.runtime import executor
from mammoth_cli.runtime import options as go
from mammoth_cli.runtime.input_loader import load_input_document
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory as service_factory

_STORAGE_MODES = ("auto", "keyring", "file")


def _check_file_permissions(path: Path) -> None:
    """Reject a login document readable by group or other users.

    Args:
        path: The document path.

    Raises:
        CliError: ``insecure_input_file`` on POSIX when the file is group- or
            other-readable.
    """
    if os.name != "posix":
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise CliError(
            code="insecure_input_file",
            message=f"'{path}' is readable by group or other users.",
            exit_status=EXIT_USAGE,
            hint=f"Restrict its permissions, for example: chmod 600 {path}",
        )


def _preflight_login_input(path_or_dash: str | None) -> None:
    """Check a credential file before any specialized parser reads it."""
    if path_or_dash is None or path_or_dash == "-" or path_or_dash.lstrip().startswith("{"):
        return
    path = Path(path_or_dash)
    if not path.exists():
        raise CliError(
            code="input_file_not_found",
            message=f"'{path}' does not exist.",
            exit_status=EXIT_USAGE,
        )
    _check_file_permissions(path)


def _load_login_document(path_or_dash: str, input_format: str | None) -> dict[str, Any]:
    """Read and parse the `auth login --input` document.

    Args:
        path_or_dash: A file path, or ``"-"`` for stdin.
        input_format: ``"json"`` or ``"yaml"``; required for stdin, otherwise
            detected from the file suffix when omitted.

    Returns:
        The parsed document as a plain dict.

    Raises:
        CliError: On a missing file, an insecure file, a missing
            ``--input-format`` for stdin, an unsupported format, or a
            document that does not parse to an object.
    """
    _preflight_login_input(path_or_dash)
    loaded = load_input_document(path_or_dash, input_format)
    # ``load_input_document`` already enforces a mapping top-level shape.  Keep
    # this assertion as a typed seam for the bespoke LoginRequest validator.
    assert loaded is not None
    return loaded


def _validate_login_document(document: dict[str, Any]) -> LoginRequest:
    """Validate a raw login document against :class:`LoginRequest`.

    Args:
        document: The parsed document.

    Returns:
        The validated :class:`LoginRequest`.

    Raises:
        CliError: ``invalid_login_document`` with sanitized (secret-free)
            field errors.
    """
    try:
        return LoginRequest.model_validate(document)
    except ValidationError as exc:
        errors = [
            {"loc": ".".join(str(part) for part in error["loc"]), "type": error["type"]}
            for error in exc.errors()
        ]
        raise CliError(
            code="invalid_login_document",
            message="The login request document failed validation.",
            exit_status=EXIT_USAGE,
            details={"errors": errors},
        ) from exc


def _masked_receipt(value: str) -> str:
    """Describe a secret without revealing it: its length and last four characters."""
    if len(value) <= 4:
        return f"{len(value)} characters"
    return f"{len(value)} characters, ending in …{value[-4:]}"


def _prompt_secret(label: str) -> str:
    """Prompt for one secret with hidden input, then confirm what was captured.

    A hidden prompt shows nothing while typing, so a paste that silently
    carried a newline or trailing space, or an empty return, used to surface
    only later as an opaque 401. Surrounding whitespace is stripped, an empty
    entry is rejected here, and a masked receipt (length and last four
    characters, never the value) is printed to stderr as feedback.
    """
    value = typer.prompt(label, hide_input=True).strip()
    if not value:
        raise CliError(
            code="login_input_required",
            message=f"The {label} was empty.",
            exit_status=EXIT_USAGE,
            hint=f"Paste the {label} at the hidden prompt; nothing is echoed while you type.",
        )
    typer.echo(f"  {label}: {_masked_receipt(value)}", err=True)
    return str(value)


def _prompt_blockers(invocation: Invocation) -> list[str]:
    """Reasons this invocation cannot interactively prompt, in report order.

    Mirrors the ``can_prompt`` rule used by
    :func:`mammoth_cli.runtime.confirm.enforce_confirmation` — a real TTY,
    without ``--no-input`` and not a machine output format. A genuine
    interactive terminal is ground truth for "a human is present," so it
    intentionally does NOT consult the ``CI``/``TERM=dumb`` heuristic: those
    only proxy for the absence of a human, which a real TTY disproves. Returns
    an empty list when prompting is possible.
    """
    reasons: list[str] = []
    if not sys.stdin.isatty():
        reasons.append("stdin is not an interactive terminal")
    if invocation.no_input:
        reasons.append("--no-input is set")
    if invocation.output in MACHINE_OUTPUTS:
        reasons.append(f"--output {invocation.output} is a machine format")
    return reasons


def _run_login(
    invocation: Invocation,
    *,
    server_prefix: str | None,
    storage: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate, connection-check, and persist one `auth login` invocation."""
    if storage not in _STORAGE_MODES:
        raise CliError(
            code="invalid_storage_mode",
            message=f"'{storage}' is not a valid --storage value.",
            exit_status=EXIT_USAGE,
            hint=f"Use one of: {', '.join(_STORAGE_MODES)}.",
        )

    blockers = _prompt_blockers(invocation)

    effective_workspace: int | None
    if invocation.input_file is not None:
        # The permission check is deliberately separate from parsing so a
        # secret-bearing file is rejected before any bytes are read.  The
        # shared loader then performs the one bounded source read and strict
        # JSON/YAML admission used by every other command.
        _preflight_login_input(invocation.input_file)
        document = load_input_document(invocation.input_file, invocation.input_format)
        assert document is not None
        request = _validate_login_document(document)
        api_key, api_secret = request.api_key, request.api_secret
        effective_workspace = request.workspace_id
        effective_prefix = server_prefix if server_prefix is not None else request.server_prefix
    elif not blockers:
        # Two flows, nothing else: a terminal prompts for everything (key,
        # secret, then workspace id), and non-interactive uses --input. The
        # workspace is asked last, after the credentials.
        api_key = _prompt_secret("API key")
        api_secret = _prompt_secret("API secret")
        effective_workspace = typer.prompt("Workspace id", type=int)
        effective_prefix = server_prefix
    else:
        raise CliError(
            code="login_input_required",
            message="Non-interactive login requires --input.",
            exit_status=EXIT_USAGE,
            hint=(
                "Interactive prompting is off because "
                + "; ".join(blockers)
                + ". Pass --input FILE|- (with --input-format for stdin), "
                "or run in an interactive terminal."
            ),
        )

    if effective_workspace is None or effective_workspace <= 0:
        raise CliError(
            code=CODE_INVALID_WORKSPACE_ID,
            message="A positive --workspace id is required.",
            exit_status=EXIT_USAGE,
        )
    if not api_key or not api_secret:
        raise CliError(
            code="invalid_credentials",
            message="The API key and secret must be non-empty.",
            exit_status=EXIT_USAGE,
        )

    resolved_base_url = resolve_base_url(effective_prefix)

    resolved_auth = ResolvedAuth(
        api_key=api_key,
        api_secret=api_secret,
        workspace_id=effective_workspace,
        base_url=resolved_base_url,
    )
    service = service_factory.build_service(resolved_auth, timeout=invocation.timeout)
    try:
        service.check_connection()
    except CliError as exc:
        if exc.code == CODE_AUTHENTICATION_FAILED:
            # Say exactly what was tried, without the secret: the endpoint,
            # the workspace, and a masked receipt of the key. Credentials are
            # per environment, and a release key typed at a production login
            # is the common cause of an otherwise opaque 401.
            exc.details = {
                **exc.details,
                "endpoint_base_url": resolved_base_url,
                "workspace_id": effective_workspace,
                # Receipts only (length and last four characters). The output
                # layer redacts any key that looks like a credential, so these
                # are named for what they are: descriptions, not values.
                "credential_receipt": {
                    "key": _masked_receipt(api_key),
                    "second_value_length": len(api_secret),
                },
            }
            exc.hint = (
                f"{resolved_base_url} rejected this key/secret for workspace "
                f"{effective_workspace}. Credentials are per environment: a key issued on "
                "one Mammoth server does not authenticate on another. Check the key, the "
                "secret, the workspace id, and that --server-prefix matches where the key "
                "was issued."
            )
        raise
    finally:
        service.close()

    profile_name = invocation.profile or profiles.DEFAULT_PROFILE_NAME
    profiles.validate_profile_name(profile_name)
    existing = profiles.get_profile(profile_name)
    record = profiles.ProfileRecord(
        name=profile_name,
        workspace_id=effective_workspace,
        server_prefix=effective_prefix,
        project_id=existing.project_id if existing is not None else None,
    )
    # Persist the record and the selection pointer in one write, before the
    # secret goes to its store: a stored secret with no readable record is the
    # "credentials present / no profile" state that strands a later doctor run.
    profiles.save_profile(record, select=True)
    storage_used = credentials.store_credentials(
        profile_name,
        api_key,
        api_secret,
        storage=cast(credentials.StorageMode, storage),
        interactive=not blockers,
    )

    data = {
        "profile": profile_name,
        "workspace_id": effective_workspace,
        "base_url": resolved_base_url,
        "storage": storage_used,
    }
    return data, {"profile": profile_name, "workspace_id": effective_workspace}


def auth_login(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    timeout: float | None = go.timeout_option(),
    job_timeout: float | None = go.job_timeout_option(),
    pipeline_timeout: float | None = go.pipeline_timeout_option(),
    color: str = go.color_option(),
    no_input: bool = go.no_input_option(),
    no_progress: bool = go.no_progress_option(),
    debug: bool = go.debug_option(),
    input_file: str | None = go.input_file_option(),
    input_format: str | None = go.input_format_option(),
    server_prefix: str | None = typer.Option(
        None, "--server-prefix", help="Server prefix (one DNS label). Default 'app'."
    ),
    storage: str = typer.Option(
        "auto", "--storage", help="Credential storage backend.", metavar="auto|keyring|file"
    ),
) -> None:
    """Log in and store one profile's credentials.

    Prompts for the API key and secret in a terminal. For non-interactive use
    (agents, CI), pass ``--input FILE`` with a login document instead.
    Performs a lightweight connection check before saving anything; a failed
    check leaves existing profile state unchanged.
    """
    invocation = go.make_invocation(
        "auth.login",
        output=output,
        profile=profile,
        project=project,
        timeout=timeout,
        job_timeout=job_timeout,
        pipeline_timeout=pipeline_timeout,
        color=color,
        no_input=no_input,
        no_progress=no_progress,
        debug=debug,
        input_file=input_file,
        input_format=input_format,
        input_preflight=_preflight_login_input,
    )

    def producer() -> tuple[Any, dict[str, Any]]:
        # Run the secret-safe preflight inside the shared executor boundary;
        # the specialized login loader then performs its one actual read.
        invocation.prepare_input()
        return _run_login(
            invocation,
            server_prefix=server_prefix,
            storage=storage,
        )

    executor.run(
        invocation.command_id,
        invocation.output,
        producer,
        agent_mode=invocation.no_input,
        invocation=invocation,
    )


def _run_status(invocation: Invocation, *, check: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    """Report local (or, with `--check`, live) authentication state."""
    profile_name = invocation.profile or profiles.get_selected()
    record = profiles.get_profile(profile_name)
    has_creds = credentials.has_credentials(profile_name)

    if record is not None:
        endpoint = resolve_base_url(record.server_prefix)
        workspace_id: int | None = record.workspace_id
    else:
        endpoint = resolve_base_url(None)
        workspace_id = None

    data: dict[str, Any] = {
        "profile": profile_name,
        "workspace_id": workspace_id,
        "endpoint": endpoint,
        "has_credentials": has_creds,
        "checked": False,
        "connected": None,
    }

    if check:
        auth = resolve_auth(invocation)
        service = service_factory.build_service(auth, timeout=invocation.timeout)
        try:
            service.check_connection()
            data["connected"] = True
        finally:
            service.close()
        data["checked"] = True

    return data, {"profile": profile_name, "workspace_id": workspace_id}


def auth_status(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    timeout: float | None = go.timeout_option(),
    job_timeout: float | None = go.job_timeout_option(),
    pipeline_timeout: float | None = go.pipeline_timeout_option(),
    color: str = go.color_option(),
    no_input: bool = go.no_input_option(),
    no_progress: bool = go.no_progress_option(),
    debug: bool = go.debug_option(),
    input_file: str | None = go.input_file_option(),
    input_format: str | None = go.input_format_option(),
    check: bool = typer.Option(False, "--check", help="Perform a live connection check."),
) -> None:
    """Report local authentication state for one profile.

    Makes no network call unless `--check` is given.
    """
    invocation = go.make_invocation(
        "auth.status",
        output=output,
        profile=profile,
        project=project,
        timeout=timeout,
        job_timeout=job_timeout,
        pipeline_timeout=pipeline_timeout,
        color=color,
        no_input=no_input,
        no_progress=no_progress,
        debug=debug,
        input_file=input_file,
        input_format=input_format,
    )

    def producer() -> tuple[Any, dict[str, Any]]:
        return _run_status(invocation, check=check)

    executor.run(
        invocation.command_id,
        invocation.output,
        producer,
        agent_mode=invocation.no_input,
        invocation=invocation,
    )


def _run_logout(
    invocation: Invocation, *, all_profiles: bool, yes: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove one profile's (or every profile's) stored credentials."""
    if all_profiles and invocation.profile is not None:
        raise CliError(
            code="invalid_argument_combination",
            message="--all and --profile are mutually exclusive.",
            exit_status=EXIT_USAGE,
        )

    if not yes:
        blockers = _prompt_blockers(invocation)
        if blockers:
            raise CliError(
                code=CODE_CONFIRMATION_REQUIRED,
                message="auth logout requires --yes in non-interactive mode.",
                exit_status=EXIT_USAGE,
                hint=(
                    "Interactive confirmation is off because "
                    + "; ".join(blockers)
                    + ". Re-run with --yes, or run in an interactive terminal."
                ),
            )
        if not typer.confirm("Remove the stored credentials?", default=False):
            raise CliError(
                code=CODE_CONFIRMATION_DECLINED,
                message="Logout was not confirmed.",
                exit_status=EXIT_USAGE,
            )

    removed: list[str] = []
    if all_profiles:
        # Iterate raw profile names so an unparseable legacy profile (for
        # example one with an unsupported base_url) is still cleaned up rather
        # than blocking the very command meant to remove it.
        for name in profiles.list_profile_names():
            if credentials.delete_credentials(name):
                removed.append(name)
            profiles.delete_profile(name)
    else:
        profile_name = invocation.profile or profiles.get_selected()
        if credentials.delete_credentials(profile_name):
            removed.append(profile_name)
        profiles.delete_profile(profile_name)

    data = {"removed_profiles": sorted(removed), "all": all_profiles}
    return data, {}


def auth_logout(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    timeout: float | None = go.timeout_option(),
    job_timeout: float | None = go.job_timeout_option(),
    pipeline_timeout: float | None = go.pipeline_timeout_option(),
    color: str = go.color_option(),
    no_input: bool = go.no_input_option(),
    no_progress: bool = go.no_progress_option(),
    debug: bool = go.debug_option(),
    input_file: str | None = go.input_file_option(),
    input_format: str | None = go.input_format_option(),
    all_profiles: bool = typer.Option(False, "--all", help="Remove every profile."),
    yes: bool = typer.Option(False, "--yes", help="Confirm the removal without a prompt."),
) -> None:
    """Remove one profile's (or every profile's) stored credentials.

    Idempotent: removing a profile that does not exist succeeds.
    """
    invocation = go.make_invocation(
        "auth.logout",
        output=output,
        profile=profile,
        project=project,
        timeout=timeout,
        job_timeout=job_timeout,
        pipeline_timeout=pipeline_timeout,
        color=color,
        no_input=no_input,
        no_progress=no_progress,
        debug=debug,
        input_file=input_file,
        input_format=input_format,
    )

    def producer() -> tuple[Any, dict[str, Any]]:
        return _run_logout(invocation, all_profiles=all_profiles, yes=yes)

    executor.run(
        invocation.command_id,
        invocation.output,
        producer,
        agent_mode=invocation.no_input,
        invocation=invocation,
    )
