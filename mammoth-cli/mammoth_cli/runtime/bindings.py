"""References between the steps of a task: ``{{steps.upload.data.dataset_id}}``.

A task step names values it does not know until an earlier step has run: the
dataset an upload made, the view it opened. A step writes them as references,
and :func:`resolve` fills them in from the scope of what has run so far. Nothing
here evaluates code: a reference is a dotted path, and a condition is one of a
few JSON operators, so a task definition cannot do more than its steps do.

Reference syntax:

* ``"{{inputs.file}}"``: a string that is only a reference resolves to the value
  itself, with its type (an id stays an int, a list stays a list).
* ``"view {{steps.upload.data.dataset_id}}"``: a reference inside a longer string
  is written in as text.
* Paths walk mappings by key and lists by index: ``steps.up.data.datasets[0].id``.
* ``{"$keys": REF}``: the keys of a mapping, in order.
* ``{"$without": [LIST, VALUE_OR_LIST]}``: the list without the given value(s).
* ``{"$first": REF}``: the first item of a list, or None for an empty one.
* ``{"$default": [REF, FALLBACK]}``: REF's value, or FALLBACK when it is missing or null.

Conditions (``when``): ``{"in": [A, B]}`` (A is an item of list B),
``{"eq": [A, B]}``, ``{"not": COND}``, ``{"all": [COND, ...]}``,
``{"any": [COND, ...]}``, ``{"present": REF}`` (resolves and is not null or
empty), or a bare reference, which is true when its value is truthy.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

_WHOLE = re.compile(r"^\{\{\s*([^{}]+?)\s*\}\}$")
_INNER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
_SEGMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)|\[(\d+)\]")

#: The value operators :func:`resolve` applies; any other ``$`` key is an error.
VALUE_OPERATORS = frozenset({"$keys", "$without", "$first", "$default"})
CONDITION_OPERATORS = frozenset({"in", "eq", "not", "all", "any", "present"})


class BindingError(ValueError):
    """A reference that does not resolve, or an expression that is malformed.

    ``path`` is the reference that failed, when there was one.
    """

    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message)
        self.path = path


class Unresolved:
    """Stands in for a value a later step will make, in a plan that has not run.

    ``str()`` gives ``<steps.upload.data.dataset_id>``, so a planned command shows
    which result it waits for.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def __str__(self) -> str:
        return f"<{self.path}>"

    def __repr__(self) -> str:
        return f"Unresolved({self.path!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Unresolved) and other.path == self.path

    def __hash__(self) -> int:
        return hash(self.path)


_MISSING = object()


def split_path(path: str) -> list[str | int]:
    """``"steps.a.data.items[0].id"`` -> ``["steps", "a", "data", "items", 0, "id"]``."""
    parts: list[str | int] = []
    for dotted in path.split("."):
        if not dotted:
            raise BindingError(f"empty segment in reference '{path}'", path)
        position = 0
        for match in _SEGMENT.finditer(dotted):
            if match.start() != position:
                break
            name, index = match.groups()
            parts.append(int(index) if index is not None else name)
            position = match.end()
        if position != len(dotted):
            raise BindingError(f"cannot read reference '{path}'", path)
    return parts


def lookup(scope: Mapping[str, Any], path: str, *, plan: bool = False) -> Any:
    """The value at ``path`` in ``scope``.

    With ``plan``, a path into a step that has not run yet (its name is in
    ``scope["pending"]``) gives an :class:`Unresolved` instead of an error.

    Raises:
        BindingError: The path does not exist in ``scope``.
    """
    parts = split_path(path)
    if plan and len(parts) >= 2 and parts[0] == "steps" and parts[1] in scope.get("pending", ()):
        return Unresolved(path)
    value: Any = scope
    for part in parts:
        if isinstance(part, int):
            if isinstance(value, list) and -len(value) <= part < len(value):
                value = value[part]
                continue
        elif isinstance(value, Mapping) and part in value:
            value = value[part]
            continue
        if isinstance(value, Unresolved):
            return Unresolved(path)
        raise BindingError(f"reference '{path}' does not resolve", path)
    return value


def _lookup_or_missing(scope: Mapping[str, Any], path: str, plan: bool) -> Any:
    try:
        return lookup(scope, path, plan=plan)
    except BindingError:
        return _MISSING


def resolve(value: Any, scope: Mapping[str, Any], *, plan: bool = False) -> Any:
    """``value`` with every reference and value operator in it filled in from ``scope``.

    Raises:
        BindingError: A reference does not resolve, or an operator is malformed.
    """
    if isinstance(value, str):
        whole = _WHOLE.match(value)
        if whole:
            return lookup(scope, whole.group(1), plan=plan)
        if "{{" not in value:
            return value
        return _INNER.sub(lambda m: _text(lookup(scope, m.group(1), plan=plan)), value)
    if isinstance(value, list):
        return [resolve(item, scope, plan=plan) for item in value]
    if isinstance(value, Mapping):
        operators = [key for key in value if isinstance(key, str) and key.startswith("$")]
        if operators:
            return _operator(value, operators, scope, plan)
        return {key: resolve(item, scope, plan=plan) for key, item in value.items()}
    return value


