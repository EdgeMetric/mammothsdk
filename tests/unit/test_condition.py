"""Unit tests for Condition, CompoundCondition, and NotCondition builders."""

from __future__ import annotations

import warnings

import pytest

from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.models.pipeline import Operator

# ── Basic Condition ─────────────────────────────────────────────


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


# ── Compound Condition ──────────────────────────────────────────


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


# ── NOT Operator ────────────────────────────────────────────────


class TestNotCondition:
    """Test NOT operator (~) on conditions."""

    def test_not_single_condition(self):
        c = Condition("Status", Operator.EQ, "Closed")
        negated = ~c
        assert isinstance(negated, NotCondition)
        result = negated.build({"Status": "col_s"})
        assert result == {"NOT": {"col_s": {"EQ": {"VALUE": "Closed"}}}}

    def test_not_compound_and(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        negated = ~(c1 & c2)
        assert isinstance(negated, NotCondition)
        result = negated.build({"A": "col_a", "B": "col_b"})
        assert "NOT" in result
        assert "AND" in result["NOT"]
        assert len(result["NOT"]["AND"]) == 2

    def test_double_negation_cancels(self):
        c = Condition("X", Operator.EQ, 1)
        double_neg = ~~c
        assert double_neg is c

    def test_not_and_combine(self):
        """~c1 & c2 → AND([~c1, c2])."""
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        combined = ~c1 & c2
        assert isinstance(combined, CompoundCondition)
        assert combined.logic == "AND"
        assert len(combined.conditions) == 2
        assert isinstance(combined.conditions[0], NotCondition)
        assert isinstance(combined.conditions[1], Condition)

    def test_not_or_combine(self):
        """~c1 | c2 → OR([~c1, c2])."""
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        combined = ~c1 | c2
        assert isinstance(combined, CompoundCondition)
        assert combined.logic == "OR"
        assert isinstance(combined.conditions[0], NotCondition)

    def test_not_inside_compound(self):
        """AND([~c1, c2]) builds correctly."""
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        combined = ~c1 & c2
        result = combined.build({"A": "col_a", "B": "col_b"})
        assert "AND" in result
        assert result["AND"][0] == {"NOT": {"col_a": {"GT": {"VALUE": 10}}}}
        assert result["AND"][1] == {"col_b": {"LT": {"VALUE": 20}}}

    def test_not_wrapping_compound_or(self):
        c1 = Condition("A", Operator.GT, 10)
        c2 = Condition("B", Operator.LT, 20)
        negated = ~(c1 | c2)
        result = negated.build({"A": "col_a", "B": "col_b"})
        assert result == {
            "NOT": {
                "OR": [
                    {"col_a": {"GT": {"VALUE": 10}}},
                    {"col_b": {"LT": {"VALUE": 20}}},
                ]
            }
        }

    def test_not_empty_operator(self):
        c = Condition("Notes", Operator.IS_EMPTY)
        negated = ~c
        result = negated.build({"Notes": "col_n"})
        assert result == {"NOT": {"col_n": {"IS_EMPTY": True}}}


# ── Deep Nesting ────────────────────────────────────────────────


class TestDeepNesting:
    """Test complex nesting of conditions."""

    def test_three_level_nesting(self):
        """((c1 & c2) | c3) & c4."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        c4 = Condition("D", Operator.NE, 4)
        combined = ((c1 & c2) | c3) & c4
        result = combined.build()
        assert "AND" in result
        assert len(result["AND"]) == 2
        assert "OR" in result["AND"][0]
        assert "AND" in result["AND"][0]["OR"][0]

    def test_or_of_ands(self):
        """(c1 & c2) | (c3 & c4)."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        c4 = Condition("D", Operator.NE, 4)
        combined = (c1 & c2) | (c3 & c4)
        result = combined.build()
        assert "OR" in result
        assert len(result["OR"]) == 2
        assert "AND" in result["OR"][0]
        assert "AND" in result["OR"][1]

    def test_not_wrapping_complex(self):
        """~((c1 & c2) | c3)."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        negated = ~((c1 & c2) | c3)
        result = negated.build()
        assert "NOT" in result
        assert "OR" in result["NOT"]

    def test_four_level_with_not(self):
        """~(~c1 & c2) | c3."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        combined = ~(~c1 & c2) | c3
        result = combined.build()
        assert "OR" in result
        inner_not = result["OR"][0]
        assert "NOT" in inner_not
        assert "AND" in inner_not["NOT"]
        # First element of the inner AND should itself be a NOT
        assert "NOT" in inner_not["NOT"]["AND"][0]

    def test_exact_output_format(self):
        """Verify exact backend format for a nested condition."""
        c1 = Condition("Sales", Operator.GTE, 1000)
        c2 = Condition("Region", Operator.EQ, "West")
        combined = c1 & c2
        col_map = {"Sales": "column_1", "Region": "column_2"}
        result = combined.build(col_map)
        expected = {
            "AND": [
                {"column_1": {"GTE": {"VALUE": 1000}}},
                {"column_2": {"EQ": {"VALUE": "West"}}},
            ]
        }
        assert result == expected


# ── Flattening ──────────────────────────────────────────────────


class TestFlattening:
    """Test that same-logic chains flatten correctly."""

    def test_and_chain_flattens(self):
        """c1 & c2 & c3 → flat AND with 3 children."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        compound = c1 & c2 & c3
        assert compound.logic == "AND"
        assert len(compound.conditions) == 3

    def test_or_chain_flattens(self):
        """c1 | c2 | c3 → flat OR with 3 children."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        compound = c1 | c2 | c3
        assert compound.logic == "OR"
        assert len(compound.conditions) == 3

    def test_cross_logic_no_flatten(self):
        """(c1 & c2) | (c3 & c4) → OR of 2 ANDs (not flattened)."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        c4 = Condition("D", Operator.NE, 4)
        compound = (c1 & c2) | (c3 & c4)
        assert compound.logic == "OR"
        assert len(compound.conditions) == 2
        assert isinstance(compound.conditions[0], CompoundCondition)
        assert isinstance(compound.conditions[1], CompoundCondition)

    def test_not_is_opaque_to_flattening(self):
        """~c1 & ~c2 & c3 → flat AND with 3 children (NOT items preserved)."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        compound = ~c1 & ~c2 & c3
        assert compound.logic == "AND"
        assert len(compound.conditions) == 3
        assert isinstance(compound.conditions[0], NotCondition)
        assert isinstance(compound.conditions[1], NotCondition)
        assert isinstance(compound.conditions[2], Condition)


# ── STRING_PROP / case_sensitive ────────────────────────────────


class TestStringProp:
    """Test case_sensitive → STRING_PROP emission."""

    def test_default_none_no_string_prop(self):
        """Default (None) → no STRING_PROP in output."""
        c = Condition("Name", Operator.EQ, "Alice")
        result = c.build()
        assert "STRING_PROP" not in result

    def test_case_sensitive_true(self):
        c = Condition("Name", Operator.EQ, "Alice", case_sensitive=True)
        result = c.build()
        assert result["STRING_PROP"] == {"CASE": "CASE-SENSITIVE"}

    def test_case_insensitive_false(self):
        c = Condition("Name", Operator.EQ, "Alice", case_sensitive=False)
        result = c.build()
        assert result["STRING_PROP"] == {"CASE": "CASE-INSENSITIVE"}

    def test_compound_inherits_from_children(self):
        c1 = Condition("A", Operator.EQ, "x", case_sensitive=True)
        c2 = Condition("B", Operator.EQ, "y")
        compound = c1 & c2
        result = compound.build()
        assert result["STRING_PROP"] == {"CASE": "CASE-SENSITIVE"}

    def test_not_inherits_from_inner(self):
        c = Condition("A", Operator.EQ, "x", case_sensitive=False)
        negated = ~c
        result = negated.build()
        assert result["STRING_PROP"] == {"CASE": "CASE-INSENSITIVE"}

    def test_compound_no_string_prop_when_children_default(self):
        c1 = Condition("A", Operator.EQ, "x")
        c2 = Condition("B", Operator.EQ, "y")
        compound = c1 & c2
        result = compound.build()
        assert "STRING_PROP" not in result

    def test_string_prop_not_in_inner_leaves(self):
        """STRING_PROP should only appear at top level, not inside AND/OR children."""
        c1 = Condition("A", Operator.EQ, "x", case_sensitive=True)
        c2 = Condition("B", Operator.EQ, "y")
        compound = c1 & c2
        result = compound.build()
        # Top level should have STRING_PROP
        assert "STRING_PROP" in result
        # Children should NOT have STRING_PROP
        for child in result["AND"]:
            assert "STRING_PROP" not in child


# ── Validation ──────────────────────────────────────────────────


class TestValidation:
    """Test construction-time validation."""

    def test_empty_column_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            Condition("", Operator.EQ, "x")

    def test_none_column_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            Condition(None, Operator.EQ, "x")  # type: ignore[arg-type]

    def test_null_operator_with_value_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Condition("Notes", Operator.IS_EMPTY, "unused_value")
            assert len(w) == 1
            assert "does not use a value" in str(w[0].message)

    def test_non_null_operator_without_value_raises(self):
        with pytest.raises(ValueError, match="requires a value"):
            Condition("Sales", Operator.GTE)

    def test_single_element_compound_raises(self):
        c = Condition("A", Operator.GT, 1)
        with pytest.raises(ValueError, match="at least 2"):
            CompoundCondition("AND", [c])

    def test_empty_conditions_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            CompoundCondition("AND", [])

    def test_bad_logic_raises(self):
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        with pytest.raises(ValueError, match="must be 'AND' or 'OR'"):
            CompoundCondition("XOR", [c1, c2])

    def test_non_condition_element_raises(self):
        c = Condition("A", Operator.GT, 1)
        with pytest.raises(TypeError, match="must be a Condition"):
            CompoundCondition("AND", [c, "not a condition"])  # type: ignore[list-item]

    def test_not_condition_bad_type_raises(self):
        with pytest.raises(TypeError, match="requires a Condition"):
            NotCondition("not a condition")  # type: ignore[arg-type]


# ── Precedence ──────────────────────────────────────────────────


class TestPrecedence:
    """Test Python operator precedence: & binds tighter than |."""

    def test_and_binds_tighter_than_or(self):
        """c1 | c2 & c3 == c1 | (c2 & c3) because & has higher precedence."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        result = c1 | c2 & c3
        # Should be OR([c1, AND([c2, c3])])
        assert isinstance(result, CompoundCondition)
        assert result.logic == "OR"
        assert len(result.conditions) == 2
        assert isinstance(result.conditions[0], Condition)
        assert isinstance(result.conditions[1], CompoundCondition)
        assert result.conditions[1].logic == "AND"

    def test_explicit_parens_override(self):
        """(c1 | c2) & c3 == AND([OR([c1, c2]), c3])."""
        c1 = Condition("A", Operator.GT, 1)
        c2 = Condition("B", Operator.LT, 2)
        c3 = Condition("C", Operator.EQ, 3)
        result = (c1 | c2) & c3
        assert isinstance(result, CompoundCondition)
        assert result.logic == "AND"
        assert len(result.conditions) == 2
        assert isinstance(result.conditions[0], CompoundCondition)
        assert result.conditions[0].logic == "OR"
        assert isinstance(result.conditions[1], Condition)
