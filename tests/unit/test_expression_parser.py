"""Unit tests for the math expression string parser."""

from __future__ import annotations

import pytest

from mammoth._expression_parser import parse_expression

# Column map matching our test fixtures
COLUMN_MAP = {
    "Price": "column_price123",
    "Quantity": "column_qty123",
    "Tax": "column_tax123",
    "Total Sales": "column_total_s123",
    "base_salary": "column_salary123",
    "bonus_pct": "column_bonus123",
}


class TestParseExpression:
    """Test expression parsing into backend format."""

    def test_simple_multiplication(self):
        result = parse_expression("Price * Quantity", COLUMN_MAP)
        assert len(result) == 3
        assert result[0] == {"TYPE": "COLUMN", "VALUE": "column_price123"}
        assert result[1] == {"TYPE": "OPERATOR", "VALUE": "*"}
        assert result[2] == {"TYPE": "COLUMN", "VALUE": "column_qty123"}

    def test_simple_addition(self):
        result = parse_expression("Price + Tax", COLUMN_MAP)
        assert len(result) == 3
        assert result[0]["TYPE"] == "COLUMN"
        assert result[1] == {"TYPE": "OPERATOR", "VALUE": "+"}
        assert result[2]["TYPE"] == "COLUMN"

    def test_numeric_literal(self):
        result = parse_expression("Price * 1.1", COLUMN_MAP)
        assert len(result) == 3
        assert result[2] == {"TYPE": "NUMBER", "VALUE": 1.1}

    def test_integer_literal(self):
        result = parse_expression("Quantity + 5", COLUMN_MAP)
        assert result[2] == {"TYPE": "NUMBER", "VALUE": 5}

    def test_multi_word_column_name(self):
        result = parse_expression("Total Sales * 2", COLUMN_MAP)
        assert result[0] == {"TYPE": "COLUMN", "VALUE": "column_total_s123"}
        assert result[2] == {"TYPE": "NUMBER", "VALUE": 2}

    def test_parentheses(self):
        result = parse_expression("(Price + Tax) * Quantity", COLUMN_MAP)
        # Parenthesized expression becomes a nested list
        assert isinstance(result[0], list)
        assert len(result[0]) == 3
        assert result[1] == {"TYPE": "OPERATOR", "VALUE": "*"}

    def test_all_operators(self):
        for op in ["+", "-", "*", "/", "%"]:
            result = parse_expression(f"Price {op} Tax", COLUMN_MAP)
            assert result[1] == {"TYPE": "OPERATOR", "VALUE": op}

    def test_unknown_column_raises(self):
        with pytest.raises(ValueError, match="Unrecognized token"):
            parse_expression("Unknown * Price", COLUMN_MAP)

    def test_underscore_column_name(self):
        result = parse_expression("base_salary * bonus_pct", COLUMN_MAP)
        assert result[0] == {"TYPE": "COLUMN", "VALUE": "column_salary123"}
        assert result[2] == {"TYPE": "COLUMN", "VALUE": "column_bonus123"}
