"""Derive a command's accepted arguments from its backing SDK signature.

Each reviewed command names the public SDK method that backs it
(``record["sdk_symbol"]``). That method's real signature is the authoritative,
always-current description of what the command accepts — no second copy to
drift. This module resolves the symbol to its callable and turns the signature
into an :class:`ArgSpec`, which several call sites share:

* command schema discovery, so ``mammoth schema get`` reports the real accepted
  fields (name, type, enum values, default) instead of an empty list;
* strict ``--input`` validation, so an unknown or misspelled document key is
  rejected instead of being silently dropped, and a present field is coerced
  to its annotated scalar type instead of reaching the SDK as a raw string;
* the argument validator, so a stray option or surplus positional is refused
  rather than ignored.

Resolution is by dotted path and never touches a private (``_``-prefixed)
member, mirroring :mod:`mammoth_cli.services.dispatch`.
"""

from __future__ import annotations

import enum
import importlib
import inspect
import types
import typing
from dataclasses import dataclass
from functools import cache
from typing import Any, get_args, get_origin

# Sentinel distinguishing "no default value" from a real default of ``None``.
_NO_DEFAULT = object()


@dataclass(frozen=True)
class FieldSpec:
    """One argument a command's backing SDK method accepts.

    Attributes:
        name: The parameter name.
        required: Whether the method declares no default for it.
        annotation: The parameter's resolved real type (not a stringified
            forward reference), or None when it has no annotation or the
            method's hints could not be resolved at all.
        default: The parameter's default value, or the module's "no default"
            sentinel; use :attr:`has_default` rather than comparing directly.
    """

    name: str
    required: bool
    annotation: Any = None
    default: Any = _NO_DEFAULT

    @property
    def has_default(self) -> bool:
        """Whether this field carries a default value."""
        return self.default is not _NO_DEFAULT

    @property
    def resolved_type(self) -> Any:
        """This field's annotation with an ``Optional[...]`` wrapper removed."""
        return unwrap_optional(self.annotation)

    @property
    def type_name(self) -> str:
        """A short display name for the field's type, for schema discovery."""
        return render_type_name(self.resolved_type)

    @property
    def enum_values(self) -> list[str] | None:
        """The member values, if this field's type is a string enum."""
        target = self.resolved_type
        if isinstance(target, type) and issubclass(target, enum.Enum):
            return [member.value for member in target]
        return None

    @property
    def default_value(self) -> Any:
        """A JSON-safe rendering of this field's default, or None when absent."""
        if not self.has_default:
            return None
        value = self.default
        if isinstance(value, enum.Enum):
            return value.value
        if value is None or isinstance(value, (bool, int, float, str, list, dict)):
            return value
        return str(value)


@dataclass(frozen=True)
class ArgSpec:
    """The accepted-argument shape of a command's backing SDK method.

    Attributes:
        fields: Each named parameter the method declares, in signature order.
        accepts_extra: Whether the method has a ``**kwargs`` catch-all, in which
            case any additional field name is legitimately accepted.
    """

    fields: tuple[FieldSpec, ...]
    accepts_extra: bool

    @property
    def field_names(self) -> frozenset[str]:
        """The set of declared field names."""
        return frozenset(field.name for field in self.fields)

    @property
    def required_names(self) -> tuple[str, ...]:
        """The declared field names that have no default, in signature order."""
        return tuple(field.name for field in self.fields if field.required)


def unwrap_optional(annotation: Any) -> Any:
    """Return the non-``None`` member of an ``Optional[...]``/``X | None`` union.

    Args:
        annotation: A resolved type annotation, or None.

    Returns:
        The inner type when ``annotation`` is a two-member union with
        ``NoneType`` as one member; otherwise ``annotation`` unchanged.
    """
    if annotation is None:
        return None
    origin = get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        members = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(members) == 1:
            return members[0]
    return annotation


def render_type_name(annotation: Any) -> str:
    """Render a resolved (``Optional``-unwrapped) annotation as a short name.

    Args:
        annotation: A resolved type, or None.

    Returns:
        A display string such as ``"int"``, ``"bool"``, ``"BulkReplaceMapping"``,
        or ``"list[BulkReplaceMapping]"``; ``"any"`` when nothing is known.
    """
    if annotation is None or annotation is Any:
        return "any"
    origin = get_origin(annotation)
    if origin in (list, typing.List):  # noqa: UP006 - runtime origin comparison
        args = get_args(annotation)
        return f"list[{render_type_name(args[0])}]" if args else "list"
    if origin in (dict, typing.Dict):  # noqa: UP006 - runtime origin comparison
        args = get_args(annotation)
        if len(args) == 2:
            return f"dict[{render_type_name(args[0])}, {render_type_name(args[1])}]"
        return "dict"
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation)


