"""Advanced E2E integration tests: complex transformations, new features, multi-step pipelines.

Target: release.mammoth.io (workspace 304 via env vars)
Dataset: Store_Transactions.csv (or employee.csv fallback)

Run:
    pytest tests/integration/test_advanced_transformations.py -v
"""

from __future__ import annotations

import pytest

from mammoth import (
    AggregateFunction,
    AggregationSpec,
    BulkReplaceMapping,
    ColumnType,
    Condition,
    ConversionSpec,
    CopySpec,
    CrosstabSpec,
    DateComponent,
    DateDelta,
    DateDiffUnit,
    FillDirection,
    JoinKeySpec,
    JoinSelectSpec,
    JoinType,
    Operator,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
    WindowFunction,
)

# Fixtures adv_second_dataset_id, adv_second_view are defined in conftest.py


# ═══════════════════════════════════════════════════════════════
#  Advanced Column Operations
# ═══════════════════════════════════════════════════════════════


class TestAdvancedColumnOps:
    """Copy with conditions, combine with condition, convert with FORMAT."""

    def test_copy_with_per_item_condition(self, adv_view):
        """Copy a column with a per-item condition (B3 feature)."""
        result = adv_view.copy_columns(
            [
                CopySpec(
                    source="Department",
                    as_name="dept_copy",
                    type=ColumnType.TEXT,
                    condition=Condition("Transaction Type", Operator.EQ, "sale"),
                ),
            ]
        )
        assert result is not None

    def test_combine_columns(self, adv_view):
        """Combine two columns with separator."""
        result = adv_view.combine_columns(
            sources=["Cashier", "Register"],
            separator=" @ ",
            new_column="cashier_register",
        )
        assert result is not None

    def test_combine_with_condition(self, adv_view):
        """Combine columns with a condition applied."""
        result = adv_view.combine_columns(
            sources=["Cashier", "Department"],
            separator=" - ",
            new_column="cashier_dept",
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None

    def test_convert_type_to_text(self, adv_view):
        """Convert a numeric column to text (a real type change).

        ``Quantity`` holds integer data, so the backend auto-types it NUMERIC on
        upload; converting NUMERIC->NUMERIC is a rejected no-op.  Converting it
        to TEXT is a genuine type change the backend accepts.
        """
        result = adv_view.convert_type(
            [
                ConversionSpec(column="Quantity", to=ColumnType.TEXT),
            ]
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Advanced Filters
# ═══════════════════════════════════════════════════════════════


class TestAdvancedFilter:
    """Compound conditions, NOT, value_is_column, multi-tier set_values."""

    def test_compound_and_or(self, adv_view):
        """Compound: (dept=ORDER AND type=sale) OR category=general."""
        cond = (
            Condition("Department", Operator.EQ, "ORDER")
            & Condition("Transaction Type", Operator.EQ, "sale")
        ) | Condition("Category", Operator.EQ, "general")
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_not_condition(self, adv_view):
        """NOT condition."""
        cond = ~Condition("Transaction Type", Operator.EQ, "return")
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_deeply_nested_condition(self, adv_view):
        """Deeply nested: NOT((A AND B) OR C)."""
        cond = ~(
            (
                Condition("Department", Operator.EQ, "ORDER")
                & Condition("Transaction Type", Operator.EQ, "sale")
            )
            | Condition("Category", Operator.EQ, "service")
        )
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_value_is_column(self, adv_view):
        """Column-to-column comparison (B1 feature)."""
        cond = Condition("Subtotal", Operator.GT, "Price", value_is_column=True)
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_set_values_multi_tier(self, adv_view):
        """Set values with multiple conditional tiers."""
        result = adv_view.set_values(
            new_column="price_tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Premium", condition=Condition("Total", Operator.GTE, 50)),
                SetValue("Standard", condition=Condition("Total", Operator.GTE, 10)),
                SetValue("Budget"),
            ],
        )
        assert result is not None

    def test_set_values_compound_condition(self, adv_view):
        """Set values with compound AND/OR in condition."""
        result = adv_view.set_values(
            new_column="flag",
            column_type=ColumnType.TEXT,
            values=[
                SetValue(
                    "HighValue",
                    condition=(
                        Condition("Total", Operator.GTE, 20)
                        & Condition("Transaction Type", Operator.EQ, "sale")
                    ),
                ),
                SetValue("Other"),
            ],
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Advanced Text Operations
# ═══════════════════════════════════════════════════════════════


class TestAdvancedText:
    """Bulk replace, substring, split, replace."""

    def test_bulk_replace(self, adv_view):
        """Bulk replace with multiple search values."""
        result = adv_view.bulk_replace(
            columns=["Department"],
            mapping=[
                BulkReplaceMapping(search=["ORDER", "service"], replace="Online"),
            ],
        )
        assert result is not None

    def test_substring_left(self, adv_view):
        """Substring from left direction.

        SUBSTRING needs a TEXT source; ``Transaction ID`` is integer data and
        auto-types NUMERIC, so we use the TEXT ``Item Description`` column.
        """
        result = adv_view.substring(
            column="Item Description",
            direction=SubstringDirection.LEFT,
            char_position=6,
            new_column="desc_prefix",
        )
        assert result is not None

    def test_substring_start(self, adv_view):
        """Substring first N chars."""
        result = adv_view.substring(
            column="Cashier",
            direction=SubstringDirection.START,
            num_char=3,
            new_column="cashier_initials",
        )
        assert result is not None

    def test_split_column(self, adv_view):
        """Split column by delimiter."""
        result = adv_view.split_column(
            column="Cashier",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec(name="First", type=ColumnType.TEXT),
                SplitColumnSpec(name="Last", type=ColumnType.TEXT),
            ],
        )
        assert result is not None

    def test_replace_values(self, adv_view):
        """Replace values in a column."""
        result = adv_view.replace_values(
            columns=["Transaction Type"],
            find="sale",
            replace="SALE",
        )
        assert result is not None

    def test_text_transform_upper(self, adv_view):
        """Text transform to upper case."""
        result = adv_view.text_transform(columns=["Department"], case=TextCase.UPPER)
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Advanced Math
# ═══════════════════════════════════════════════════════════════


