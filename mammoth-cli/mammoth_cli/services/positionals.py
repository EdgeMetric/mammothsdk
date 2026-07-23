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

from dataclasses import dataclass
from functools import cache
from typing import Any

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.services.argspec import arg_spec

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
        return {
            "name": self.name,
            "type": self.type.__name__,
            "required": self.required,
            "metavar": self.metavar,
            "falls_back_to_field": self.falls_back_to_field,
            "help": self.help,
        }


def _optional_project_id() -> tuple[PositionalSpec, ...]:
    """The shared ``project`` family locator: an optional project-id positional.

    Every ``project`` command that acts on a single project accepts the project
    id as an optional positional, falling back to the active project when
    omitted. That dual-sourcing is invisible to the SDK signature (the id is
    ``project``/``project_id`` and looks required), so it is authored here.
    """
    return (
        PositionalSpec(
            name="project_id",
            type=int,
            required=False,
            help="ID of the project to act on; defaults to the active project.",
            # ``project get`` names this argument ``project`` in the SDK; every
            # other project command names it ``project_id``. Declaring the alias
            # keeps the resource id positional-sourced (never an --input field)
            # regardless of the backing parameter's name.
            fills_sdk_param="project",
        ),
    )


# Commands whose positionals the signature cannot express correctly. Each entry
# replaces the derivation wholesale; the drift test proves the union is right.
POSITIONAL_OVERRIDES: dict[str, tuple[PositionalSpec, ...]] = {
    # project family: the project id is an optional positional (falls back to the
    # active project). The SDK signature marks it required or omits it, so the
    # dual-sourced optional locator is authored here.
    "project.get": _optional_project_id(),
    "project.pending-changes": _optional_project_id(),
    "project.resource-status": _optional_project_id(),
    "project.resource-dependencies": _optional_project_id(),
    "project.publish-credentials": _optional_project_id(),
    "project.update": _optional_project_id(),
    "project.delete": _optional_project_id(),
    "project.sample-flow": _optional_project_id(),
    "project.checkpoint.list": _optional_project_id(),
    "project.data-check.list": _optional_project_id(),
    "project.user.add": _optional_project_id(),
    "project.user.remove": _optional_project_id(),
    "project.user.update": _optional_project_id(),
    # project create takes the name as an optional positional or a ``name`` field.
    "project.create": (
        PositionalSpec(
            name="name",
            type=str,
            required=False,
            help="Name of the new project; or pass it via the 'name' input field.",
            falls_back_to_field="name",
        ),
    ),
    # project commands sourced entirely from ``--input`` or the active workspace.
    "project.list": (),
    "project.bulk-delete": (),
    "project.bulk-update": (),
    # ``data-app user remove`` takes the shared user's email as a required second
    # positional. ``email`` is not an identity-named signature parameter, so the
    # derivation stops after ``data_app_id``; the handler reads it positionally
    # (never from ``--input``), so it is authored here as a required locator.
    "data-app.user.remove": (
        PositionalSpec(
            name="data_app_id",
            type=int,
            required=True,
            help="ID of the data app.",
        ),
        PositionalSpec(
            name="email",
            type=str,
            required=True,
            help="Email address of the shared user to remove.",
        ),
    ),
    # ``ai condition generate`` / ``ai expression generate`` take the dataset id
    # as a positional. The SDK signature leads with the required ``intent`` (a
    # non-identity ``str``), so the derivation stops before ``dataset_id`` and
    # emits nothing -- leaving the command uninvokable (the positional was
    # unregistered) while ``dataset_id`` was still advertised as an --input field
    # the handler never reads. Author the id locator here; ``intent`` (and
    # ``mode`` for the expression variant) remain required --input fields.
    "ai.condition.generate": (
        PositionalSpec(
            name="dataset_id",
            type=int,
            required=True,
            help="ID of the dataset to generate a condition for.",
        ),
    ),
    "ai.expression.generate": (
        PositionalSpec(
            name="dataset_id",
            type=int,
            required=True,
            help="ID of the dataset to generate an expression for.",
        ),
    ),
    # ``support`` create/register verbs take their identifying name/email as a
    # positional OR the matching ``--input`` field (handler
    # ``_require_positional_or_field``). Without a registered optional positional
    # the strict validator rejects the positional form outright, so only the
    # ``--input`` form is invokable and the documented dual-sourcing is a half
    # promise. Author an optional locator that falls back to the field -- the
    # same shape as ``project create``.
    **{
        command: (
            PositionalSpec(
                name=field,
                type=str,
                required=False,
                help=f"{label}; or pass it via the '{field}' input field.",
                falls_back_to_field=field,
            ),
        )
        for command, field, label in (
            ("support.connector.create", "name", "Name of the new connector"),
            ("support.connector-profile.create", "name", "Name of the new connector profile"),
            ("support.feature.create", "name", "Name of the new feature"),
            ("support.feature-profile.create", "name", "Name of the new feature profile"),
            ("support.plan.create", "name", "Name of the new plan"),
            ("support.workspace.create", "name", "Name of the new workspace"),
            ("support.user.register", "email", "Email of the user to register"),
            ("support.user.update", "email", "Email of the user to update"),
        )
    },
    # ``schema get`` / ``capability get`` are CLI-only discovery commands with no
    # backing SDK signature (their ``sdk_symbol`` is a meta-reference), so the
    # derivation emits nothing. Their handlers read the single id positionally
    # (``registry._require_arg`` -> ``extra_args[0]``), so without a registered
    # positional the strict validator rejects the id and the documented command
    # is uninvokable. Author the required locator here.
    "schema.get": (
        PositionalSpec(
            name="command_id",
            type=str,
            required=True,
            help="Command id to fetch the schema for (e.g. view.transform.bulk-replace).",
            # The generated example is executed offline against the real command
            # catalog (see the discovery-example subprocess test), so its
            # placeholder must be a genuine, resolvable command id -- the generic
            # ``example`` would resolve to nothing and exit non-zero.
            example_value="view.transform.bulk-replace",
        ),
    ),
    "capability.get": (
        PositionalSpec(
            name="operation_id",
            type=str,
            required=True,
            help="Operation id to fetch the capability record for (e.g. AddTask).",
            # A genuine, resolvable operation id, for the same reason as above.
            example_value="AddTask",
        ),
    ),
    # ``folder delete`` takes a single folder id positionally; the handler wraps
    # it into the SDK's ``folder_ids`` list. The signature leads with the
    # required ``folder_ids`` (a ``list[int]``, not a scalar identity), so the
    # derivation emits nothing -- the command was uninvokable and ``folder_ids``
    # was advertised as an --input field the handler ignores. Author the scalar
    # locator and mark it as filling ``folder_ids`` so that SDK parameter is
    # excluded from the advertised --input fields.
    "folder.delete": (
        PositionalSpec(
            name="folder_id",
            type=int,
            required=True,
            help="ID of the folder to delete.",
            fills_sdk_param="folder_ids",
        ),
    ),
}


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
        return POSITIONAL_OVERRIDES[command_id]
    if not sdk_symbol:
        return ()
    return derive_positionals(command_id, sdk_symbol)


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