def _resolve_callable(sdk_symbol: str) -> object | None:
    """Resolve a dotted ``sdk_symbol`` to its callable, or None if it cannot be.

    Args:
        sdk_symbol: A dotted symbol such as ``mammoth.view.View.bulk_replace``
            or ``mammoth.api.projects.ProjectsAPI.list``.

    Returns:
        The resolved callable, or None when the symbol names a private member,
        cannot be imported, or does not resolve to an attribute chain. Internal
        module segments (for example ``mammoth._mixins._text_ops``) are allowed
        — only the resolved class/method attributes must be public.
    """
    parts = sdk_symbol.split(".")
    # Walk from the longest importable module prefix down to the attribute tail.
    for boundary in range(len(parts) - 1, 0, -1):
        module_name = ".".join(parts[:boundary])
        try:
            obj: object = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        attributes = parts[boundary:]
        # The class/method attributes resolved off the module must be public,
        # so the CLI can never reach a private (``_``-prefixed) SDK member.
        if any(attr.startswith("_") for attr in attributes):
            return None
        try:
            for attr in attributes:
                obj = getattr(obj, attr)
        except AttributeError:
            return None
        return obj
    return None


@cache
def _sdk_type_namespace() -> dict[str, Any]:
    """Return SDK types needed to resolve annotations hidden behind ``TYPE_CHECKING``.

    Several SDK modules (the ``View`` mixins in particular) import their
    annotated types (``Condition``, the ``mammoth.models.pipeline`` dataclasses
    and enums, ``View`` itself) only under ``TYPE_CHECKING``, so those names are
    absent from a method's own ``__globals__`` at runtime and
    :func:`typing.get_type_hints` cannot resolve them unaided. This supplies
    them as an explicit namespace, mirroring
    :func:`mammoth_cli.services.coerce._sdk_type_namespace`.
    """
    from mammoth import condition as _condition_module
    from mammoth import view as _view_module
    from mammoth.models import pipeline as _pipeline_module

    namespace: dict[str, Any] = {}
    for module in (_pipeline_module, _condition_module, _view_module):
        for name in dir(module):
            if not name.startswith("_"):
                namespace[name] = getattr(module, name)
    return namespace


@cache
def _type_hints(sdk_symbol: str) -> dict[str, Any]:
    """Return the resolved type hints for a command's backing method.

    Args:
        sdk_symbol: The command's reviewed ``sdk_symbol``.

    Returns:
        A mapping of parameter name to resolved type. Empty (never raises) when
        the symbol does not resolve or its annotations cannot be resolved even
        with the SDK type namespace, so callers degrade to "no type known"
        rather than crashing on an exotic or unresolvable forward reference.
    """
    target = _resolve_callable(sdk_symbol)
    if target is None or not callable(target):
        return {}
    try:
        return typing.get_type_hints(target, localns=_sdk_type_namespace())
    except Exception:  # noqa: BLE001 - deliberately broad, see docstring
        return {}


@cache
def arg_spec(sdk_symbol: str) -> ArgSpec | None:
    """Return the :class:`ArgSpec` for a command's backing SDK method.

    Args:
        sdk_symbol: The command's reviewed ``sdk_symbol``.

    Returns:
        The derived :class:`ArgSpec`, or None when the symbol does not resolve
        to an introspectable callable (in which case callers fall back to their
        prior, non-strict behavior rather than guessing).
    """
    target = _resolve_callable(sdk_symbol)
    if target is None or not callable(target):
        return None
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):
        return None

    hints = _type_hints(sdk_symbol)
    fields: list[FieldSpec] = []
    accepts_extra = False
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            accepts_extra = True
            continue
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            continue
        default = (
            parameter.default if parameter.default is not inspect.Parameter.empty else _NO_DEFAULT
        )
        fields.append(
            FieldSpec(
                name=name,
                required=parameter.default is inspect.Parameter.empty,
                annotation=hints.get(name),
                default=default,
            )
        )
    return ArgSpec(fields=tuple(fields), accepts_extra=accepts_extra)


def accepted_field_names(sdk_symbol: str) -> frozenset[str] | None:
    """Return the field names a command accepts, or None to accept anything.

    Args:
        sdk_symbol: The command's reviewed ``sdk_symbol``.

    Returns:
        The frozenset of accepted field names, or None when the symbol is
        unresolvable or the method has a ``**kwargs`` catch-all (so no key can
        be proven invalid). None means "do not enforce".
    """
    spec = arg_spec(sdk_symbol)
    if spec is None or spec.accepts_extra:
        return None
    return spec.field_names
