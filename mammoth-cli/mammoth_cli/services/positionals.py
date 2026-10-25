"""Single code-derived source of truth for a command's positional arguments.

A command's positionals are the leading, non-``--input`` tokens it accepts on
the command line (view ids, dataset ids, project names, and the like). Before
this module they were invisible to the system: the manifest hardcoded an empty
list, Typer declared no ``Argument``s, and every handler re-derived its own
positionals imperatively from ``extra_args``. Five consumers each carried a
private, drift-prone copy.

This module resolves a command's positionals **once**, from the command's
backing SDK signature (via :mod:`mammoth_cli.services.argspec`) plus a rule keyed
on the symbol's class, with a small authored override catalog for the cases the
signature cannot express. Every consumer -- the manifest builder, the runnable
``agent_example``, the docs generator, the Typer registration, and the handlers
-- reads the same :func:`resolve_positionals` result, so they cannot disagree.

The derivation is intentionally conservative: ``int``/``str`` scalars only, never
multi-valued, and it emits nothing it cannot justify from the signature. Anything
ambiguous lives in :data:`POSITIONAL_OVERRIDES`, guarded by the real-code drift
test rather than trusted.
"""

from __future__ import annotations

from functools import cache
from typing import Any

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.argspec import arg_spec
from mammoth_cli.services.positional_overrides import POSITIONAL_OVERRIDES
from mammoth_cli.services.positional_spec import PositionalSpec

# Field names that identify a resource (and so become a positional locator).
_IDENTITY_SUFFIXES = ("_id", "_key")
_IDENTITY_NAMES = ("id", "key", "url")

# Fields that are always sourced from a global option or resolved context, never
# a positional. ``project_id`` comes from ``--project`` or the active project for
# every command except the ``project`` family (which overrides it back in, since
# the project *is* the resource those commands act on).
_SOURCED_ELSEWHERE = frozenset({"project_id"})

# Modules whose methods take the dataview as the receiver (``self``); the id is
# therefore not a signature parameter and must be synthesized.
_VIEW_METHOD_MODULE = "mammoth.view"
_MIXIN_MODULE_PREFIX = "mammoth._mixins"


def _module_of(sdk_symbol: str) -> str:
    """Return the module portion of a ``module.Class.method`` SDK symbol."""
    parts = sdk_symbol.rsplit(".", 2)
    return parts[0] if len(parts) == 3 else sdk_symbol


def _is_view_method(sdk_symbol: str) -> bool:
    """Whether the symbol is a :class:`~mammoth.view.View` (or mixin) method."""
    module = _module_of(sdk_symbol)
    return module == _VIEW_METHOD_MODULE or module.startswith(_MIXIN_MODULE_PREFIX)


def _is_identity_name(name: str) -> bool:
    """Whether a field name identifies a resource (so becomes a locator)."""
    return name in _IDENTITY_NAMES or name.endswith(_IDENTITY_SUFFIXES)


def _identity_type(name: str, annotation: Any) -> type[int] | type[str]:
    """Return the declared scalar type, falling back only when unresolved."""
    if annotation is int:
        return int
    if annotation is str:
        return str
    if name == "id" or name.endswith("_id"):
        return int
    return str


def _identity_help(name: str) -> str:
    """Synthesize one-line help for an identity-named locator field."""
    if name == "id":
        return "Identifier of the resource."
    if name == "key":
        return "Key identifying the resource."
    if name == "url":
        return "URL slug identifying the resource."
    if name.endswith("_id"):
        return f"ID of the {name[:-3].replace('_', ' ')}."
    return f"Key identifying the {name[:-4].replace('_', ' ')}."


def derive_positionals(command_id: str, sdk_symbol: str) -> tuple[PositionalSpec, ...]:
    """Derive a command's positionals from its backing SDK signature.

    Args:
        command_id: The manifest command id (used only for diagnostics).
        sdk_symbol: The command's reviewed backing SDK symbol.

    Returns:
        The derived positional specs, in command-line order. A view-method emits
        a single synthesized ``view_id`` locator (the dataview receiver); every
        other symbol emits the leading contiguous run of required, identity-named
        signature parameters that are not sourced from a global option.
    """
    if _is_view_method(sdk_symbol):
        return (
            PositionalSpec(
                name="view_id",
                type=int,
                required=True,
                help="ID of the view to act on.",
            ),
        )
    spec = arg_spec(sdk_symbol)
    if spec is None:
        return ()
    positionals: list[PositionalSpec] = []
    for field in spec.fields:
        if not field.required:
            break
        if field.name in _SOURCED_ELSEWHERE:
            break
        if not _is_identity_name(field.name):
            break
        positionals.append(
            PositionalSpec(
                name=field.name,
                type=_identity_type(field.name, field.annotation),
                required=True,
                help=_identity_help(field.name),
            )
        )
    return tuple(positionals)


