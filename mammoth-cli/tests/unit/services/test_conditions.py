"""Condition-spec compilation: operator validation and symbol aliases.

The SDK ``Condition`` forwards any operator string to the backend, so the
CLI is the only place an unknown operator (or a comparison symbol) can be
caught before it becomes a backend error.
"""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.conditions import OPERATOR_NAMES, compile_condition


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("=", "EQ"),
        ("==", "EQ"),
        ("!=", "NE"),
        ("<>", "NE"),
        (">", "GT"),
        (">=", "GTE"),
        ("<", "LT"),
        ("<=", "LTE"),
    ],
)
def test_comparison_symbols_alias_backend_operators(symbol: str, expected: str) -> None:
    condition = compile_condition({"column": "Age", "operator": symbol, "value": 30})
    assert condition.operator == expected  # type: ignore[union-attr]


def test_operator_names_are_case_insensitive() -> None:
    condition = compile_condition({"column": "Status", "operator": "is_empty"})
    assert condition.operator == "IS_EMPTY"  # type: ignore[union-attr]


def test_unknown_operator_is_a_usage_error_naming_the_accepted_set() -> None:
    with pytest.raises(CliError) as excinfo:
        compile_condition({"column": "Age", "operator": "GREATER", "value": 1})
    assert excinfo.value.code == "invalid_condition"
    assert excinfo.value.exit_status == 2
    assert excinfo.value.details == {"operator": "GREATER", "accepted": list(OPERATOR_NAMES)}
    assert "IS_EMPTY / IS_NOT_EMPTY take no value" in (excinfo.value.hint or "")


def test_aliases_apply_inside_compound_specs() -> None:
    condition = compile_condition(
        {
            "and": [
                {"column": "A", "operator": "=", "value": 1},
                {"column": "B", "operator": "<", "value": 2},
            ]
        }
    )
    built = condition.build({"A": "c1", "B": "c2"}, {"A": "NUMERIC", "B": "NUMERIC"})
    assert built == {"AND": [{"c1": {"EQ": {"VALUE": 1}}}, {"c2": {"LT": {"VALUE": 2}}}]}
