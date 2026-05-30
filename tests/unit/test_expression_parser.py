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

    def test_three_operands(self):
        result = parse_expression("Price + Tax + Quantity", COLUMN_MAP)
        assert len(result) == 5
        assert result[0]["TYPE"] == "COLUMN"
        assert result[1]["VALUE"] == "+"
        assert result[2]["TYPE"] == "COLUMN"
        assert result[3]["VALUE"] == "+"
        assert result[4]["TYPE"] == "COLUMN"

    def test_nested_parens(self):
        result = parse_expression("((Price + Tax) * Quantity)", COLUMN_MAP)
        # Outer parens create one nested list
        assert isinstance(result[0], list)
        inner = result[0]
        # Inner: [sub_expr, *, Quantity]
        assert isinstance(inner[0], list)  # (Price + Tax)
        assert inner[1] == {"TYPE": "OPERATOR", "VALUE": "*"}

    def test_modulo(self):
        result = parse_expression("Quantity % 2", COLUMN_MAP)
        assert result[1] == {"TYPE": "OPERATOR", "VALUE": "%"}
        assert result[2] == {"TYPE": "NUMBER", "VALUE": 2}

    def test_float_literal(self):
        result = parse_expression("Price * 0.15", COLUMN_MAP)
        assert result[2] == {"TYPE": "NUMBER", "VALUE": 0.15}

    def test_column_name_substring_of_another(self):
        """Longer column name should match first (substring-boundary case)."""
        col_map = {"Tax Rate": "col_tr", "Tax": "col_t"}
        result = parse_expression("Tax Rate + Tax", col_map)
        assert result[0] == {"TYPE": "COLUMN", "VALUE": "col_tr"}
        assert result[2] == {"TYPE": "COLUMN", "VALUE": "col_t"}


class TestFunctionParsing:
    """Test function call parsing (ABS, INT, SMALL, LARGE)."""

    def test_abs_function(self):
        result = parse_expression("ABS(Price - Tax)", COLUMN_MAP)
        assert len(result) == 1
        func = result[0]
        assert func["TYPE"] == "FUNCTION"
        assert func["VALUE"]["FUNCTION"] == "ABS"
        # Argument should be the parsed inner expression
        arg = func["VALUE"]["ARGUMENT"][0]
        # It's a list: [COLUMN, OPERATOR, COLUMN]
        assert isinstance(arg, list)
        assert len(arg) == 3

    def test_int_function(self):
        result = parse_expression("INT(Price)", COLUMN_MAP)
        assert result[0]["TYPE"] == "FUNCTION"
        assert result[0]["VALUE"]["FUNCTION"] == "INT"
        assert result[0]["VALUE"]["ARGUMENT"][0] == {"TYPE": "COLUMN", "VALUE": "column_price123"}

    def test_nested_function(self):
        result = parse_expression("ABS(Price) + ABS(Tax)", COLUMN_MAP)
        assert len(result) == 3
        assert result[0]["TYPE"] == "FUNCTION"
        assert result[0]["VALUE"]["FUNCTION"] == "ABS"
        assert result[1] == {"TYPE": "OPERATOR", "VALUE": "+"}
        assert result[2]["TYPE"] == "FUNCTION"

    def test_function_with_multiple_args(self):
        result = parse_expression("SMALL(Price, 2)", COLUMN_MAP)
        assert result[0]["TYPE"] == "FUNCTION"
        assert result[0]["VALUE"]["FUNCTION"] == "SMALL"
        args = result[0]["VALUE"]["ARGUMENT"]
        assert len(args) == 2
        assert args[0] == {"TYPE": "COLUMN", "VALUE": "column_price123"}
        assert args[1] == {"TYPE": "NUMBER", "VALUE": 2}

    def test_function_in_expression(self):
        result = parse_expression("ABS(Price) * Quantity", COLUMN_MAP)
        assert len(result) == 3
        assert result[0]["TYPE"] == "FUNCTION"
        assert result[1] == {"TYPE": "OPERATOR", "VALUE": "*"}
        assert result[2] == {"TYPE": "COLUMN", "VALUE": "column_qty123"}
