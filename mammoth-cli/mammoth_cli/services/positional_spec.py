"""The positional parameter spec a command declares, and the local-path marker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: The ``kind`` of a positional or input field that takes a path on the CLI's own machine.
LOCAL_PATH = "local_path"


#: Input fields (not positionals) that read a host path, by command. A positional that
#: falls back to a field marks that field too, so this lists only fields with no positional.
LOCAL_PATH_INPUT_FIELDS: dict[str, frozenset[str]] = {
    "collection.files.upload": frozenset({"files"}),
}


@dataclass(frozen=True)
class PositionalSpec:
    """One positional argument of a CLI command, derived from the SDK signature.

    Attributes:
        name: snake_case argument name; also the key under which the resolved
            value is stored on :attr:`mammoth_cli.runtime.invocation.Invocation.positionals`.
        type: The scalar the value represents; ``int`` or ``str`` only.
        required: Whether the argument must be supplied on the command line. An
            optional positional may legitimately be absent (filled from
            ``--input`` or a resolved context by the handler).
        help: One-line help shown in the Typer Arguments panel and the docs.
        falls_back_to_field: When set, an omitted optional positional is filled
            from this ``--input`` document field by the handler; this is how the
            "positional OR ``--input`` field" commands stay dual-sourced.
        fills_sdk_param: The backing SDK parameter this positional supplies when
            its name differs from that parameter (e.g. the ``project_id``
            positional fills the ``project`` argument of ``ProjectsAPI.get``).
            Such a parameter is positional-sourced, so it must be excluded from
            the accepted ``--input`` fields even though its name never appears in
            the positional list. Defaults to ``name``.
    """

    name: str
    type: type[int] | type[str]
    required: bool
    help: str
    falls_back_to_field: str | None = None
    fills_sdk_param: str | None = None
    kind: str | None = None
    """``"local_path"`` when the value is a path on the machine running the CLI.

    A host that embeds the CLI has no such machine to read from, so every command
    with a local-path positional or input field is refused there
    (:func:`mammoth_cli.runtime.local_paths.local_path_commands`)."""
    example_value: str | None = None
    """A concrete, resolvable value for the generated runnable example.

    Left ``None`` for ordinary locators, whose example placeholder is a generic
    ``123``/``example`` (never validated at build time). Set only where the
    generated example must actually *run* to exit zero -- the CLI-only discovery
    commands (``schema get``/``capability get``), whose id is looked up against a
    real, offline catalog, so the placeholder must be a genuine command/operation
    id rather than the literal ``example`` (which resolves to nothing)."""

    @property
    def metavar(self) -> str:
        """UPPER_SNAKE placeholder used in help, examples, and docs."""
        return self.name.upper()

    def as_manifest(self) -> dict[str, Any]:
        """Serialize to the manifest/schema JSON shape (type as ``'int'``/``'str'``)."""
        record: dict[str, Any] = {
            "name": self.name,
            "type": self.type.__name__,
            "required": self.required,
            "metavar": self.metavar,
            "falls_back_to_field": self.falls_back_to_field,
            "help": self.help,
        }
        if self.kind is not None:
            record["kind"] = self.kind
        return record
