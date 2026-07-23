"""Bespoke `auth` command family: login, status, logout.

Authentication has exactly three required inputs (API key, API secret,
workspace id) and one optional input (server prefix, default ``app``).
Authentication always requires a login; there is no environment credential
path. These commands never accept a secret as an ordinary command-line value:
the API key and secret come from a hidden TTY prompt or a permission-checked
JSON/YAML login document read through the shared ``--input`` option.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, cast

import typer
import yaml
from pydantic import ValidationError

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.context.resolver import (
    ResolvedAuth,
    resolve_auth,
)
from mammoth_cli.contracts.auth import LoginRequest
from mammoth_cli.errors.envelope import (
    CODE_CONFIRMATION_DECLINED,
    CODE_CONFIRMATION_REQUIRED,
    CODE_INPUT_FORMAT_REQUIRED,
    CODE_INVALID_INPUT_DOCUMENT,
    CODE_INVALID_INPUT_FORMAT,
    CODE_INVALID_WORKSPACE_ID,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.policy import resolve_policy
from mammoth_cli.runtime import executor
from mammoth_cli.runtime import options as go
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory as service_factory

_STORAGE_MODES = ("auto", "keyring", "file")


def _format_from_suffix(path: Path) -> str:
    """Detect the JSON/YAML document format from a file suffix.

    Args:
        path: The document path.

    Returns:
        ``"json"`` or ``"yaml"``.

    Raises:
        CliError: ``invalid_input_format`` when the suffix is not recognized.
    """
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in (".yaml", ".yml"):
        return "yaml"
    raise CliError(
        code=CODE_INVALID_INPUT_FORMAT,
        message=f"Cannot detect the document format from '{path.name}'.",
        exit_status=EXIT_USAGE,
        hint="Pass --input-format json or --input-format yaml.",
    )


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
    if path_or_dash == "-":
        if input_format is None:
            raise CliError(
                code=CODE_INPUT_FORMAT_REQUIRED,
                message="Reading the login document from stdin requires --input-format.",
                exit_status=EXIT_USAGE,
                hint="Pass --input-format json or --input-format yaml.",
            )
        text = sys.stdin.read()
        fmt = input_format
    else:
        path = Path(path_or_dash)
        if not path.exists():
            raise CliError(
                code="input_file_not_found",
                message=f"'{path}' does not exist.",
                exit_status=EXIT_USAGE,
            )
        _check_file_permissions(path)
        text = path.read_text(encoding="utf-8")
        fmt = input_format or _format_from_suffix(path)

    if fmt not in ("json", "yaml"):
        raise CliError(
            code=CODE_INVALID_INPUT_FORMAT,
            message=f"'{fmt}' is not a supported input format.",
            exit_status=EXIT_USAGE,
            hint="Use json or yaml.",
        )
    try:
        loaded = json.loads(text) if fmt == "json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise CliError(
            code=CODE_INVALID_INPUT_DOCUMENT,
            message=f"The login document is not valid {fmt}.",
            exit_status=EXIT_USAGE,
            hint="Provide a well-formed JSON or YAML object.",
        ) from exc
    if not isinstance(loaded, dict):
        raise CliError(
            code=CODE_INVALID_INPUT_DOCUMENT,
            message="The login document must be a JSON/YAML object.",
            exit_status=EXIT_USAGE,
        )
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


def _run_login(
    invocation: Invocation,
    *,
    workspace: int | None,
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

    policy = resolve_policy(
        output=invocation.output,
        no_input=invocation.no_input,
        no_progress=invocation.no_progress,
        is_tty=sys.stdin.isatty(),
        color=invocation.color,
    )

    effective_workspace: int | None
    if invocation.input_file is not None:
        document = _load_login_document(invocation.input_file, invocation.input_format)
        request = _validate_login_document(document)
        api_key, api_secret = request.api_key, request.api_secret
        effective_workspace = workspace if workspace is not None else request.workspace_id
        effective_prefix = server_prefix if server_prefix is not None else request.server_prefix
    elif not policy.prompts_disabled:
        api_key = typer.prompt("API key", hide_input=True)
        api_secret = typer.prompt("API secret", hide_input=True)
        effective_workspace = workspace
        effective_prefix = server_prefix
    else:
        raise CliError(
            code="login_input_required",
            message="Non-interactive login requires --input.",
            exit_status=EXIT_USAGE,
            hint="Pass --input FILE|- (with --input-format for stdin), or run in a terminal.",
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
    profiles.save_profile(record)
    storage_used = credentials.store_credentials(
        profile_name,
        api_key,
        api_secret,
        storage=cast(credentials.StorageMode, storage),
        interactive=not policy.prompts_disabled,
    )
    profiles.set_selected(profile_name)

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
    workspace: int | None = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace id. Required unless --input supplies it.",
    ),
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
    )

    def producer() -> tuple[Any, dict[str, Any]]:
        return _run_login(
            invocation,
            workspace=workspace,
            server_prefix=server_prefix,
            storage=storage,
        )

    executor.run(invocation.command_id, invocation.output, producer)


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

    executor.run(invocation.command_id, invocation.output, producer)


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

    policy = resolve_policy(
        output=invocation.output,
        no_input=invocation.no_input,
        no_progress=invocation.no_progress,
        is_tty=sys.stdin.isatty(),
        color=invocation.color,
    )
    if not yes:
        if policy.prompts_disabled:
            raise CliError(
                code=CODE_CONFIRMATION_REQUIRED,
                message="auth logout requires --yes in non-interactive mode.",
                exit_status=EXIT_USAGE,
                hint="Re-run with --yes.",
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

    executor.run(invocation.command_id, invocation.output, producer)
