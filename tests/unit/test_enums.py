"""Unit tests for all enum classes — correct values and importability."""

from __future__ import annotations

import pytest

from mammoth.models.pipeline import (
    AggregateFunction,
    ColumnType,
    DateComponent,
    DateDiffUnit,
    FillDirection,
    FilterType,
    JoinType,
    JsonType,
    MathOperator,
    Operator,
    ProviderType,
    SortDirection,
    SubstringDirection,
    TaskType,
    TextCase,
    ValueType,
    WindowFunction,
    WindowRange,
)


class TestOperatorEnum:
    def test_comparison_operators(self):
        assert Operator.GT == "GT"
        assert Operator.LT == "LT"
        assert Operator.GTE == "GTE"
        assert Operator.LTE == "LTE"
        assert Operator.EQ == "EQ"
        assert Operator.NE == "NE"

    def test_string_operators(self):
        assert Operator.CONTAINS == "CONTAINS"
        assert Operator.NOT_CONTAINS == "NOT_CONTAINS"
        assert Operator.STARTS_WITH == "STARTS_WITH"
        assert Operator.ENDS_WITH == "ENDS_WITH"

    def test_list_operators(self):
        assert Operator.IN_LIST == "IN_LIST"
        assert Operator.NOT_IN_LIST == "NOT_IN_LIST"

    def test_null_operators(self):
        assert Operator.IS_EMPTY == "IS_EMPTY"
        assert Operator.IS_NOT_EMPTY == "IS_NOT_EMPTY"


class TestColumnType:
    def test_values(self):
        assert ColumnType.TEXT == "TEXT"
        assert ColumnType.NUMERIC == "NUMERIC"
        assert ColumnType.DATE == "DATE"

    def test_is_string(self):
        assert isinstance(ColumnType.TEXT, str)


class TestJoinType:
    def test_values(self):
        assert JoinType.INNER == "INNER"
        assert JoinType.LEFT == "LEFT"
        assert JoinType.RIGHT == "RIGHT"
        assert JoinType.OUTER == "OUTER"


class TestTextCase:
    def test_values(self):
        assert TextCase.UPPER == "UPPER"
        assert TextCase.LOWER == "LOWER"
        assert TextCase.TITLE == "TITLE"


class TestDateComponent:
    def test_all_values_lowercase(self):
        for member in DateComponent:
            assert member.value == member.value.lower(), f"{member.name} value should be lowercase"

    def test_common_values(self):
        assert DateComponent.YEAR == "year"
        assert DateComponent.MONTH == "month"
        assert DateComponent.DAY == "day"
        assert DateComponent.WEEKDAY_TEXT == "weekday_text"


class TestDateDiffUnit:
    def test_all_values_uppercase(self):
        for member in DateDiffUnit:
            assert member.value == member.value.upper(), f"{member.name} value should be uppercase"

    def test_common_values(self):
        assert DateDiffUnit.YEAR == "YEAR"
        assert DateDiffUnit.MONTH == "MONTH"
        assert DateDiffUnit.DAY == "DAY"


class TestWindowFunction:
    def test_ranking_functions(self):
        assert WindowFunction.ROW_NUMBER == "ROW_NUMBER"
        assert WindowFunction.RANK == "RANK"
        assert WindowFunction.DENSE_RANK == "DENSE_RANK"

    def test_aggregate_functions(self):
        assert WindowFunction.SUM == "SUM"
        assert WindowFunction.AVG == "AVG"
        assert WindowFunction.COUNT == "COUNT"


class TestAggregateFunction:
    def test_values(self):
        assert AggregateFunction.SUM == "SUM"
        assert AggregateFunction.AVG == "AVG"
        assert AggregateFunction.COUNT == "COUNT"
        assert AggregateFunction.COUNT_DISTINCT == "COUNT_DISTINCT"
        assert AggregateFunction.MEDIAN == "MEDIAN"


class TestFilterType:
    def test_values(self):
        assert FilterType.SHOW == "SHOW"
        assert FilterType.REMOVE == "REMOVE"


class TestFillDirection:
    def test_values(self):
        assert FillDirection.FIRST_VALUE == "FIRST_VALUE"
        assert FillDirection.LAST_VALUE == "LAST_VALUE"


class TestSortDirection:
    def test_values(self):
        assert SortDirection.ASC == "ASC"
        assert SortDirection.DESC == "DESC"


class TestMathOperator:
    def test_values(self):
        assert MathOperator.ADD == "+"
        assert MathOperator.SUBTRACT == "-"
        assert MathOperator.MULTIPLY == "*"
        assert MathOperator.DIVIDE == "/"
        assert MathOperator.MODULO == "%"


class TestSubstringDirection:
    def test_values(self):
        assert SubstringDirection.START == "START"
        assert SubstringDirection.END == "END"
        assert SubstringDirection.LEFT == "LEFT"
        assert SubstringDirection.RIGHT == "RIGHT"


class TestJsonType:
    def test_values(self):
        assert JsonType.OBJECT == "OBJECT"
        assert JsonType.LIST == "LIST"


class TestWindowRange:
    def test_values(self):
        assert WindowRange.UNBOUNDED == "UNBOUNDED"
        assert WindowRange.RUNNING == "RUNNING"


class TestEnumsAreStrings:
    """All enums should be str subclasses for JSON serialization."""

    @pytest.mark.parametrize(
        "enum_cls",
        [
            ColumnType,
            JoinType,
            TextCase,
            DateComponent,
            DateDiffUnit,
            WindowFunction,
            AggregateFunction,
            FilterType,
            FillDirection,
            SortDirection,
            MathOperator,
            SubstringDirection,
            JsonType,
            WindowRange,
            Operator,
            ValueType,
            ProviderType,
            TaskType,
        ],
    )
    def test_str_subclass(self, enum_cls):
        for member in enum_cls:
            assert isinstance(
                member, str
            ), f"{enum_cls.__name__}.{member.name} is not a str subclass"
