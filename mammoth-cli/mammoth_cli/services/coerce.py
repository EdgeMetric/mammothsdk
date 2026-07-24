"""Coerce JSON-shaped input into the typed values SDK View methods expect.

Transform methods on the rich ``View`` take dataclasses (for example
``BulkReplaceMapping``, ``JoinKeySpec``) and string enums (for example
``JoinType``, ``FillDirection``). Command input arrives as plain JSON — dicts,
strings, and lists. This module bridges the two by reading a bound method's type
hints and converting each argument to its annotated type, recursively, so the
real transform and payload-builder code runs instead of crashing on a raw dict
or string.

The ``condition`` argument is handled separately by
:func:`mammoth_cli.services.conditions.compile_condition` and is left untouched
here.
"""

from __future__ import annotations

import enum
import importlib
import pkgutil
import types
import typing
from collections.abc import Callable
from dataclasses import fields, is_dataclass
from functools import lru_cache
from typing import Any, get_args, get_origin, get_type_hints

from mammoth import condition as _condition_module
from mammoth import models as _models_package
from mammoth import view as _view_module
from mammoth.models import pipeline as _pipeline_module
from pydantic import BaseModel

from mammoth_cli.services.conditions import CONDITION_KWARG, compile_condition

#: The SDK condition types a ``condition``-shaped union field may name. A
#: dict value against one of these members is a condition spec, not a
#: dataclass, so it must be compiled via :func:`compile_condition` rather
#: than routed through the generic dataclass/enum coercion below.
_CONDITION_TYPES = (
    _condition_module.Condition,
    _condition_module.CompoundCondition,
    _condition_module.NotCondition,
)


@lru_cache(maxsize=1)
def _sdk_type_namespace() -> dict[str, Any]:
    """Return the SDK types needed to resolve View-method annotations.

    View transform methods (and public API methods) live in modules that
    import their annotated types (``Condition``, ``View``, the
    ``mammoth.models.*`` dataclasses/enums, and pydantic models such as
    ``PatchRequest``) only under ``TYPE_CHECKING``. Those names are therefore
    absent from each bound method's ``__globals__`` at runtime, so
    :func:`typing.get_type_hints` cannot resolve them on its own. This provides
    them as an explicit namespace spanning every ``mammoth.models`` submodule
    plus the condition and view modules.

    Returns:
        A mapping of type name to type object, drawn from the SDK's condition
        and view modules and every ``mammoth.models`` submodule.
    """
    namespace: dict[str, Any] = {}
    modules: list[Any] = [_pipeline_module, _condition_module, _view_module]
    for info in pkgutil.iter_modules(_models_package.__path__):
        try:
            modules.append(importlib.import_module(f"{_models_package.__name__}.{info.name}"))
        except Exception:  # noqa: S112 # pragma: no cover - skip a non-importable submodule
            continue
    for module in modules:
        for name in dir(module):
            if not name.startswith("_"):
                namespace[name] = getattr(module, name)
    return namespace


def coerce_arguments(method: Callable[..., Any], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Coerce ``kwargs`` to the types annotated on ``method``.

    Args:
        method: The bound View method whose annotations drive coercion.
        kwargs: The raw JSON-shaped keyword arguments.

    Returns:
        A new mapping with each recognized argument coerced to its annotated
        type. Arguments the method does not annotate are passed through
        unchanged, so the method's own signature check still reports them.

    Raises:
        TypeError: When the method's type hints cannot be resolved even with
            the SDK type namespace supplied, so the failure is visible rather
            than silently skipping coercion.
    """
    hints = get_type_hints(method, localns=_sdk_type_namespace())
    coerced: dict[str, Any] = {}
    for name, value in kwargs.items():
        if name == CONDITION_KWARG:
            coerced[name] = value
            continue
        annotation = hints.get(name)
        coerced[name] = _coerce(value, annotation) if annotation is not None else value
    return coerced


def _coerce(value: Any, annotation: Any) -> Any:
    """Coerce a single JSON value to ``annotation`` where a mapping is possible."""
    if value is None or annotation is Any:
        return value

    origin = get_origin(annotation)

    if origin in (typing.Union, types.UnionType):
        return _coerce_union(value, get_args(annotation))

    if origin in (list, typing.List):  # noqa: UP006 - runtime origin comparison
        args = get_args(annotation)
        if args and isinstance(value, list):
            return [_coerce(item, args[0]) for item in value]
        return value

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        if isinstance(value, annotation):
            return value
        if isinstance(value, str):
            return annotation(value)
        return value

    if is_dataclass(annotation) and isinstance(value, dict):
        return _coerce_dataclass(value, annotation)

    if (
        isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
        and isinstance(value, (dict, list))
    ):
        # pydantic v2 validates and recurses into nested models itself, so a
        # single ``model_validate`` builds the whole tree from JSON-shaped input.
        return annotation.model_validate(value)

    return value


def _coerce_union(value: Any, args: tuple[Any, ...]) -> Any:
    """Coerce a value against a union, preferring the member its shape fits."""
    members = [arg for arg in args if arg is not type(None)]
    # A dict against a Condition-family member is a condition spec, compiled
    # through the same path the top-level `condition` kwarg uses -- not a
    # dataclass and not left as a raw dict.
    if isinstance(value, dict) and any(member in _CONDITION_TYPES for member in members):
        return compile_condition(value)
    # A dict fits a dataclass member; a string fits an enum member.
    if isinstance(value, dict):
        for member in members:
            if is_dataclass(member):
                return _coerce_dataclass(value, member)
    if isinstance(value, str):
        for member in members:
            if isinstance(member, type) and issubclass(member, enum.Enum):
                try:
                    return member(value)
                except ValueError:
                    continue
        # No enum member accepted the string. If a plain `str` is itself a
        # permitted union member (e.g. `str | SortDirection`), the value is
        # legitimately a non-enum string (a column name, say) -- pass it
        # through unchanged instead of raising on the last enum tried.
        if str in members:
            return value
    # Otherwise try each member; the first that changes the value wins.
    for member in members:
        coerced = _coerce(value, member)
        if coerced is not value:
            return coerced
    return value


def _coerce_dataclass(value: dict[str, Any], dataclass_type: Any) -> Any:
    """Build ``dataclass_type`` from a dict, coercing each declared field."""
    try:
        field_hints = get_type_hints(dataclass_type, localns=_sdk_type_namespace())
    except Exception:  # pragma: no cover - defensive
        field_hints = {}
    field_names = {field.name for field in fields(dataclass_type)}
    coerced: dict[str, Any] = {}
    for key, item in value.items():
        if key not in field_names:
            # Leave unknown keys in place; the dataclass constructor rejects
            # them with a clear TypeError that maps to a usage error.
            coerced[key] = item
            continue
        coerced[key] = _coerce(item, field_hints.get(key))
    return dataclass_type(**coerced)
