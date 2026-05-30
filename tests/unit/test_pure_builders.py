"""Unit tests for the pure parameter builders (``mammoth._pure``).

Every ``build_<op>_params`` is exercised against the **typed spec** inputs the
public View methods take (ConversionSpec, CopySpec, SetValue, ...), asserting
the exact backend dict it emits. A deterministic ``name_gen`` makes generated
INTERNAL_NAMEs reproducible so the asserts are byte-exact.

Coverage goal: 100% line + branch on ``mammoth/_pure/`` — each builder's
new/existing/neither destination paths, optional CONDITION, and enum branches
are covered explicitly, plus the BE-conformance corrections (CONVERT FORMAT
dict, UNNEST/JSON_HANDLE INTERNAL_NAME, literal-fill as SET+IS_EMPTY).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from mammoth._pure import builders as b
from mammoth._pure.resolve import (
    build_as_column,
    build_condition,
    next_internal_name,
    resolve_column,
    resolve_columns,
    resolve_order_by,
)
from mammoth.condition import Condition
from mammoth.exceptions import MammothColumnError
from mammoth.models.pipeline import (
    AggregateFunction,
    AggregationSpec,
    BulkReplaceMapping,
    ColumnType,
    ConversionSpec,
    CopySpec,
    CrosstabSpec,
    DateComponent,
    DateDelta,
    DateDiffUnit,
    FillDirection,
    FilterType,
    JoinKeySpec,
    JoinSelectSpec,
    JoinType,
    JsonExtractionSpec,
    JsonOpType,
    JsonType,
    Operator,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
    WindowFunction,
    WindowRange,
)

pytestmark = pytest.mark.unit

# ── Fixtures: column metadata ──────────────────────────────────
COLS = {"Sales": "c1", "Region": "c2", "Order Date": "c3", "Notes": "c4", "End Date": "c5"}
INTERNALS = ["c1", "c2", "c3", "c4", "c5"]
TYPES = {
    "Sales": "NUMERIC",
    "Region": "TEXT",
    "Order Date": "DATE",
    "Notes": "TEXT",
    "End Date": "DATE",
}


def gen() -> Callable[[], str]:
    """A deterministic internal-name generator: gen1, gen2, gen3, ..."""
    counter = {"n": 0}

    def _g() -> str:
        counter["n"] += 1
        return f"gen{counter['n']}"

    return _g


def cond(value: int = 1000) -> Condition:
    """A simple reusable Condition on the NUMERIC Sales column."""
    return Condition("Sales", Operator.GTE, value)


def built_cond(value: int = 1000) -> dict:
    """The built form of :func:`cond` (fresh dict each call)."""
    return Condition("Sales", Operator.GTE, value).build(COLS, TYPES)


# ===============================================================
# resolve.py
# ===============================================================


class TestResolve:
    def test_resolve_column_display_name(self) -> None:
        assert resolve_column("Sales", COLS, INTERNALS) == "c1"

    def test_resolve_column_passthrough_internal(self) -> None:
        assert resolve_column("c3", COLS, INTERNALS) == "c3"

    def test_resolve_column_unknown_raises(self) -> None:
        with pytest.raises(MammothColumnError):
            resolve_column("Nope", COLS, INTERNALS)

    def test_resolve_columns(self) -> None:
        assert resolve_columns(["Sales", "c2"], COLS, INTERNALS) == ["c1", "c2"]

    def test_next_internal_name_custom(self) -> None:
        assert next_internal_name(gen()) == "gen1"

    def test_next_internal_name_default(self) -> None:
        name = next_internal_name()
        assert name.startswith("column_") and len(name) == len("column_") + 10

    def test_build_as_column_with_name_gen(self) -> None:
        assert build_as_column("New", ColumnType.NUMERIC, name_gen=gen()) == {
            "COLUMN": "New",
            "TYPE": "NUMERIC",
            "INTERNAL_NAME": "gen1",
        }

    def test_build_as_column_explicit_internal(self) -> None:
        assert build_as_column("New", "text", internal_name="fixed") == {
            "COLUMN": "New",
            "TYPE": "TEXT",
            "INTERNAL_NAME": "fixed",
        }

    def test_build_as_column_default_internal(self) -> None:
        spec = build_as_column("New")
        assert spec["COLUMN"] == "New" and spec["TYPE"] == "TEXT"
        assert spec["INTERNAL_NAME"].startswith("column_")

    def test_build_condition_none(self) -> None:
        assert build_condition(None, COLS) is None

    def test_build_condition_raw_dict_passthrough(self) -> None:
        raw = {"c1": {"GTE": {"VALUE": 1}}}
        assert build_condition(raw, COLS) is raw

    def test_build_condition_object(self) -> None:
        assert build_condition(cond(), COLS, TYPES) == built_cond()

    def test_resolve_order_by_with_direction(self) -> None:
        assert resolve_order_by([["Sales", SortDirection.DESC]], COLS) == [["c1", "DESC"]]

    def test_resolve_order_by_default_asc(self) -> None:
        assert resolve_order_by([["Sales"]], COLS) == [["c1", "ASC"]]

    def test_resolve_order_by_passthrough_unknown(self) -> None:
        assert resolve_order_by([["unknown_internal", "ASC"]], COLS) == [
            ["unknown_internal", "ASC"]
        ]


# ===============================================================
# Column operations
# ===============================================================


class TestColumnOps:
    def test_add_column(self) -> None:
        assert b.build_add_column_params("Score", ColumnType.NUMERIC, gen()) == {
            "ADD_COLUMN": [{"COLUMN": "Score", "TYPE": "NUMERIC", "INTERNAL_NAME": "gen1"}]
        }

    def test_add_column_default_type(self) -> None:
        spec = b.build_add_column_params("Notes2")
        assert spec["ADD_COLUMN"][0]["TYPE"] == "TEXT"

    def test_delete(self) -> None:
        assert b.build_delete_params(["Sales", "Region"], COLS, INTERNALS) == {
            "DELETE": ["c1", "c2"]
        }

    def test_copy_with_as_and_condition(self) -> None:
        copies = [
            CopySpec(
                source="Sales", as_name="Sales Copy", type=ColumnType.NUMERIC, condition=cond()
            )
        ]
        assert b.build_copy_params(copies, COLS, INTERNALS, TYPES, gen()) == {
            "COPY": [
                {
                    "SOURCE": "c1",
                    "AS": {"COLUMN": "Sales Copy", "TYPE": "NUMERIC", "INTERNAL_NAME": "gen1"},
                    "CONDITION": built_cond(),
                }
            ],
            "VERSION": 2,
        }

    def test_copy_default_as_no_condition(self) -> None:
        spec = b.build_copy_params([CopySpec(source="Region")], COLS, INTERNALS, name_gen=gen())
        item = spec["COPY"][0]
        assert item["SOURCE"] == "c2"
        assert item["AS"]["COLUMN"] == "Region Copy"
        assert "CONDITION" not in item
        assert spec["VERSION"] == 2

    def test_combine_new_column_with_condition(self) -> None:
        spec = b.build_combine_params(
            ["Region", "Notes"],
            COLS,
            INTERNALS,
            new_column="Combo",
            separator="-",
            condition=cond(),
            column_types=TYPES,
            name_gen=gen(),
        )
        assert spec == {
            "COMBINE": {
                "SOURCE": [{"COLUMN": "c2"}, {"STRING": "-"}, {"COLUMN": "c4"}],
                "AS": {"COLUMN": "Combo", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
            },
            "CONDITION": built_cond(),
        }

    def test_combine_existing_column(self) -> None:
        spec = b.build_combine_params(["Region"], COLS, INTERNALS, existing_column="Notes")
        assert spec["COMBINE"]["DESTINATION"] == "c4"
        assert "AS" not in spec["COMBINE"]
        assert "CONDITION" not in spec

    def test_combine_neither_destination(self) -> None:
        spec = b.build_combine_params(["Region", "Notes"], COLS, INTERNALS)
        assert "AS" not in spec["COMBINE"] and "DESTINATION" not in spec["COMBINE"]

    def test_convert_with_format_dict(self) -> None:
        conversions = [ConversionSpec(column="Order Date", to=ColumnType.DATE, format="MM/DD/YYYY")]
        assert b.build_convert_params(conversions, COLS, INTERNALS) == {
            "CONVERT": [
                {"SOURCE": "c3", "TO_TYPE": "DATE", "FORMAT": {"date_format": "MM/DD/YYYY"}}
            ]
        }

    def test_convert_no_format(self) -> None:
        conversions = [ConversionSpec(column="Sales", to=ColumnType.TEXT)]
        spec = b.build_convert_params(conversions, COLS, INTERNALS)
        assert spec == {"CONVERT": [{"SOURCE": "c1", "TO_TYPE": "TEXT"}]}
        assert "FORMAT" not in spec["CONVERT"][0]


# ===============================================================
# Filter / Set
# ===============================================================


class TestFilterSet:
    def test_filter_show(self) -> None:
        spec = b.build_filter_params(cond(), COLS, TYPES, FilterType.SHOW, prompt="big sales")
        expected = built_cond()
        expected["FILTER_TYPE"] = "SHOW"
        expected["PROMPT"] = "big sales"
        assert spec == {"SELECT": "ALL", "CONDITION": expected}

    def test_filter_remove(self) -> None:
        spec = b.build_filter_params(cond(), COLS, TYPES, FilterType.REMOVE)
        assert spec["CONDITION"]["FILTER_TYPE"] == "REMOVE"
        assert spec["CONDITION"]["PROMPT"] == ""

    def test_filter_none_condition_branch(self) -> None:
        # Covers the `not isinstance(built, dict)` branch (built is None).
        spec = b.build_filter_params(None, COLS)  # type: ignore[arg-type]
        assert spec == {"SELECT": "ALL", "CONDITION": None}

    def test_set_new_column_value_condition_and_global(self) -> None:
        values = [SetValue("High", condition=cond(10000)), SetValue("Low")]
        spec = b.build_set_params(
            values,
            COLS,
            new_column="Risk",
            column_type=ColumnType.TEXT,
            condition=cond(),
            column_types=TYPES,
            name_gen=gen(),
        )
        assert spec == {
            "SET": {
                "VALUES": [
                    {"PROVIDER_TYPE": "FIXED", "PROVIDER": "High", "CONDITION": built_cond(10000)},
                    {"PROVIDER_TYPE": "FIXED", "PROVIDER": "Low"},
                ],
                "AS": {"COLUMN": "Risk", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
            },
            "VERSION": 2,
            "CONDITION": built_cond(),
        }

    def test_set_existing_column_no_global_condition(self) -> None:
        spec = b.build_set_params(
            [SetValue("X")],
            COLS,
            existing_column="Notes",
            internal_names=INTERNALS,
        )
        assert spec["SET"]["DESTINATION"] == "c4"
        assert "AS" not in spec["SET"]
        assert "CONDITION" not in spec

    def test_set_neither_destination(self) -> None:
        spec = b.build_set_params([SetValue("X")], COLS)
        assert "AS" not in spec["SET"] and "DESTINATION" not in spec["SET"]


# ===============================================================
# Math
# ===============================================================


class TestMath:
    def test_math_new_column_with_condition(self) -> None:
        spec = b.build_math_params(
            "Sales * 2",
            COLS,
            new_column="Doubled",
            condition=cond(),
            column_types=TYPES,
            name_gen=gen(),
        )
        assert spec["MATH"]["AS"] == {
            "COLUMN": "Doubled",
            "TYPE": "NUMERIC",
            "INTERNAL_NAME": "gen1",
        }
        assert "EXPRESSION" in spec["MATH"]
        assert spec["CONDITION"] == built_cond()

    def test_math_existing_column(self) -> None:
        spec = b.build_math_params(
            "Sales + 1", COLS, existing_column="Sales", internal_names=INTERNALS
        )
        assert spec["MATH"]["DESTINATION"] == "c1"
        assert "CONDITION" not in spec

    def test_math_neither(self) -> None:
        spec = b.build_math_params("Sales * 2", COLS)
        assert "AS" not in spec["MATH"] and "DESTINATION" not in spec["MATH"]


# ===============================================================
# Text operations
# ===============================================================


class TestTextOps:
    def test_text_transform_case_and_condition(self) -> None:
        spec = b.build_text_transform_params(
            ["Region"],
            COLS,
            INTERNALS,
            case=TextCase.UPPER,
            trim=True,
            condition=cond(),
            column_types=TYPES,
        )
        assert spec == {
            "TEXT_TRANSFORM": {"SOURCE": ["c2"], "TRIM": True, "CASE": "UPPER"},
            "CONDITION": built_cond(),
        }

    def test_text_transform_no_case_no_condition(self) -> None:
        spec = b.build_text_transform_params(["Region", "Notes"], COLS, INTERNALS, trim=True)
        assert spec == {"TEXT_TRANSFORM": {"SOURCE": ["c2", "c4"], "TRIM": True}}

    def test_replace_with_condition(self) -> None:
        spec = b.build_replace_params(
            ["Region"],
            COLS,
            INTERNALS,
            find="NYC",
            replace="New York",
            match_case=True,
            condition=cond(),
            column_types=TYPES,
        )
        assert spec["REPLACE"]["VALUE_PAIR"] == [
            {"SEARCH_VALUE": "NYC", "REPLACE_VALUE": "New York"}
        ]
        assert spec["REPLACE"]["MATCH_CASE"] is True
        assert spec["CONDITION"] == built_cond()

    def test_replace_no_condition(self) -> None:
        spec = b.build_replace_params(["Region"], COLS, INTERNALS, find="a", replace="b")
        assert "CONDITION" not in spec
        assert spec["REPLACE"]["MATCH_CASE"] is False

    def test_bulk_replace_with_condition(self) -> None:
        mapping = [BulkReplaceMapping(search=["6 inch", "8 inch"], replace="CAKE")]
        spec = b.build_bulk_replace_params(
            ["Notes"],
            COLS,
            INTERNALS,
            mapping,
            condition=cond(),
            column_types=TYPES,
        )
        assert spec["REPLACE"]["MAPPING"] == [
            {"SEARCH_VALUE": ["6 inch", "8 inch"], "REPLACE_VALUE": "CAKE"}
        ]
        assert spec["REPLACE"]["MATCH_CASE"] is True
        assert spec["CONDITION"] == built_cond()

    def test_bulk_replace_no_condition(self) -> None:
        mapping = [BulkReplaceMapping(search=["x"], replace="y")]
        spec = b.build_bulk_replace_params(["Notes"], COLS, INTERNALS, mapping)
        assert "CONDITION" not in spec

    def test_split(self) -> None:
        new_cols = [SplitColumnSpec("First"), SplitColumnSpec("Last", type=ColumnType.TEXT)]
        spec = b.build_split_params("Notes", " ", new_cols, COLS, INTERNALS, gen())
        assert spec == {
            "SPLIT": {
                "SOURCE": "c4",
                "DELIMITER": " ",
                "AS": [
                    {"COLUMN": "First", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
                    {"COLUMN": "Last", "TYPE": "TEXT", "INTERNAL_NAME": "gen2"},
                ],
            }
        }

    def test_substring_regex_new_column(self) -> None:
        spec = b.build_substring_params(
            "Notes",
            COLS,
            INTERNALS,
            regex_pattern="@(.+)",
            regex_invert=True,
            new_column="Domain",
            name_gen=gen(),
        )
        assert spec["SUBSTRING"]["REGEX"] == {"EXPRESSION": "@(.+)", "INVERT": True}
        assert spec["SUBSTRING"]["AS"]["COLUMN"] == "Domain"

    def test_substring_direction_numchar_existing(self) -> None:
        spec = b.build_substring_params(
            "Notes",
            COLS,
            INTERNALS,
            direction=SubstringDirection.START,
            num_char=3,
            existing_column="Region",
        )
        assert spec["SUBSTRING"]["DIRECTION"] == "START"
        assert spec["SUBSTRING"]["NUM_CHAR"] == 3
        assert spec["SUBSTRING"]["DESTINATION"] == "c2"

    def test_substring_charposition_with_condition_neither_dest(self) -> None:
        spec = b.build_substring_params(
            "Notes",
            COLS,
            INTERNALS,
            direction=SubstringDirection.LEFT,
            char_position=5,
            condition=cond(),
            column_types=TYPES,
        )
        assert spec["SUBSTRING"]["CHAR_POSITION"] == 5
        assert "AS" not in spec["SUBSTRING"] and "DESTINATION" not in spec["SUBSTRING"]
        assert spec["CONDITION"] == built_cond()


# ===============================================================
# Date operations
# ===============================================================


class TestDateOps:
    def test_extract_date_text_component_new(self) -> None:
        spec = b.build_extract_date_params(
            "Order Date",
            DateComponent.WEEKDAY_TEXT,
            COLS,
            INTERNALS,
            new_column="Weekday",
            name_gen=gen(),
        )
        assert spec["EXTRACT_DATE"]["COMPONENT"] == "weekday_text"
        assert spec["EXTRACT_DATE"]["AS"]["TYPE"] == "TEXT"

    def test_extract_date_numeric_component_existing(self) -> None:
        spec = b.build_extract_date_params(
            "Order Date",
            DateComponent.YEAR,
            COLS,
            INTERNALS,
            existing_column="Sales",
        )
        assert spec["EXTRACT_DATE"]["COMPONENT"] == "year"
        assert spec["EXTRACT_DATE"]["DESTINATION"] == "c1"

    def test_extract_date_neither(self) -> None:
        spec = b.build_extract_date_params("Order Date", DateComponent.MONTH, COLS, INTERNALS)
        assert "AS" not in spec["EXTRACT_DATE"] and "DESTINATION" not in spec["EXTRACT_DATE"]

    def test_date_diff_new(self) -> None:
        spec = b.build_date_diff_params(
            DateDiffUnit.DAY,
            "Order Date",
            "End Date",
            COLS,
            INTERNALS,
            new_column="Duration",
            name_gen=gen(),
        )
        assert spec["DATE_DIFF"]["COMPONENT"] == "DAY"
        assert spec["DATE_DIFF"]["MINUEND"] == {"TYPE": "COLUMN", "VALUE": "c5"}
        assert spec["DATE_DIFF"]["SUBTRAHEND"] == {"TYPE": "COLUMN", "VALUE": "c3"}
        assert spec["DATE_DIFF"]["AS"]["COLUMN"] == "Duration"

    def test_date_diff_existing(self) -> None:
        spec = b.build_date_diff_params(
            DateDiffUnit.MONTH,
            "Order Date",
            "End Date",
            COLS,
            INTERNALS,
            existing_column="Sales",
        )
        assert spec["DATE_DIFF"]["DESTINATION"] == "c1"

    def test_date_diff_neither(self) -> None:
        spec = b.build_date_diff_params(DateDiffUnit.DAY, "Order Date", "End Date", COLS, INTERNALS)
        assert "AS" not in spec["DATE_DIFF"] and "DESTINATION" not in spec["DATE_DIFF"]

    def test_increment_date_new_with_condition(self) -> None:
        spec = b.build_increment_date_params(
            "Order Date",
            DateDelta(days=30, months=-1),
            COLS,
            INTERNALS,
            new_column="Due",
            condition=cond(),
            column_types=TYPES,
            name_gen=gen(),
        )
        assert spec["INCREMENT_DATE"]["DELTA"] == {"MONTH": -1, "DAY": 30}
        assert spec["INCREMENT_DATE"]["AS"]["TYPE"] == "DATE"
        assert spec["CONDITION"] == built_cond()

    def test_increment_date_existing_no_condition(self) -> None:
        spec = b.build_increment_date_params(
            "Order Date",
            DateDelta(years=1),
            COLS,
            INTERNALS,
            existing_column="Order Date",
        )
        assert spec["INCREMENT_DATE"]["DESTINATION"] == "c3"
        assert "CONDITION" not in spec

    def test_increment_date_neither(self) -> None:
        spec = b.build_increment_date_params("Order Date", DateDelta(days=1), COLS, INTERNALS)
        assert "AS" not in spec["INCREMENT_DATE"] and "DESTINATION" not in spec["INCREMENT_DATE"]


# ===============================================================
# Row operations
# ===============================================================


class TestRowOps:
    def test_fill_with_partition_and_order(self) -> None:
        spec = b.build_fill_params(
            "Sales",
            FillDirection.LAST_VALUE,
            COLS,
            INTERNALS,
            partition_by="Region",
            order_by=[["Order Date", SortDirection.ASC]],
        )
        assert spec == {
            "FILL": {
                "COLUMN": "c1",
                "WITH": "LAST_VALUE",
                "PARTITION_BY": "c2",
                "ORDER_BY": [["c3", "ASC"]],
            }
        }

    def test_fill_minimal(self) -> None:
        spec = b.build_fill_params("Sales", FillDirection.FIRST_VALUE, COLS, INTERNALS)
        assert spec == {"FILL": {"COLUMN": "c1", "WITH": "FIRST_VALUE"}}

    def test_fill_value_set_is_empty(self) -> None:
        assert b.build_fill_value_params("Sales", 0, COLS, INTERNALS) == {
            "SET": {
                "DESTINATION": "c1",
                "VALUES": [
                    {
                        "PROVIDER_TYPE": "FIXED",
                        "PROVIDER": 0,
                        "CONDITION": {"c1": {"IS_EMPTY": True}},
                    }
                ],
            },
            "VERSION": 2,
        }

    def test_limit_with_order(self) -> None:
        spec = b.build_limit_params(10, COLS, order_by=[["Sales", SortDirection.DESC]])
        assert spec == {"LIMIT": {"LIMIT": 10, "BOTTOM": False}, "ORDER_BY": [["c1", "DESC"]]}

    def test_limit_bottom_no_order(self) -> None:
        assert b.build_limit_params(5, COLS, bottom=True) == {"LIMIT": {"LIMIT": 5, "BOTTOM": True}}

    def test_discard_duplicates_with_ignore(self) -> None:
        assert b.build_discard_duplicates_params(COLS, INTERNALS, ["Notes"]) == {
            "DISCARD_DUPLICATES": True,
            "IGNORE_COLUMNS": ["c4"],
        }

    def test_discard_duplicates_all(self) -> None:
        assert b.build_discard_duplicates_params(COLS, INTERNALS) == {
            "DISCARD_DUPLICATES": True,
            "IGNORE_COLUMNS": [],
        }

    def test_unnest_display_names(self) -> None:
        spec = b.build_unnest_params(
            ["Sales", "Region"],
            COLS,
            INTERNALS,
            label_column="Metric",
            value_column="Amount",
            name_gen=gen(),
        )
        assert spec == {
            "UNNEST": {
                "COLUMNS": [
                    {"COLUMN": "c1", "LABEL": "Sales"},
                    {"COLUMN": "c2", "LABEL": "Region"},
                ],
                "LABEL": {"COLUMN": "Metric", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
                "VALUE": {"COLUMN": "Amount", "TYPE": "TEXT", "INTERNAL_NAME": "gen2"},
            }
        }

    def test_unnest_internal_name_reverse_lookup(self) -> None:
        # Passing an internal name resolves LABEL back to the display name.
        spec = b.build_unnest_params(["c1"], COLS, INTERNALS, name_gen=gen())
        assert spec["UNNEST"]["COLUMNS"] == [{"COLUMN": "c1", "LABEL": "Sales"}]


# ===============================================================
# Aggregation
# ===============================================================


class TestAggregation:
    def test_pivot_with_delimiter_and_condition(self) -> None:
        aggs = [
            AggregationSpec(column="Sales", function=AggregateFunction.SUM, as_name="Total"),
            AggregationSpec(column="Notes", function=AggregateFunction.CONCAT, delimiter=", "),
        ]
        spec = b.build_pivot_params(
            ["Region"],
            aggs,
            COLS,
            INTERNALS,
            condition=cond(),
            column_types=TYPES,
        )
        assert spec["PIVOT"]["GROUP_BY"] == [{"COLUMN": "c2", "ORDER": 0}]
        assert spec["PIVOT"]["SELECT"] == [
            {"ORDER": 1, "FUNCTION": "SUM", "COLUMN": "c1", "AS": "Total"},
            {
                "ORDER": 2,
                "FUNCTION": "CONCAT",
                "COLUMN": "c4",
                "AS": "CONCAT_Notes",
                "DELIMITER": ", ",
            },
        ]
        assert spec["PIVOT"]["CONDITION"] == built_cond()

    def test_pivot_no_condition_default_as(self) -> None:
        aggs = [AggregationSpec(column="Sales", function=AggregateFunction.AVG)]
        spec = b.build_pivot_params(["Region"], aggs, COLS, INTERNALS)
        assert spec["PIVOT"]["SELECT"][0]["AS"] == "AVG_Sales"
        assert "DELIMITER" not in spec["PIVOT"]["SELECT"][0]
        assert "CONDITION" not in spec["PIVOT"]

    def test_window_column_partition_order_new(self) -> None:
        spec = b.build_window_params(
            WindowFunction.SUM,
            COLS,
            INTERNALS,
            column="Sales",
            new_column="Running",
            partition_by=["Region"],
            order_by=[["Order Date", SortDirection.ASC]],
            range_type=WindowRange.RUNNING,
            name_gen=gen(),
        )
        assert spec["WINDOW"]["EVALUATE"] == {
            "FUNCTION": "SUM",
            "SOURCES": "c1",
            "ARGUMENTS": ["c1"],
        }
        assert spec["WINDOW"]["RANGE"] == "RUNNING"
        assert spec["WINDOW"]["AS"]["COLUMN"] == "Running"
        assert spec["WINDOW"]["GROUP_BY"] == [{"COLUMN": "c2"}]
        assert spec["WINDOW"]["ORDER_BY"] == [["c3", "ASC"]]

    def test_window_no_column_existing(self) -> None:
        spec = b.build_window_params(
            WindowFunction.ROW_NUMBER,
            COLS,
            INTERNALS,
            existing_column="Sales",
        )
        assert "SOURCES" not in spec["WINDOW"]["EVALUATE"]
        assert spec["WINDOW"]["DESTINATION"] == "c1"
        assert spec["WINDOW"]["RANGE"] == "UNBOUNDED"

    def test_window_neither_dest(self) -> None:
        spec = b.build_window_params(WindowFunction.RANK, COLS, INTERNALS)
        assert "AS" not in spec["WINDOW"] and "DESTINATION" not in spec["WINDOW"]
        assert "GROUP_BY" not in spec["WINDOW"] and "ORDER_BY" not in spec["WINDOW"]

    def test_crosstab_with_value_column(self) -> None:
        spec = b.build_crosstab_params(
            ["Region"],
            "Notes",
            CrosstabSpec(function=AggregateFunction.SUM, column="Sales"),
            COLS,
            INTERNALS,
            TYPES,
        )
        assert spec["CROSSTAB"]["ROWS"] == [{"COLUMN": "c2", "TYPE": "TEXT"}]
        assert spec["CROSSTAB"]["COLUMNS"] == [{"COLUMN": "c4", "TYPE": "TEXT"}]
        assert spec["CROSSTAB"]["SELECT"] == {"FUNCTION": "SUM", "COLUMN": "c1"}

    def test_crosstab_count_no_column(self) -> None:
        spec = b.build_crosstab_params(
            ["Region"],
            "Notes",
            CrosstabSpec(function=AggregateFunction.COUNT),
            COLS,
            INTERNALS,
            TYPES,
        )
        assert spec["CROSSTAB"]["SELECT"] == {"FUNCTION": "COUNT"}


# ===============================================================
# Advanced operations
# ===============================================================


class TestAdvanced:
    def test_join_foreign_columns_and_prefix(self) -> None:
        foreign = {"Customer ID": "fc1", "Category": "fc2"}
        spec = b.build_join_params(
            2050,
            JoinType.LEFT,
            on=[JoinKeySpec(left="Region", right="Customer ID")],
            select=["Category", JoinSelectSpec(column="Category", alias="Cat")],
            col_map=COLS,
            internal_names=INTERNALS,
            foreign_columns=foreign,
            column_prefix="L_",
            join_id="testjoin",
        )
        assert spec == {
            "JOIN": {
                "JOIN_ID": "testjoin",
                "DATAVIEW_ID": 2050,
                "TYPE": "LEFT",
                "ON": [{"LEFT": "c2", "RIGHT": "fc1"}],
                "SELECT": [
                    {"COLUMN": "fc2", "ALIAS": "Category"},
                    {"COLUMN": "fc2", "ALIAS": "Cat"},
                ],
                "COLUMN_PREFIX": "L_",
            }
        }

    def test_join_no_foreign_columns_default_alias_uuid(self) -> None:
        spec = b.build_join_params(
            2051,
            JoinType.INNER,
            on=[JoinKeySpec(left="Region", right="column_x")],
            select=["column_y", JoinSelectSpec(column="column_z")],
            col_map=COLS,
            internal_names=INTERNALS,
        )
        join = spec["JOIN"]
        assert join["ON"] == [{"LEFT": "c2", "RIGHT": "column_x"}]
        assert join["SELECT"] == [
            {"COLUMN": "column_y", "ALIAS": "column_y"},
            {"COLUMN": "column_z", "ALIAS": "column_z"},
        ]
        assert isinstance(join["JOIN_ID"], str) and len(join["JOIN_ID"]) == 8
        assert "COLUMN_PREFIX" not in join

    def test_lookup_new(self) -> None:
        spec = b.build_lookup_params(
            "Region",
            2055,
            key="k",
            value="v",
            col_map=COLS,
            internal_names=INTERNALS,
            new_column="Looked Up",
            name_gen=gen(),
        )
        assert spec["LOOKUP"] == {
            "DATAVIEW_ID": 2055,
            "SOURCE": "c2",
            "KEY": "k",
            "VALUE": "v",
            "AS": {"COLUMN": "Looked Up", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
        }

    def test_lookup_existing(self) -> None:
        spec = b.build_lookup_params(
            "Region",
            2055,
            key="k",
            value="v",
            col_map=COLS,
            internal_names=INTERNALS,
            existing_column="Notes",
        )
        assert spec["LOOKUP"]["DESTINATION"] == "c4"

    def test_lookup_neither(self) -> None:
        spec = b.build_lookup_params(
            "Region", 1, key="k", value="v", col_map=COLS, internal_names=INTERNALS
        )
        assert "AS" not in spec["LOOKUP"] and "DESTINATION" not in spec["LOOKUP"]

    def test_json_extract_extractions_object(self) -> None:
        extractions = [
            JsonExtractionSpec(key="name", as_name="Name"),
            JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
        ]
        spec = b.build_json_extract_params(
            "Notes",
            COLS,
            INTERNALS,
            extractions=extractions,
            name_gen=gen(),
        )
        jh = spec["JSON_HANDLE"]
        assert jh["TYPE"] == "JSON_OBJECT"
        assert jh["JSON_OBJECT_OP_TYPE"] == "JSON_OBJECT_TO_COLUMNS"
        assert jh["JSON_EXTRACT"] == [
            {"COLUMN": "Name", "KEY": "name", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
            {"COLUMN": "Age", "KEY": "age", "TYPE": "NUMERIC", "INTERNAL_NAME": "gen2"},
        ]

    def test_json_extract_keys_list_op_override(self) -> None:
        spec = b.build_json_extract_params(
            "Notes",
            COLS,
            INTERNALS,
            json_type=JsonType.LIST,
            keys=["a"],
            keep_source=True,
            op_type=JsonOpType.JSON_LIST_TO_ROWS,
            name_gen=gen(),
        )
        jh = spec["JSON_HANDLE"]
        assert jh["TYPE"] == "JSON_LIST"
        assert jh["JSON_KEEP_SOURCE"] is True
        assert jh["JSON_LIST_OP_TYPE"] == "JSON_LIST_TO_ROWS"
        assert jh["JSON_EXTRACT"] == [
            {"COLUMN": "a", "KEY": "a", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"}
        ]

    def test_json_extract_empty(self) -> None:
        spec = b.build_json_extract_params("Notes", COLS, INTERNALS)
        assert spec["JSON_HANDLE"]["JSON_EXTRACT"] == []

    def test_gen_ai_with_assistant_data_and_derivation(self) -> None:
        spec = b.build_gen_ai_params(
            "classify",
            ["Notes"],
            COLS,
            INTERNALS,
            new_column="Sentiment",
            assistant_data=["hint"],
            context_columns_derivation=True,
            name_gen=gen(),
        )
        assert spec["GEN_AI"] == {
            "AS": {"COLUMN": "Sentiment", "TYPE": "TEXT", "INTERNAL_NAME": "gen1"},
            "ASSISTANT_DATA": ["hint"],
            "query": "classify",
            "context_columns": ["c4"],
            "context_columns_derivation": True,
        }

    def test_gen_ai_defaults(self) -> None:
        spec = b.build_gen_ai_params("do it", ["Notes"], COLS, INTERNALS)
        assert spec["GEN_AI"]["ASSISTANT_DATA"] == []
        assert "context_columns_derivation" not in spec["GEN_AI"]

    def test_sql(self) -> None:
        assert b.build_sql_params("SELECT 1") == {"SQL": {"USER_QUERY": "SELECT 1"}}


# ===============================================================
# Date normalization
# ===============================================================


class TestDateNormalize:
    def test_normalize_with_format(self) -> None:
        assert b.build_date_normalize_params(
            "Order Date",
            COLS,
            INTERNALS,
            formats=["%m/%d/%Y", "%Y-%m-%d"],
        ) == {
            "CONVERT": [{"SOURCE": "c3", "TO_TYPE": "DATE", "FORMAT": {"date_format": "%m/%d/%Y"}}]
        }

    def test_normalize_no_format(self) -> None:
        spec = b.build_date_normalize_params("Order Date", COLS, INTERNALS)
        assert spec == {"CONVERT": [{"SOURCE": "c3", "TO_TYPE": "DATE"}]}

    def test_normalize_rejects_non_date(self) -> None:
        with pytest.raises(ValueError, match="ColumnType.DATE"):
            b.build_date_normalize_params(
                "Order Date", COLS, INTERNALS, target_type=ColumnType.TEXT
            )
