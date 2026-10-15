"""Refuse to replace a local file a command writes, unless ``--overwrite`` says to."""

from __future__ import annotations

import shlex
from pathlib import Path

from mammoth_cli.errors.envelope import EXIT_CONFLICT, CliError
from mammoth_cli.runtime.invocation import Invocation

CODE_FILE_EXISTS = "file_exists"


def refuse_existing_file(invocation: Invocation, path: str | Path) -> None:
    """Raise ``file_exists`` when ``path`` is already there and ``--overwrite`` was not given.

    Call it before the download starts, so a refusal costs no export job.
    """
    target = Path(path)
    if invocation.overwrite or not (target.exists() or target.is_symlink()):
        return
    rerun = " ".join([*invocation.command_id.split("."), *invocation.extra_args])
    # The same scope the user ran it with, or the re-run lands in another project or
    # profile (a profile only the saved selection supplied is not pinned).
    if invocation.project is not None:
        rerun += f" --project {invocation.project}"
    if invocation.profile and not invocation.profile_is_default:
        rerun += f" --profile {shlex.quote(invocation.profile)}"
    if invocation.input_file and invocation.input_file != "-":
        rerun += f" --input {shlex.quote(invocation.input_file)}"
    raise CliError(
        code=CODE_FILE_EXISTS,
        message=f"{target} already exists; the command would replace it.",
        exit_status=EXIT_CONFLICT,
        hint="Add --overwrite to replace the file, or choose another path with output_path.",
        details={"output_path": str(target)},
        recovery_commands=[f"mammoth {rerun} --overwrite"],
    )