def _text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _operator(
    value: Mapping[str, Any], operators: list[str], scope: Mapping[str, Any], plan: bool
) -> Any:
    if len(value) != 1 or operators[0] not in VALUE_OPERATORS:
        raise BindingError(
            "a value operator is an object with one key, one of: "
            + ", ".join(sorted(VALUE_OPERATORS))
        )
    name = operators[0]
    argument = value[name]
    if name == "$default":
        if not isinstance(argument, list) or len(argument) != 2:
            raise BindingError("$default takes [REFERENCE, FALLBACK]")
        reference, fallback = argument
        whole = _WHOLE.match(reference) if isinstance(reference, str) else None
        found = (
            _lookup_or_missing(scope, whole.group(1), plan)
            if whole
            else resolve(reference, scope, plan=plan)
        )
        if found is _MISSING or found is None:
            return resolve(fallback, scope, plan=plan)
        return found
    resolved = resolve(argument, scope, plan=plan)
    if _contains_unresolved(resolved):
        return Unresolved(f"{name} of {_describe(argument)}")
    if name == "$keys":
        if not isinstance(resolved, Mapping):
            raise BindingError("$keys needs a mapping")
        return list(resolved)
    if name == "$first":
        if not isinstance(resolved, list):
            raise BindingError("$first needs a list")
        return resolved[0] if resolved else None
    # $without
    if not isinstance(resolved, list) or len(resolved) != 2 or not isinstance(resolved[0], list):
        raise BindingError("$without takes [LIST, VALUE_OR_LIST]")
    items, dropped = resolved
    drop = dropped if isinstance(dropped, list) else [dropped]
    return [item for item in items if item not in drop]


def _describe(argument: Any) -> str:
    if isinstance(argument, str):
        whole = _WHOLE.match(argument)
        return whole.group(1) if whole else argument
    return "an expression"


def _contains_unresolved(value: Any) -> bool:
    if isinstance(value, Unresolved):
        return True
    if isinstance(value, list):
        return any(_contains_unresolved(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_unresolved(item) for item in value.values())
    return False


def contains_unresolved(value: Any) -> bool:
    """Whether ``value`` still waits on a step that has not run (plan mode only)."""
    return _contains_unresolved(value)


def evaluate(condition: Any, scope: Mapping[str, Any], *, plan: bool = False) -> bool | None:
    """Whether ``condition`` holds; None in a plan when it depends on a step not run yet.

    Raises:
        BindingError: The condition is malformed, or a reference in it does not resolve.
    """
    if isinstance(condition, str):
        value = resolve(condition, scope, plan=plan)
        return None if isinstance(value, Unresolved) else bool(value)
    if not isinstance(condition, Mapping) or len(condition) != 1:
        raise BindingError(
            "a condition is a reference or an object with one key, one of: "
            + ", ".join(sorted(CONDITION_OPERATORS))
        )
    ((name, argument),) = condition.items()
    if name not in CONDITION_OPERATORS:
        raise BindingError(f"unknown condition '{name}'")
    if name == "not":
        inner = evaluate(argument, scope, plan=plan)
        return None if inner is None else not inner
    if name in ("all", "any"):
        if not isinstance(argument, list):
            raise BindingError(f"'{name}' takes a list of conditions")
        results = [evaluate(item, scope, plan=plan) for item in argument]
        if name == "all":
            if any(result is False for result in results):
                return False
            return None if any(result is None for result in results) else True
        if any(result is True for result in results):
            return True
        return None if any(result is None for result in results) else False
    if name == "present":
        whole = _WHOLE.match(argument) if isinstance(argument, str) else None
        if whole is None:
            raise BindingError("'present' takes one reference, such as '{{inputs.select}}'")
        found = _lookup_or_missing(scope, whole.group(1), plan)
        if isinstance(found, Unresolved):
            return None
        return found is not _MISSING and found is not None and found != [] and found != ""
    if not isinstance(argument, list) or len(argument) != 2:
        raise BindingError(f"'{name}' takes [A, B]")
    left, right = (resolve(item, scope, plan=plan) for item in argument)
    if _contains_unresolved(left) or _contains_unresolved(right):
        return None
    if name == "eq":
        return bool(left == right)
    if not isinstance(right, list):
        raise BindingError("'in' needs a list as its second value")
    return left in right