class TestAdvancedMath:
    """Parenthesized expressions, function calls, conditions."""

    def test_parenthesized_expression(self, adv_view):
        """Math with parenthesized expression: (Price + Tax) * Quantity."""
        result = adv_view.math(
            expression="(Price + Tax) * Quantity",
            new_column="total_calc",
        )
        assert result is not None

    def test_function_call_abs(self, adv_view):
        """Math with ABS function (B6 feature)."""
        result = adv_view.math(
            expression="ABS(Subtotal - Total)",
            new_column="diff_abs",
        )
        assert result is not None

    def test_math_with_literal(self, adv_view):
        """Math with numeric literal."""
        result = adv_view.math(
            expression="Price * 1.1",
            new_column="price_plus_10pct",
        )
        assert result is not None

    def test_math_with_condition(self, adv_view):
        """Math with a condition."""
        result = adv_view.math(
            expression="Subtotal * 0.05",
            new_column="extra_discount",
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Advanced Date Operations
# ═══════════════════════════════════════════════════════════════


class TestAdvancedDate:
    """Extract, increment, date diff on date columns.

    ``Time`` is a timestamp, so the backend auto-types it DATE on upload; a
    ``convert Time->DATE`` would be a rejected no-op, so we operate on it
    directly.
    """

    def test_extract_year_and_month(self, adv_view):
        """Extract year then month from date column."""
        r1 = adv_view.extract_date(
            column="Time",
            component=DateComponent.YEAR,
            new_column="txn_year",
        )
        assert r1 is not None
        r2 = adv_view.extract_date(
            column="Time",
            component=DateComponent.MONTH,
            new_column="txn_month",
        )
        assert r2 is not None

    def test_extract_weekday(self, adv_view):
        """Extract weekday_text from date column."""
        result = adv_view.extract_date(
            column="Time",
            component=DateComponent.WEEKDAY_TEXT,
            new_column="txn_weekday",
        )
        assert result is not None

    def test_increment_date(self, adv_view):
        """Increment date by multi-component delta."""
        result = adv_view.increment_date(
            column="Time",
            delta=DateDelta(months=1, days=15),
            new_column="time_shifted",
        )
        assert result is not None

    def test_date_diff(self, adv_view):
        """Date diff on same column (zero diff, tests API acceptance)."""
        result = adv_view.date_diff(
            component=DateDiffUnit.DAY,
            start="Time",
            end="Time",
            new_column="zero_diff",
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Advanced Aggregation
# ═══════════════════════════════════════════════════════════════


class TestAdvancedAggregation:
    """Pivot, window, crosstab with advanced options."""

    def test_pivot_multi_group_multi_agg(self, adv_view):
        """Pivot with 2 group_by columns and 2 aggregations."""
        result = adv_view.pivot(
            group_by=["Department", "Transaction Type"],
            aggregations=[
                AggregationSpec(
                    column="Total", function=AggregateFunction.SUM, as_name="total_sum"
                ),
                AggregationSpec(
                    column="Quantity", function=AggregateFunction.AVG, as_name="avg_qty"
                ),
            ],
        )
        assert result is not None

    def test_pivot_with_condition(self, adv_view):
        """Pivot with a filter condition."""
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total", function=AggregateFunction.SUM, as_name="sale_total"
                ),
            ],
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None

    def test_pivot_concat_with_delimiter(self, adv_view):
        """Pivot with CONCAT aggregation and delimiter (B7 feature)."""
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Cashier",
                    function=AggregateFunction.CONCAT,
                    as_name="all_cashiers",
                    delimiter=", ",
                ),
            ],
        )
        assert result is not None

    def test_window_row_number(self, adv_view):
        """Window ROW_NUMBER partitioned and ordered."""
        result = adv_view.window(
            function=WindowFunction.ROW_NUMBER,
            new_column="row_num",
            partition_by=["Department"],
            order_by=[["Total", SortDirection.DESC]],
        )
        assert result is not None

    def test_window_sum_running(self, adv_view):
        """Window SUM with partition and order."""
        result = adv_view.window(
            function=WindowFunction.SUM,
            column="Total",
            new_column="running_total",
            partition_by=["Department"],
            order_by=[["Transaction ID", SortDirection.ASC]],
        )
        assert result is not None

    @pytest.mark.xfail(reason="CROSSTAB uses exports endpoint, not pipeline tasks — SDK fix needed")
    def test_crosstab_count(self, adv_view):
        """Crosstab with COUNT (no column needed)."""
        result = adv_view.crosstab(
            rows=["Department"],
            pivot_column="Transaction Type",
            select=CrosstabSpec(function=AggregateFunction.COUNT),
        )
        assert result is not None

    @pytest.mark.xfail(reason="CROSSTAB uses exports endpoint, not pipeline tasks — SDK fix needed")
    def test_crosstab_sum(self, adv_view):
        """Crosstab with SUM on a numeric column (Bug 1 fix verification)."""
        result = adv_view.crosstab(
            rows=["Department"],
            pivot_column="Transaction Type",
            select=CrosstabSpec(function=AggregateFunction.SUM, column="Total"),
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Row Operations
# ═══════════════════════════════════════════════════════════════


class TestAdvancedRowOps:
    """Fill, limit, discard, unnest."""

    def test_fill_missing(self, adv_view):
        """Fill missing with last value."""
        result = adv_view.fill_missing(
            column="Discount",
            direction=FillDirection.LAST_VALUE,
        )
        assert result is not None

    def test_limit_rows_top(self, adv_view):
        """Limit to top N rows with ordering."""
        result = adv_view.limit_rows(
            n=10,
            order_by=[["Total", SortDirection.DESC]],
        )
        assert result is not None

    def test_limit_rows_bottom(self, adv_view):
        """Limit bottom N rows."""
        result = adv_view.limit_rows(n=5, bottom=True)
        assert result is not None

    def test_discard_duplicates(self, adv_view):
        """Discard duplicates ignoring some columns."""
        result = adv_view.discard_duplicates(
            ignore_columns=["Transaction ID"],
        )
        assert result is not None

    def test_unnest_basic(self, adv_view):
        """Unnest text columns into label/value format."""
        result = adv_view.unnest(
            columns=["Cashier", "Department"],
            label_column="Metric",
            value_column="Amount",
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  JOIN Tests
# ═══════════════════════════════════════════════════════════════


class TestJoin:
    """Join two datasets in the same workspace."""

    def test_join_inner_with_view_object(self, adv_view, adv_second_view):
        """INNER join using View object (display name resolution)."""
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.INNER,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=["department"],
        )
        assert result is not None

    def test_join_left_with_view_object(self, adv_view, adv_second_view):
        """LEFT join — all rows from source preserved."""
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=[JoinSelectSpec(column="base_salary", alias="cashier_salary")],
        )
        assert result is not None

    def test_join_with_column_prefix(self, adv_view, adv_second_view):
        """JOIN with column prefix to avoid name collisions."""
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=["department", "designation"],
            column_prefix="emp_",
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Multi-Step Pipeline
# ═══════════════════════════════════════════════════════════════


