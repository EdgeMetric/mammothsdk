"""Refuse to replace a local file a command writes, unless ``--overwrite`` says to."""

from __future__ import annotations

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
    rerun = " ".join(["mammoth", *invocation.command_id.split("."), *invocation.extra_args])
    if invocation.input_file and invocation.input_file != "-":
        rerun += f" --input {invocation.input_file}"
    raise CliError(
        code=CODE_FILE_EXISTS,
        message=f"{target} already exists; the command would replace it.",
        exit_status=EXIT_CONFLICT,
        hint="Add --overwrite to replace the file, or choose another path with output_path.",
        details={"output_path": str(target)},
        recovery_commands=[f"{rerun} --overwrite"],
    )
