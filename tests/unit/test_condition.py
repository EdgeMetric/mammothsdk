"""Unit tests for Condition and CompoundCondition builders."""

from __future__ import annotations

from mammoth.condition import CompoundCondition, Condition
from mammoth.models.pipeline import Operator


class TestCondition:
    """Test Condition construction and serialization."""

    def test_basic_condition(self):
        c = Condition("Sales", Operator.GTE, 1000)
        assert c.column == "Sales"
        assert c.operator == "GTE"
        assert c.value == 1000

    def test_build_with_column_map(self):
        c = Condition("Sales", Operator.GTE, 1000)
        column_map = {"Sales": "column_abc123"}
        result = c.build(column_map)
        # Format: {internal_name: {OPERATOR: {VALUE: val}}}
        assert "column_abc123" in result
        assert "GTE" in result["column_abc123"]
        assert result["column_abc123"]["GTE"]["VALUE"] == 1000

    def test_build_unknown_column_passthrough(self):
        """Unknown columns pass through as-is (no error)."""
        c = Condition("Unknown", Operator.EQ, "x")
        result = c.build({"Sales": "column_abc"})
        assert "Unknown" in result

    def test_list_value(self):
        c = Condition("Region", Operator.IN_LIST, ["East", "West"])
        column_map = {"Region": "column_xyz"}
        result = c.build(column_map)
        assert result["column_xyz"]["IN_LIST"]["VALUE"] == ["East", "West"]

    def test_empty_operator(self):
        c = Condition("Notes", Operator.IS_EMPTY)
        column_map = {"Notes": "column_nnn"}
        result = c.build(column_map)
        assert result["column_nnn"]["IS_EMPTY"] is True

    def test_and_operator(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        compound = c1 & c2
        assert isinstance(compound, CompoundCondition)
        assert compound.logic == "AND"
        assert len(compound.conditions) == 2

    def test_or_operator(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        compound = c1 | c2
        assert isinstance(compound, CompoundCondition)
        assert compound.logic == "OR"
        assert len(compound.conditions) == 2


class TestCompoundCondition:
    """Test CompoundCondition building."""

    def test_nested_and(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        c3 = Condition("C", Operator.EQ, "X")
        compound = c1 & c2 & c3
        assert isinstance(compound, CompoundCondition)

    def test_build_compound(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        compound = c1 & c2
        column_map = {"A": "col_a", "B": "col_b"}
        result = compound.build(column_map)
        # Format: {AND: [{col_a: ...}, {col_b: ...}]}
        assert "AND" in result
        assert len(result["AND"]) == 2

    def test_mixed_and_or(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        c3 = Condition("C", Operator.EQ, "X")
        compound = (c1 & c2) | c3
        assert isinstance(compound, CompoundCondition)
        assert compound.logic == "OR"

    def test_build_nested(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        c3 = Condition("C", Operator.EQ, "X")
        compound = (c1 & c2) | c3
        column_map = {"A": "col_a", "B": "col_b", "C": "col_c"}
        result = compound.build(column_map)
        assert "OR" in result
        assert len(result["OR"]) == 2
