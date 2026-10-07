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

from functools import cache, reduce
from typing import Any

from mammoth.condition import CompoundCondition, Condition, NotCondition

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

#: The View-method keyword whose value is a condition spec compiled by
#: :func:`compile_condition` rather than coerced by type hints.
CONDITION_KWARG = "condition"

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


@cache
def _operator_aliases() -> dict[str, str]:
    """Comparison symbols accepted as aliases for the backend operator names.

    The SDK ``Condition`` forwards any string, so an unaliased symbol would
    reach the backend as an unknown operator; validate here, at the CLI
    boundary. Built on first use: the operator enum lives in a models module
    that most commands never need.
    """
    from mammoth.models.pipeline import Operator

    return {
        "=": Operator.EQ.value,
        "==": Operator.EQ.value,
        "!=": Operator.NE.value,
        "<>": Operator.NE.value,
        ">": Operator.GT.value,
        ">=": Operator.GTE.value,
        "<": Operator.LT.value,
        "<=": Operator.LTE.value,
    }


@cache
def _operator_names() -> tuple[str, ...]:
    from mammoth.models.pipeline import Operator

    return tuple(member.value for member in Operator)


def __getattr__(name: str) -> tuple[str, ...]:
    if name == "OPERATOR_NAMES":
        return _operator_names()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _resolve_operator(raw: Any) -> str:
    if isinstance(raw, str):
        alias = _operator_aliases().get(raw.strip())
        if alias is not None:
            return alias
        name = raw.strip().upper()
        if name in _operator_names():
            return name
    raise CliError(
        code="invalid_condition",
        message=f"Unknown condition operator {raw!r}.",
        exit_status=EXIT_USAGE,
        hint=(
            "Use one of: " + ", ".join(_operator_names()) + ". Symbols =, !=, >, >=, <, <= are "
            "accepted as aliases. IS_EMPTY / IS_NOT_EMPTY take no value."
        ),
        details={"operator": raw, "accepted": list(_operator_names())},
    )


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

    compound = [key for key in ("and", "or", "not") if key in spec]
    if compound and len(spec) != 1:
        raise _invalid(
            f"'{compound[0]}' must be the condition's only key; nest the others inside it."
        )
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
    return Condition(**{**spec, "operator": _resolve_operator(spec["operator"])})
