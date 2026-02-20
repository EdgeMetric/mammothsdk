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


# ── New features: value_is_column, component, truncate ─────────


class TestValueIsColumn:
    """Test column-to-column comparison."""

    def test_value_is_column(self):
        c = Condition("Sales", Operator.GT, "Cost", value_is_column=True)
        col_map = {"Sales": "column_1", "Cost": "column_2"}
        result = c.build(col_map)
        assert result["column_1"]["GT"] == {"COLUMN": "column_2"}

    def test_value_is_column_without_map(self):
        c = Condition("Sales", Operator.GT, "Cost", value_is_column=True)
        result = c.build()
        assert result["Sales"]["GT"] == {"COLUMN": "Cost"}


class TestDateComponentCondition:
    """Test date component wrapped values."""

    def test_component_month_text(self):
        c = Condition("Date", Operator.EQ, "October", component="month_text")
        col_map = {"Date": "column_d"}
        result = c.build(col_map)
        assert result["column_d"]["EQ"] == {"VALUE": {"COMPONENT": "month_text", "VALUE": "October"}}

    def test_component_year(self):
        c = Condition("Date", Operator.GTE, 2020, component="year")
        result = c.build({"Date": "col_d"})
        assert result["col_d"]["GTE"] == {"VALUE": {"COMPONENT": "year", "VALUE": 2020}}


class TestDateTruncateCondition:
    """Test date truncation wrapped values."""

    def test_truncate_day(self):
        c = Condition("Date", Operator.GT, "2021-02-28", truncate="DAY")
        col_map = {"Date": "column_d"}
        result = c.build(col_map)
        assert result["column_d"]["GT"] == {"VALUE": {"TRUNCATE": "DAY", "VALUE": "2021-02-28"}}

    def test_truncate_month(self):
        c = Condition("Date", Operator.LTE, "2021-06-30", truncate="MONTH")
        result = c.build({"Date": "col_d"})
        assert result["col_d"]["LTE"] == {"VALUE": {"TRUNCATE": "MONTH", "VALUE": "2021-06-30"}}


class TestAdditionalOperators:
    """Test additional operator types."""

    def test_contains_operator(self):
        c = Condition("Name", Operator.CONTAINS, "Smith")
        result = c.build({"Name": "col_n"})
        assert result["col_n"]["CONTAINS"] == {"VALUE": ["Smith"]}

    def test_starts_with(self):
        c = Condition("Name", Operator.STARTS_WITH, "A")
        result = c.build({"Name": "col_n"})
        assert result["col_n"]["STARTS_WITH"] == {"VALUE": "A"}

    def test_ends_with(self):
        c = Condition("Name", Operator.ENDS_WITH, "son")
        result = c.build({"Name": "col_n"})
        assert result["col_n"]["ENDS_WITH"] == {"VALUE": "son"}

    def test_is_maxval(self):
        c = Condition("Sales", Operator.IS_MAXVAL)
        result = c.build({"Sales": "col_s"})
        assert result["col_s"]["IS_MAXVAL"] is True

    def test_is_minval(self):
        c = Condition("Sales", Operator.IS_MINVAL)
        result = c.build({"Sales": "col_s"})
        assert result["col_s"]["IS_MINVAL"] is True


# ── TEXT EQ/NE → IN_LIST/NOT_IN_LIST remap workaround ─────────


class TestTextEqNeRemap:
    """Backend falsely rejects TEXT + EQ/NE as 'type mismatch'.

    The workaround remaps EQ → IN_LIST and NE → NOT_IN_LIST (single-element)
    when column_types indicates a TEXT column.
    """

    def test_eq_text_remaps_to_in_list(self):
        c = Condition("Name", Operator.EQ, "Alice")
        col_map = {"Name": "col_n"}
        col_types = {"Name": "TEXT"}
        result = c.build(col_map, col_types)
        assert result == {"col_n": {"IN_LIST": {"VALUE": ["Alice"]}}}

    def test_ne_text_remaps_to_not_in_list(self):
        c = Condition("Name", Operator.NE, "Bob")
        col_map = {"Name": "col_n"}
        col_types = {"Name": "TEXT"}
        result = c.build(col_map, col_types)
        assert result == {"col_n": {"NOT_IN_LIST": {"VALUE": ["Bob"]}}}

    def test_eq_numeric_unchanged(self):
        c = Condition("Sales", Operator.EQ, 100)
        col_map = {"Sales": "col_s"}
        col_types = {"Sales": "NUMERIC"}
        result = c.build(col_map, col_types)
        assert result == {"col_s": {"EQ": {"VALUE": 100}}}

    def test_eq_no_column_types_unchanged(self):
        """Without column_types, EQ stays EQ (backward compat)."""
        c = Condition("Name", Operator.EQ, "Alice")
        col_map = {"Name": "col_n"}
        result = c.build(col_map)
        assert result == {"col_n": {"EQ": {"VALUE": "Alice"}}}

    def test_eq_column_types_none_unchanged(self):
        """Explicit None column_types, EQ stays EQ."""
        c = Condition("Name", Operator.EQ, "Alice")
        result = c.build({"Name": "col_n"}, None)
        assert result == {"col_n": {"EQ": {"VALUE": "Alice"}}}

    def test_value_is_column_no_remap(self):
        """Column-to-column EQ should NOT be remapped."""
        c = Condition("Name", Operator.EQ, "Other", value_is_column=True)
        col_map = {"Name": "col_n", "Other": "col_o"}
        col_types = {"Name": "TEXT", "Other": "TEXT"}
        result = c.build(col_map, col_types)
        assert result == {"col_n": {"EQ": {"COLUMN": "col_o"}}}

    def test_compound_with_text_eq(self):
        """AND/OR propagates remap to children."""
        c1 = Condition("Name", Operator.EQ, "Alice")
        c2 = Condition("Sales", Operator.GTE, 100)
        compound = c1 & c2
        col_map = {"Name": "col_n", "Sales": "col_s"}
        col_types = {"Name": "TEXT", "Sales": "NUMERIC"}
        result = compound.build(col_map, col_types)
        assert "AND" in result
        assert result["AND"][0] == {"col_n": {"IN_LIST": {"VALUE": ["Alice"]}}}
        assert result["AND"][1] == {"col_s": {"GTE": {"VALUE": 100}}}

    def test_not_with_text_eq(self):
        """NOT wrapping a TEXT EQ should remap the inner condition."""
        c = Condition("Name", Operator.EQ, "Alice")
        negated = ~c
        col_map = {"Name": "col_n"}
        col_types = {"Name": "TEXT"}
        result = negated.build(col_map, col_types)
        assert result == {"NOT": {"col_n": {"IN_LIST": {"VALUE": ["Alice"]}}}}

    def test_date_column_eq_unchanged(self):
        """DATE column + EQ should not be remapped."""
        c = Condition("Date", Operator.EQ, "2021-01-01")
        col_map = {"Date": "col_d"}
        col_types = {"Date": "DATE"}
        result = c.build(col_map, col_types)
        assert result == {"col_d": {"EQ": {"VALUE": "2021-01-01"}}}
