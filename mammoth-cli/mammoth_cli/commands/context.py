"""Bespoke `context project` command family: status, use, clear.

A project id is operational context, not authentication. It resolves from
``--project``, then the selected profile's saved active project, then no
project at all. All three commands are local; none makes a network call.
"""

from __future__ import annotations

from typing import Any

import typer

from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import CODE_PROFILE_NOT_FOUND, EXIT_USAGE, CliError
from mammoth_cli.runtime import executor
from mammoth_cli.runtime import options as go
from mammoth_cli.runtime.invocation import Invocation


def _profile_name(invocation: Invocation) -> str:
    return invocation.profile or profiles.get_selected()


def _project_source(invocation: Invocation, record: profiles.ProfileRecord | None) -> str:
    if invocation.project is not None:
        return "flag"
    if record is not None and record.project_id is not None:
        return "profile"
    return "none"


def _profile_not_found_error(profile_name: str) -> CliError:
    return CliError(
        code=CODE_PROFILE_NOT_FOUND,
        message=f"No profile named '{profile_name}' exists yet.",
        exit_status=EXIT_USAGE,
        hint="Run 'mammoth auth login' first.",
        recovery_commands=["mammoth auth login"],
    )


def _run_status(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
    profile_name = _profile_name(invocation)
    record = profiles.get_profile(profile_name)
    project_id = invocation.project
    if project_id is None and record is not None:
        project_id = record.project_id
    data = {
        "profile": profile_name,
        "project_id": project_id,
        "source": _project_source(invocation, record),
    }
    return data, {"profile": profile_name, "project_id": project_id}


def context_project_status(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    base_url: str | None = go.base_url_option(),
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
    """Report the resolved active project id for one profile."""
    invocation = go.make_invocation(
        "context.project.status",
        output=output,
        profile=profile,
        project=project,
        base_url=base_url,
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
        return _run_status(invocation)

    executor.run(invocation.command_id, invocation.output, producer)


def _run_use(invocation: Invocation, *, project_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if project_id <= 0:
        raise CliError(
            code="invalid_project_id",
            message="project_id must be a positive integer.",
            exit_status=EXIT_USAGE,
        )
    profile_name = _profile_name(invocation)
    existing = profiles.get_profile(profile_name)
    if existing is None:
        raise _profile_not_found_error(profile_name)
    profiles.save_profile(
        profiles.ProfileRecord(
            name=existing.name,
            workspace_id=existing.workspace_id,
            server_prefix=existing.server_prefix,
            base_url=existing.base_url,
            project_id=project_id,
        )
    )
    data = {"profile": profile_name, "project_id": project_id}
    return data, {"profile": profile_name, "project_id": project_id}


def context_project_use(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    base_url: str | None = go.base_url_option(),
    timeout: float | None = go.timeout_option(),
    job_timeout: float | None = go.job_timeout_option(),
    pipeline_timeout: float | None = go.pipeline_timeout_option(),
    color: str = go.color_option(),
    no_input: bool = go.no_input_option(),
    no_progress: bool = go.no_progress_option(),
    debug: bool = go.debug_option(),
    input_file: str | None = go.input_file_option(),
    input_format: str | None = go.input_format_option(),
    project_id: int = typer.Argument(..., help="Positive project id to make active."),
) -> None:
    """Save a positive project id as the active project for one profile."""
    invocation = go.make_invocation(
        "context.project.use",
        output=output,
        profile=profile,
        project=project,
        base_url=base_url,
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
        return _run_use(invocation, project_id=project_id)

    executor.run(invocation.command_id, invocation.output, producer)


def _run_clear(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
    profile_name = _profile_name(invocation)
    existing = profiles.get_profile(profile_name)
    if existing is not None and existing.project_id is not None:
        profiles.save_profile(
            profiles.ProfileRecord(
                name=existing.name,
                workspace_id=existing.workspace_id,
                server_prefix=existing.server_prefix,
                base_url=existing.base_url,
                project_id=None,
            )
        )
    data = {"profile": profile_name, "project_id": None}
    return data, {"profile": profile_name}


def context_project_clear(
    output: str = go.output_option(),
    profile: str | None = go.profile_option(),
    project: int | None = go.project_option(),
    base_url: str | None = go.base_url_option(),
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
    """Clear the active project id for one profile. Idempotent."""
    invocation = go.make_invocation(
        "context.project.clear",
        output=output,
        profile=profile,
        project=project,
        base_url=base_url,
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
        return _run_clear(invocation)

    executor.run(invocation.command_id, invocation.output, producer)
