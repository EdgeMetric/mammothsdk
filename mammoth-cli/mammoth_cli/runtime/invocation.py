"""The resolved invocation context passed to every command handler.

An :class:`Invocation` carries the fully parsed global options plus any
command-specific trailing arguments and the strict input document reference. It
is the single, typed input a handler receives; handlers never read
``sys.argv``, environment, or Typer context directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.output.policy import OUTPUT_AUTO, resolve_output
from mammoth_cli.runtime.input_loader import load_input_document
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.input_fields import accepts_resource_dataset


class _UninitializedInput:
    """Private marker for an invocation whose input has not been admitted."""


_UNINITIALIZED_INPUT = _UninitializedInput()


@dataclass(frozen=True)
class ResourceRef:
    """Fully scoped identity for a resource used by a command invocation."""

    workspace_id: int | None = None
    project_id: int | None = None
    dataset_id: int | None = None
    view_id: int | None = None


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
    resource_ref: ResourceRef | None = field(default=None, repr=False, compare=False)
    # Specialized commands (notably auth login) may need a secret-safe
    # preflight before their own parser reads the document.  The hook is
    # invocation-local and never serialized or shown in repr output.
    input_preflight: Callable[[str | None], None] | None = field(
        default=None, repr=False, compare=False
    )
    _prepared_input: object = field(
        default=_UNINITIALIZED_INPUT, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Resolve the ``auto`` output alias to a concrete mode.

        Resolving here — the single point every invocation passes through —
        means confirmation prompts, the executor, and the renderer all see the
        concrete mode, so a piped ``auto`` run gets machine JSON everywhere
        (including its error envelopes) and never a half-human, half-machine
        mix.
        """
        if self.output == OUTPUT_AUTO:
            import sys

            object.__setattr__(
                self, "output", resolve_output(self.output, is_tty=sys.stdout.isatty())
            )

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

    def prepare_input(self) -> dict[str, Any] | None:
        """Admit this invocation's request document exactly once.

        The cached value is invocation-local and intentionally excluded from
        the dataclass representation.  ``None`` means that ``--input`` was
        omitted; an empty mapping remains an empty mapping, so handlers can
        distinguish omission from an explicitly supplied empty object.

        Returns:
            The parsed request mapping, or None when no ``--input`` was given.

        Raises:
            CliError: When the document is missing, undeclared, unparseable, or
                not a mapping (see
                :func:`mammoth_cli.runtime.input_loader.load_input_document`),
                or ``unknown_input_field`` when it carries a key the command's
                backing method cannot accept.
        """
        if self._prepared_input is _UNINITIALIZED_INPUT:
            if self.input_preflight is not None:
                self.input_preflight(self.input_file)
                # A specialized parser owns the resulting value.  Mark this
                # invocation admitted so the preflight cannot run twice.
                object.__setattr__(self, "_prepared_input", None)
                return None
            document = load_input_document(self.input_file, self.input_format)
            # Transform commands accept the target dataset as resource
            # identity context.  It is intentionally not forwarded as a View
            # method argument, so admit it around the normal SDK-signature
            # validator and restore it for the handler/service boundary.
            resource_dataset: Any = None
            has_resource_dataset = (
                document is not None
                and accepts_resource_dataset(self.command_id)
                and "dataset_id" in document
            )
            if has_resource_dataset:
                assert document is not None
                resource_dataset = document.pop("dataset_id")
                try:
                    if isinstance(resource_dataset, bool):
                        raise ValueError
                    resource_dataset = int(resource_dataset)
                    if resource_dataset <= 0:
                        raise ValueError
                except (TypeError, ValueError):
                    raise CliError(
                        code="invalid_resource_context",
                        message="Input field 'dataset_id' must be a positive integer.",
                        exit_status=EXIT_USAGE,
                        hint="Pass the exact parent dataset id for the target view.",
                        details={"field": "dataset_id", "expected_type": "positive integer"},
                    ) from None
            validate_input_fields(self.command_id, document)
            if has_resource_dataset:
                assert document is not None
                document["dataset_id"] = resource_dataset
            object.__setattr__(self, "_prepared_input", document)
        return self._prepared_input  # type: ignore[return-value]

    def load_input(self) -> dict[str, Any] | None:
        """Return the already-admitted input document for this invocation.

        Kept as the handler-facing compatibility name.  The first call admits
        the document; subsequent calls return the same object without reading
        stdin or parsing the source again.
        """
        document = self.prepare_input()
        # Migrated family handlers remain domain-specific (confirmation,
        # positional fallback, and job waiting remain in those modules), but
        # their structured values cross the shared contract boundary before a
        # handler sees them. This prevents a family handler from validating
        # one document and forwarding a different, hand-picked copy.
        from mammoth_cli.services.command_contract import CONTRACT_BOUND_COMMANDS

        if self.command_id in CONTRACT_BOUND_COMMANDS:
            return self._bound_document(document)
        return document

    def _bound_document(self, document: dict[str, Any] | None) -> dict[str, Any] | None:
        """Bind one admitted document for a migrated API-backed command."""
        if document is None:
            return None
        from mammoth_cli.services.command_contract import bind_command_inputs

        context = dict(self.positionals)
        from mammoth_cli.services.positionals import resolve_positionals

        for index, spec in enumerate(resolve_positionals(self.command_id)):
            if spec.name not in context and index < len(self.extra_args):
                context[spec.name] = self.extra_args[index]
        # A contract with no positional/context values is already admitted and
        # name-preserving. Preserve its cached document identity for callers
        # that intentionally use ``prepare_input() is load_input()`` as their
        # once-only parsing guarantee.
        if not context:
            return document
        return bind_command_inputs(self.command_id, document, **context)

    def bound_input(self) -> dict[str, Any]:
        """Return admitted structured input merged with declared positionals.

        Local handlers use this small boundary instead of independently
        deciding whether a value came from ``--input`` or a positional.  The
        resolved command contract owns that precedence and rejects a handler
        typo in a context name.  Commands without structured input simply get
        the declared positional/context values.
        """
        return self._bound_document(self.prepare_input() or {}) or {}
