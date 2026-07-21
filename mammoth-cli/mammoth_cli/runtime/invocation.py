"""The resolved invocation context passed to every command handler.

An :class:`Invocation` carries the fully parsed global options plus any
command-specific trailing arguments and the strict input document reference. It
is the single, typed input a handler receives; handlers never read
``sys.argv``, environment, or Typer context directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mammoth_cli.runtime.input_loader import load_input_document


@dataclass(frozen=True)
class Invocation:
    """One command invocation with resolved global options."""

    command_id: str
    output: str = "table"
    profile: str | None = None
    project: int | None = None
    base_url: str | None = None
    timeout: float | None = None
    job_timeout: float | None = None
    pipeline_timeout: float | None = None
    color: str = "auto"
    no_input: bool = False
    no_progress: bool = False
    debug: bool = False
    input_file: str | None = None
    input_format: str | None = None
    extra_args: list[str] = field(default_factory=list)

    @property
    def command_path(self) -> str:
        """The space-separated command path (for envelope meta)."""
        return self.command_id.replace(".", " ")

    def load_input(self) -> dict[str, Any] | None:
        """Load and validate this invocation's ``--input`` request document.

        Returns:
            The parsed request mapping, or None when no ``--input`` was given.

        Raises:
            CliError: When the document is missing, undeclared, unparseable, or
                not a mapping (see
                :func:`mammoth_cli.runtime.input_loader.load_input_document`).
        """
        return load_input_document(self.input_file, self.input_format)
