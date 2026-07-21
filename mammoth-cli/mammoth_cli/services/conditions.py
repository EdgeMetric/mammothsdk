"""Compile a JSON condition spec into the SDK's condition objects.

Command modules never import the SDK's condition builder; instead a filter or
set-values command forwards a plain ``condition`` spec (parsed from ``--input``)
and this service-layer helper turns it into a
:class:`mammoth.condition.Condition` / ``CompoundCondition`` / ``NotCondition``.
A spec is one of:

* a leaf mapping ``{"column": ..., "operator": ..., "value": ...}`` (plus the
  optional ``case_sensitive``, ``value_is_column``, ``component``, ``truncate``,
  ``value_is_date_fn`` fields the SDK ``Condition`` accepts),
* ``{"and": [spec, ...]}`` / ``{"or": [spec, ...]}`` for compound conditions,
* ``{"not": spec}`` for negation.
"""

from __future__ import annotations

from functools import reduce
from typing import Any

from mammoth.condition import CompoundCondition, Condition, NotCondition

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

_ConditionResult = Condition | CompoundCondition | NotCondition
_LEAF_FIELDS = {
    "column",
    "operator",
    "value",
    "case_sensitive",
    "value_is_column",
    "component",
    "truncate",
    "value_is_date_fn",
}


def _invalid(message: str) -> CliError:
    return CliError(
        code="invalid_condition",
        message=message,
        exit_status=EXIT_USAGE,
        hint='Use {"column","operator","value"}, or {"and"/"or":[...]}, or {"not":{...}}.',
    )


def compile_condition(spec: Any) -> _ConditionResult:
    """Compile a condition spec into an SDK condition object.

    Args:
        spec: The condition spec mapping (leaf, ``and``/``or``, or ``not``).

    Returns:
        The compiled SDK condition.

    Raises:
        CliError: ``invalid_condition`` when the spec shape is not recognized
            or a compound branch is empty.
    """
    if not isinstance(spec, dict):
        raise _invalid("A condition must be a mapping.")

    if "and" in spec or "or" in spec:
        key = "and" if "and" in spec else "or"
        branches = spec[key]
        if not isinstance(branches, list) or not branches:
            raise _invalid(f"'{key}' must be a non-empty list of conditions.")
        compiled = [compile_condition(branch) for branch in branches]
        if key == "and":
            return reduce(lambda a, b: a & b, compiled)
        return reduce(lambda a, b: a | b, compiled)

    if "not" in spec:
        return ~compile_condition(spec["not"])

    unknown = set(spec) - _LEAF_FIELDS
    if unknown:
        raise _invalid(f"Unknown condition field(s): {', '.join(sorted(unknown))}.")
    if "column" not in spec or "operator" not in spec:
        raise _invalid("A leaf condition needs at least 'column' and 'operator'.")
    return Condition(**spec)
