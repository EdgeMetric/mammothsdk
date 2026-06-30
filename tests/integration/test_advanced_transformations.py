"""Advanced E2E integration tests: complex transformations, new features, multi-step pipelines.

Target: release.mammoth.io (workspace 304 via env vars)
Dataset: Store_Transactions.csv (or employee.csv fallback)

Run:
    pytest tests/integration/test_advanced_transformations.py -v
"""

from __future__ import annotations

import contextlib

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
    MammothClient,
    Operator,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
    View,
    WindowFunction,
)

# Fixtures adv_second_dataset_id, adv_second_view are defined in conftest.py

# ── Read-back helpers (verify the EFFECT of dataset-producing exports) ──
#
# branch_out / crosstab return the new dataset's id (int). To prove the export
# actually did what was asked — not merely "it ran" — we open a view on that
# dataset and assert on its real contents. The live data() shape is
# ``{"data": [rows], "paging": {...}}`` where ``paging.total`` is unreliable
# (observed 0), rows are keyed by INTERNAL name (``column_1``…) plus a ``hash``
# field, and values are strings. So: count via the paginated ``data`` list,
# read cell values positionally while skipping ``hash``, and coerce strings.

_PAGE = 10_000
_HASH_KEY = "hash"


def _open_new_dataset(client: MammothClient, dataset_id: int) -> View:
    """Open the default view of a freshly-materialised dataset."""
    return client.views.list(dataset_id)[0]


def _data_rows(view: View, columns: list[str] | None = None, condition=None):
    """Yield every (optionally filtered) row of a view, paginating fully.

    A single large ``limit`` is unreliable, so page by ``offset`` until a short
    page arrives — this reads the dataset in full regardless of any cap.
    """
    offset = 1
    while True:
        page = view.data(columns=columns, condition=condition, limit=_PAGE, offset=offset)["data"]
        yield from page
        if len(page) < _PAGE:
            return
        offset += _PAGE


def _cells(row: dict[str, object]) -> list[object]:
    """The row's real cell values (excluding the internal ``hash`` field)."""
    return [v for k, v in row.items() if k != _HASH_KEY]


def _count_rows(view: View, condition=None) -> int:
    """Exact row count via full pagination (``paging.total`` is unreliable)."""
    return sum(1 for _ in _data_rows(view, condition=condition))


def _distinct_count(view: View, column: str) -> int:
    """Number of distinct values in one column of a view."""
    return len({_cells(r)[0] for r in _data_rows(view, [column])})


def _to_number(value: object) -> float | None:
    """Coerce a cell to float, or None if it isn't numeric (e.g. a text label)."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _sum_numeric_cells(view: View) -> float:
    """Sum every numeric cell across a view (text labels and hash are skipped)."""
    return sum(
        n for row in _data_rows(view) for v in _cells(row) if (n := _to_number(v)) is not None
    )


def _sum_column(view: View, column: str) -> float:
    """Sum one numeric column over all rows of a view."""
    return sum(n for r in _data_rows(view, [column]) if (n := _to_number(_cells(r)[0])) is not None)


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

    def test_crosstab_count(self, adv_view, adv_client):
        """Crosstab COUNT → a dataset grouped by Department, pivoted on type.

        Verifies the EFFECT, not just job success: the row-grouping column
        survives, the pivot adds value columns, and aggregation collapses the
        output to exactly one row per distinct Department.
        """
        n_depts = _distinct_count(adv_view, "Department")
        n_types = _distinct_count(adv_view, "Transaction Type")
        source_rows = _count_rows(adv_view)
        new_ds_id = adv_view.crosstab(
            rows=["Department"],
            pivot_column="Transaction Type",
            select=CrosstabSpec(function=AggregateFunction.COUNT),
            dataset_name="xtab_count_by_dept",
        )
        assert isinstance(new_ds_id, int)
        try:
            xtab = _open_new_dataset(adv_client, new_ds_id)
            names = xtab.display_names
            assert "Department" in names, "row-grouping column must survive"
            # One label column (Department) + one value column per pivot value.
            assert len(names) >= 1 + n_types
            # Aggregation collapses to one row per distinct row-group value.
            assert _count_rows(xtab) == n_depts
            # The grand total of all COUNT cells equals the source row count.
            assert _sum_numeric_cells(xtab) == source_rows
        finally:
            with contextlib.suppress(Exception):
                adv_client.datasets.delete(new_ds_id)

    def test_crosstab_sum(self, adv_view, adv_client):
        """Crosstab SUM of Total, grouped by Department, pivoted on type.

        Verifies the SUM math end-to-end: SUM is partition-invariant, so the
        grand total of every value cell in the crosstab must equal the SUM of
        ``Total`` over the whole source dataset.
        """
        n_depts = _distinct_count(adv_view, "Department")
        source_total_sum = _sum_column(adv_view, "Total")
        new_ds_id = adv_view.crosstab(
            rows=["Department"],
            pivot_column="Transaction Type",
            select=CrosstabSpec(function=AggregateFunction.SUM, column="Total"),
            dataset_name="xtab_sum_total_by_dept",
        )
        assert isinstance(new_ds_id, int)
        try:
            xtab = _open_new_dataset(adv_client, new_ds_id)
            assert "Department" in xtab.display_names
            assert _count_rows(xtab) == n_depts
            # Grand total of the pivoted SUM cells == source SUM(Total).
            assert _sum_numeric_cells(xtab) == pytest.approx(source_total_sum, rel=1e-6)
        finally:
            with contextlib.suppress(Exception):
                adv_client.datasets.delete(new_ds_id)


class TestBranchOut:
    """Branch out — save the view as a new internal dataset (internal export)."""

    def test_branch_out_new_dataset(self, adv_view, adv_client):
        """Branch out the full view into a brand-new dataset.

        Verifies the EFFECT: the new dataset is a faithful copy — same row
        count and the exact same set of columns as the source.
        """
        full_total = _count_rows(adv_view)
        source_columns = set(adv_view.display_names)
        new_ds_id = adv_view.branch_out(dataset_name="branchout_e2e_full")
        assert isinstance(new_ds_id, int)
        try:
            copy = _open_new_dataset(adv_client, new_ds_id)
            assert _count_rows(copy) == full_total, "full copy must preserve every row"
            assert set(copy.display_names) == source_columns, "all columns must carry over"
        finally:
            with contextlib.suppress(Exception):
                adv_client.datasets.delete(new_ds_id)

    def test_branch_out_with_condition(self, adv_view, adv_client):
        """Branch out only rows matching a condition into a new dataset.

        Verifies the filter was truly applied: the new dataset has exactly the
        rows the same condition selects in the source, strictly fewer rows than
        the full source, and ZERO rows that violate the condition.
        """
        sale = Condition("Transaction Type", Operator.EQ, "sale")
        full_total = _count_rows(adv_view)
        sales_total = _count_rows(adv_view, condition=sale)
        assert 0 < sales_total < full_total, "fixture must have both sale and non-sale rows"

        new_ds_id = adv_view.branch_out(dataset_name="branchout_e2e_sales_only", condition=sale)
        assert isinstance(new_ds_id, int)
        try:
            filtered = _open_new_dataset(adv_client, new_ds_id)
            # Kept exactly the matching rows — no more, no fewer.
            assert _count_rows(filtered) == sales_total
            # And not one row that breaks the condition leaked through.
            assert _count_rows(filtered, condition=~sale) == 0, "filter must exclude non-matches"
        finally:
            with contextlib.suppress(Exception):
                adv_client.datasets.delete(new_ds_id)


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
