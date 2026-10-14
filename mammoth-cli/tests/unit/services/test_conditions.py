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
    assert excinfo.value.details == {
        "operator": "GREATER",
        "accepted": list(OPERATOR_NAMES),
        "did_you_mean": "GT",
    }
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


@pytest.mark.parametrize(
    "spec",
    [
        {
            "and": [{"column": "a", "operator": "EQ", "value": 1}],
            "or": [{"column": "b", "operator": "EQ", "value": 2}],
        },
        {"not": {"column": "a", "operator": "EQ", "value": 1}, "value": 3},
        {"or": [{"column": "a", "operator": "EQ", "value": 1}], "column": "b"},
    ],
)
def test_a_compound_condition_with_a_second_key_is_refused(spec: dict[str, object]) -> None:
    """With "and" beside "or", "or" was silently dropped: the filter kept or
    removed different rows than the caller wrote."""
    with pytest.raises(CliError) as excinfo:
        compile_condition(spec)
    assert excinfo.value.code == "invalid_condition"


@pytest.mark.parametrize(
    ("guess", "expected"),
    [("NOT_EQUALS", "NE"), ("EQUALS", "EQ"), ("CONTAIN", "CONTAINS"), ("GREATER_THAN", "GT")],
)
def test_unknown_operator_suggests_the_closest_valid_one(guess: str, expected: str) -> None:
    from mammoth.condition import Condition

    from mammoth_cli.services.type_system import TypeValidationError, validate_value

    spec = {"column": "Status", "operator": guess, "value": "x"}
    with pytest.raises(CliError) as caught:
        validate_value(spec, Condition, "condition")
    error = caught.value
    assert guess in error.message and f"Did you mean {expected}?" in error.message
    assert error.details["did_you_mean"] == expected
    assert error.details["accepted"] == list(OPERATOR_NAMES)
    assert error.details["path"] == "condition"
    assert TypeValidationError  # other malformed conditions still use the type error


def test_condition_schema_enumerates_the_valid_operators() -> None:
    from mammoth.condition import Condition

    from mammoth_cli.services.type_system import json_schema

    schema = json_schema(Condition)
    assert schema["oneOf"][0]["properties"]["operator"]["enum"] == list(OPERATOR_NAMES)
