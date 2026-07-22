"""Derive a command's accepted arguments from its backing SDK signature.

Each reviewed command names the public SDK method that backs it
(``record["sdk_symbol"]``). That method's real signature is the authoritative,
always-current description of what the command accepts — no second copy to
drift. This module resolves the symbol to its callable and turns the signature
into an :class:`ArgSpec`, which three call sites share:

* command schema discovery, so ``mammoth schema get`` reports the real accepted
  fields instead of an empty list;
* strict ``--input`` validation, so an unknown or misspelled document key is
  rejected instead of being silently dropped;
* the argument validator, so a stray option or surplus positional is refused
  rather than ignored.

Resolution is by dotted path and never touches a private (``_``-prefixed)
member, mirroring :mod:`mammoth_cli.services.dispatch`.
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from functools import cache


@dataclass(frozen=True)
class FieldSpec:
    """One argument a command's backing SDK method accepts."""

    name: str
    required: bool


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
        fields.append(FieldSpec(name=name, required=parameter.default is inspect.Parameter.empty))
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
