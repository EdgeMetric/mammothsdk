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
from mammoth_cli.runtime.strict import validate_input_fields


@dataclass(frozen=True)
class Invocation:
    """One command invocation with resolved global options."""

    command_id: str
    output: str = "table"
    profile: str | None = None
    project: int | None = None
    timeout: float | None = None
    job_timeout: float | None = None
    pipeline_timeout: float | None = None
    color: str = "auto"
    no_input: bool = False
    no_progress: bool = False
    debug: bool = False
    yes: bool = False
    confirm: str | None = None
    input_file: str | None = None
    input_format: str | None = None
    positionals: dict[str, Any] = field(default_factory=dict)
    extra_args: list[str] = field(default_factory=list)

    def positional(self, name: str) -> Any:
        """Return a resolved positional's value, or None when it was omitted.

        The value has already been parsed off the command line (or supplied by a
        test), keyed by the positional's declared
        :attr:`mammoth_cli.services.positionals.PositionalSpec.name`. Handlers
        read positionals through this accessor instead of indexing
        ``extra_args`` so the declared spec is the single source of truth.

        Args:
            name: The positional's snake_case name.

        Returns:
            The positional value, or None when it was not supplied.
        """
        if name in self.positionals:
            return self.positionals[name]
        # Direct handler unit tests and incremental callers may still construct
        # Invocation with the legacy ordered list. Resolve that list through the
        # declarative positional catalog instead of making handlers know indexes.
        from mammoth_cli.services.positionals import resolve_positionals

        for index, spec in enumerate(resolve_positionals(self.command_id)):
            if spec.name == name and index < len(self.extra_args):
                return self.extra_args[index]
        return None

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
                :func:`mammoth_cli.runtime.input_loader.load_input_document`),
                or ``unknown_input_field`` when it carries a key the command's
                backing method cannot accept.
        """
        document = load_input_document(self.input_file, self.input_format)
        validate_input_fields(self.command_id, document)
        return document