def positionals_for(command_id: str, sdk_symbol: str | None) -> tuple[PositionalSpec, ...]:
    """Resolve a command's positionals from an explicitly supplied SDK symbol.

    This is the build-time entry point: :mod:`scripts.build_manifests` already
    holds the reviewed ``command_id`` and ``sdk_symbol`` in scope, so it passes
    them directly rather than reading the (in-progress) manifest.

    Args:
        command_id: The manifest command id.
        sdk_symbol: The command's reviewed backing SDK symbol, or None.

    Returns:
        The command's positional specs (an override when catalogued, else the
        signature derivation, else an empty tuple).
    """
    if command_id in POSITIONAL_OVERRIDES:
        return _with_exact_parent_help(command_id, POSITIONAL_OVERRIDES[command_id])
    if not sdk_symbol:
        return ()
    return _with_exact_parent_help(command_id, derive_positionals(command_id, sdk_symbol))


EXACT_PARENT_HELP = (
    "Exact parent dataset ID. Required for this command: pass it here or as the "
    "'dataset_id' input field; only read commands may omit it and discover the parent."
)

# Per-command overrides of ``EXACT_PARENT_HELP`` for a command whose own
# fields could otherwise be mistaken for this positional. ``view.export.dataset``
# also takes a ``target_ds_id`` input field naming the destination dataset;
# an agent that read only the generic text passed a destination id here
# instead and hit a not-found on the (unrelated) source view's own parent
# (WPP evidence c38/c39).
_EXACT_PARENT_HELP_OVERRIDES: dict[str, str] = {
    "view.optimize": (
        "Optional parent dataset ID. Leave it out and the CLI looks up the view's dataset. "
        "A value that is not the view's dataset is refused before the write."
    ),
    "view.explore-panel.set": (
        "Optional parent dataset ID. Leave it out and the CLI looks up the view's dataset. "
        "A value that is not the view's dataset is refused before the write."
    ),
    "view.explore-panel.edit": (
        "Optional parent dataset ID. Leave it out and the CLI looks up the view's dataset. "
        "A value that is not the view's dataset is refused before the write."
    ),
    "view.explore-panel.add-to-dashboard": (
        "Optional parent dataset ID. Leave it out and the CLI looks up the view's dataset. "
        "A value that is not the view's dataset is refused before the write."
    ),
    "view.export.dataset": (
        "Exact parent dataset ID of the SOURCE view being exported -- not the "
        "destination. Required for this command: pass it here or as the "
        "'dataset_id' input field. To write into an existing destination dataset "
        "instead of creating one, use the 'target_ds_id' input field, not this "
        "positional."
    ),
}


def _with_exact_parent_help(
    command_id: str, specs: tuple[PositionalSpec, ...]
) -> tuple[PositionalSpec, ...]:
    """Tell the truth about an optional ``dataset_id`` on a non-read command.

    The parse shape stays optional (the field may also arrive via ``--input``),
    but the handler refuses project-wide parent discovery before a mutation,
    export, or delete, so the help must say the parent is required there.
    """
    record = command_by_id(command_id)
    if record is None or record.get("mutation_class", "read") == "read":
        return specs
    help_text = _EXACT_PARENT_HELP_OVERRIDES.get(command_id, EXACT_PARENT_HELP)
    return tuple(
        (
            PositionalSpec(
                name=spec.name,
                type=spec.type,
                required=spec.required,
                help=help_text,
                falls_back_to_field=spec.falls_back_to_field,
                fills_sdk_param=spec.fills_sdk_param,
                example_value=spec.example_value,
            )
            if spec.name == "dataset_id" and not spec.required and spec.falls_back_to_field
            else spec
        )
        for spec in specs
    )


def _symbol_for(command_id: str) -> str | None:
    """Return a command's backing SDK symbol from the loaded manifest."""
    record = command_by_id(command_id)
    if record is None:
        return None
    symbol = record.get("sdk_symbol")
    return str(symbol) if symbol else None


@cache
def resolve_positionals(command_id: str) -> tuple[PositionalSpec, ...]:
    """Resolve a command's positionals at runtime, by command id.

    This is the runtime entry point every non-build consumer uses (Typer
    registration, handlers, the docs generator, the drift test). It reads the
    command's reviewed ``sdk_symbol`` from the loaded manifest, then defers to
    :func:`positionals_for`, so it always agrees with the generated manifest.

    Args:
        command_id: The manifest command id.

    Returns:
        The command's positional specs.
    """
    return positionals_for(command_id, _symbol_for(command_id))