class TestMultiStepPipeline:
    """Chain multiple transformations and verify pipeline state."""

    def test_five_step_chain(self, adv_view):
        """Chain: convert_type -> filter -> math -> set_values -> limit."""
        # Transaction ID auto-types NUMERIC; -> TEXT is a real change (Quantity is
        # already NUMERIC, so converting it would be a no-op ref_error).
        r1 = adv_view.convert_type([ConversionSpec(column="Transaction ID", to=ColumnType.TEXT)])
        assert r1 is not None

        r2 = adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        assert r2 is not None

        r3 = adv_view.math(
            expression="Price * Quantity",
            new_column="line_total",
        )
        assert r3 is not None

        r4 = adv_view.set_values(
            new_column="size",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Large", condition=Condition("Quantity", Operator.GTE, 10)),
                SetValue("Small"),
            ],
        )
        assert r4 is not None

        r5 = adv_view.limit_rows(n=50)
        assert r5 is not None

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 5

    def test_text_pipeline(self, adv_view):
        """Chain: combine -> replace -> split (all using original columns).

        Note: Pipeline tasks are added but not executed until data is fetched,
        so we cannot reference columns created by previous pipeline steps.
        """
        r1 = adv_view.combine_columns(
            sources=["Cashier", "Department"],
            separator="|",
            new_column="combined",
        )
        assert r1 is not None

        r2 = adv_view.replace_values(
            columns=["Transaction Type"],
            find="sale",
            replace="SALE",
        )
        assert r2 is not None

        r3 = adv_view.split_column(
            column="Cashier",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec(name="first_name", type=ColumnType.TEXT),
                SplitColumnSpec(name="last_name", type=ColumnType.TEXT),
            ],
        )
        assert r3 is not None

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 3

    def test_date_pipeline(self, adv_view):
        """Chain: extract year -> extract month -> increment (Time is already DATE)."""
        r1 = adv_view.extract_date(
            column="Time",
            component=DateComponent.YEAR,
            new_column="year",
        )
        assert r1 is not None

        r2 = adv_view.extract_date(
            column="Time",
            component=DateComponent.MONTH_TEXT,
            new_column="month_name",
        )
        assert r2 is not None

        r3 = adv_view.increment_date(
            column="Time",
            delta=DateDelta(days=7),
            new_column="next_week",
        )
        assert r3 is not None

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 3


# ═══════════════════════════════════════════════════════════════
#  Export after Transformations
# ═══════════════════════════════════════════════════════════════


class TestAdvancedExport:
    """Export after transformations."""

    def test_export_after_transform(self, adv_view, tmp_path):
        """Apply a transformation then export to CSV."""
        adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        out = tmp_path / "adv_export.csv"
        path = adv_view.export.to_csv(output_path=str(out))
        assert path.exists()
        content = path.read_text()
        assert len(content.splitlines()) > 1
