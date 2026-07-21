"""Shared global-option definitions for bespoke Typer command callbacks.

Every command, generic or bespoke, exposes the same machine-output and
agent-mode options (``--output``, ``--no-input``, ``--no-progress``,
``--color``, ``--profile``, ``--project``, the timeout family, and the
structured-input pair) so ``--help`` for any command advertises the same
contract. ``app.py``'s generic leaf builds these inline; bespoke command
modules import the factories below instead of repeating thirteen parameter
declarations in every function.
"""

from __future__ import annotations

from typing import cast

import typer

from mammoth_cli.runtime.invocation import Invocation

OUTPUT_MODES = ("table", "json", "yaml", "ndjson", "plain")
COLOR_MODES = ("auto", "always", "never")


def output_option() -> str:
    """Return the shared ``--output`` option definition."""
    return cast(
        str,
        typer.Option(
            "table", "--output", "-o", help="Output format.", metavar="|".join(OUTPUT_MODES)
        ),
    )


def profile_option() -> str | None:
    """Return the shared ``--profile`` option definition."""
    return cast(str | None, typer.Option(None, "--profile", help="Credential profile name."))


def project_option() -> int | None:
    """Return the shared ``--project`` option definition."""
    return cast(int | None, typer.Option(None, "--project", help="Active project id override."))


def base_url_option() -> str | None:
    """Return the shared ``--base-url`` option definition."""
    return cast(
        str | None,
        typer.Option(None, "--base-url", help="Expert runtime API base-url override."),
    )


def timeout_option() -> float | None:
    """Return the shared ``--timeout`` option definition."""
    return cast(float | None, typer.Option(None, "--timeout", help="Per-request timeout seconds."))


def job_timeout_option() -> float | None:
    """Return the shared ``--job-timeout`` option definition."""
    return cast(float | None, typer.Option(None, "--job-timeout", help="Job wait timeout seconds."))


def pipeline_timeout_option() -> float | None:
    """Return the shared ``--pipeline-timeout`` option definition."""
    return cast(
        float | None,
        typer.Option(None, "--pipeline-timeout", help="Pipeline wait timeout seconds."),
    )


def color_option() -> str:
    """Return the shared ``--color`` option definition."""
    return cast(
        str,
        typer.Option("auto", "--color", help="Color policy.", metavar="|".join(COLOR_MODES)),
    )


def no_input_option() -> bool:
    """Return the shared ``--no-input`` option definition."""
    return cast(bool, typer.Option(False, "--no-input", help="Never prompt; fail instead."))


def no_progress_option() -> bool:
    """Return the shared ``--no-progress`` option definition."""
    return cast(bool, typer.Option(False, "--no-progress", help="Never render progress."))


def debug_option() -> bool:
    """Return the shared ``--debug`` option definition."""
    return cast(bool, typer.Option(False, "--debug", help="Emit diagnostic detail to stderr."))


def input_file_option() -> str | None:
    """Return the shared ``--input`` option definition."""
    return cast(
        str | None,
        typer.Option(None, "--input", help="Strict JSON/YAML request document, or '-' for stdin."),
    )


def input_format_option() -> str | None:
    """Return the shared ``--input-format`` option definition."""
    return cast(
        str | None,
        typer.Option(None, "--input-format", help="Required for stdin: json or yaml."),
    )


def make_invocation(
    command_id: str,
    *,
    output: str,
    profile: str | None,
    project: int | None,
    base_url: str | None,
    timeout: float | None,
    job_timeout: float | None,
    pipeline_timeout: float | None,
    color: str,
    no_input: bool,
    no_progress: bool,
    debug: bool,
    input_file: str | None,
    input_format: str | None,
) -> Invocation:
    """Build an :class:`Invocation` from one bespoke command's global options.

    Args:
        command_id: The manifest command id for this invocation.
        output: The resolved ``--output`` value.
        profile: The resolved ``--profile`` value.
        project: The resolved ``--project`` value.
        base_url: The resolved ``--base-url`` value.
        timeout: The resolved ``--timeout`` value.
        job_timeout: The resolved ``--job-timeout`` value.
        pipeline_timeout: The resolved ``--pipeline-timeout`` value.
        color: The resolved ``--color`` value.
        no_input: The resolved ``--no-input`` value.
        no_progress: The resolved ``--no-progress`` value.
        debug: The resolved ``--debug`` value.
        input_file: The resolved ``--input`` value.
        input_format: The resolved ``--input-format`` value.

    Returns:
        The typed :class:`Invocation` a bespoke command hands to its handler.
    """
    return Invocation(
        command_id=command_id,
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
