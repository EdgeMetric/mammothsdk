"""Bespoke `config` command family: get, set, list, path.

Manages non-secret, profile-scoped configuration: the default output mode,
the timeout family, the one-label server prefix, and the active project id.
All local; no command in this family makes a network call.
"""

from __future__ import annotations

from typing import Any

import typer

from mammoth_cli.context import profiles
from mammoth_cli.context.endpoint import resolve_base_url
from mammoth_cli.errors.envelope import (
    CODE_INVALID_CONFIG_VALUE,
    CODE_PROFILE_NOT_FOUND,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.output.policy import VALID_OUTPUTS
from mammoth_cli.runtime import executor
from mammoth_cli.runtime import options as go
from mammoth_cli.runtime.invocation import Invocation

#: The timeout-family setting keys, shared between the settable-key registry
#: and the numeric-parsing branch below.
_TIMEOUT_KEYS = ("timeout", "job_timeout", "pipeline_timeout")
_PROFILE_KEYS = ("server_prefix", "project")
_SETTING_KEYS = ("output", *_TIMEOUT_KEYS)
ALL_CONFIG_KEYS = tuple(sorted(_PROFILE_KEYS + _SETTING_KEYS))


def _profile_name(invocation: Invocation) -> str:
    return invocation.profile or profiles.get_selected()


def _unknown_key_error(key: str) -> CliError:
    return CliError(
        code="unknown_config_key",
        message=f"'{key}' is not a recognized configuration key.",
        exit_status=EXIT_USAGE,
        hint=f"Use one of: {', '.join(ALL_CONFIG_KEYS)}.",
    )


def _profile_not_found_error(profile_name: str) -> CliError:
    return CliError(
        code=CODE_PROFILE_NOT_FOUND,
        message=f"No profile named '{profile_name}' exists yet.",
        exit_status=EXIT_USAGE,
        hint="Run 'mammoth auth login' first.",
        recovery_commands=["mammoth auth login"],
    )


def _validate_key(key: str) -> None:
    if key not in _PROFILE_KEYS and key not in _SETTING_KEYS:
        raise _unknown_key_error(key)


def _get_value(profile_name: str, key: str) -> str | int | None:
    if key in _SETTING_KEYS:
        return profiles.get_setting(profile_name, key)
    record = profiles.get_profile(profile_name)
    if record is None:
        return None
    if key == "project":
        return record.project_id
    return record.server_prefix


def _require_profile(profile_name: str) -> profiles.ProfileRecord:
    existing = profiles.get_profile(profile_name)
    if existing is None:
        raise _profile_not_found_error(profile_name)
    return existing


def _set_value(profile_name: str, key: str, value: str) -> str | int | float:
    if key == "output":
        if value not in VALID_OUTPUTS:
            raise CliError(
                code=CODE_INVALID_CONFIG_VALUE,
                message=f"'{value}' is not a valid --output mode.",
                exit_status=EXIT_USAGE,
                hint=f"Use one of: {', '.join(VALID_OUTPUTS)}.",
            )
        profiles.set_setting(profile_name, key, value)
        return value

    if key in _TIMEOUT_KEYS:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise CliError(
                code=CODE_INVALID_CONFIG_VALUE,
                message=f"'{value}' is not a number.",
                exit_status=EXIT_USAGE,
            ) from exc
        if parsed <= 0:
            raise CliError(
                code=CODE_INVALID_CONFIG_VALUE,
                message="Timeouts must be positive.",
                exit_status=EXIT_USAGE,
            )
        profiles.set_setting(profile_name, key, value)
        return parsed

    if key == "project":
        try:
            project_id = int(value)
        except ValueError as exc:
            raise CliError(
                code=CODE_INVALID_CONFIG_VALUE,
                message=f"'{value}' is not an integer project id.",
                exit_status=EXIT_USAGE,
            ) from exc
        if project_id <= 0:
            raise CliError(
                code=CODE_INVALID_CONFIG_VALUE,
                message="project must be a positive integer.",
                exit_status=EXIT_USAGE,
            )
        existing = _require_profile(profile_name)
        profiles.save_profile(
            profiles.ProfileRecord(
                name=existing.name,
                workspace_id=existing.workspace_id,
                server_prefix=existing.server_prefix,
                project_id=project_id,
            )
        )
        return project_id

    if key == "server_prefix":
        resolve_base_url(value)
        existing = _require_profile(profile_name)
        profiles.save_profile(
            profiles.ProfileRecord(
                name=existing.name,
                workspace_id=existing.workspace_id,
                server_prefix=value,
                project_id=existing.project_id,
            )
        )
        return value

    raise _unknown_key_error(key)


def config_get(
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
    key: str = typer.Argument(..., help="Configuration key."),
) -> None:
    """Get one profile-scoped configuration value."""
    invocation = go.make_invocation(
        "config.get",
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
        _validate_key(key)
        profile_name = _profile_name(invocation)
        value = _get_value(profile_name, key)
        return {"key": key, "value": value, "profile": profile_name}, {"profile": profile_name}

    executor.run(invocation.command_id, invocation.output, producer)


def config_set(
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
    key: str = typer.Argument(..., help="Configuration key."),
    value: str = typer.Argument(..., help="New value."),
) -> None:
    """Set one profile-scoped configuration value."""
    invocation = go.make_invocation(
        "config.set",
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
        _validate_key(key)
        profile_name = _profile_name(invocation)
        stored = _set_value(profile_name, key, value)
        return {"key": key, "value": stored, "profile": profile_name}, {"profile": profile_name}

    executor.run(invocation.command_id, invocation.output, producer)


def config_list(
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
) -> None:
    """List every profile-scoped configuration value."""
    invocation = go.make_invocation(
        "config.list",
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
        profile_name = _profile_name(invocation)
        values = {key: _get_value(profile_name, key) for key in ALL_CONFIG_KEYS}
        return {"profile": profile_name, "values": values}, {"profile": profile_name}

    executor.run(invocation.command_id, invocation.output, producer)


def config_path(
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
) -> None:
    """Print the path to the non-secret profiles file."""
    invocation = go.make_invocation(
        "config.path",
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
        return {"profiles_path": str(profiles.profiles_path())}, {}

    executor.run(invocation.command_id, invocation.output, producer)
