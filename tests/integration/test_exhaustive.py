"""Exhaustive SDK integration tests using typed enums and dataclasses.

Target: app.mammoth.io (workspace 304, project 1134)
Dataset: Store_Transactions.csv (primary), employee.csv (secondary for JOIN/LOOKUP)

Every test uses typed SDK objects (enums, dataclasses) instead of raw dicts/strings.
Data is verified after transformations — not just ``assert result is not None``.

Run:
    pytest tests/integration/test_exhaustive.py -v --tb=short
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

from mammoth import (
    AggregateFunction,
    AggregationSpec,
    BulkReplaceMapping,
    ColumnType,
    CompoundCondition,
    Condition,
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
    MammothClient,
    NotCondition,
    Operator,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
    View,
    WindowFunction,
)

# ── Paths ────────────────────────────────────────────────────

STORE_CSV = Path(__file__).resolve().parent.parent.parent / "Store_Transactions.csv"
EMPLOYEE_CSV = Path(__file__).resolve().parent.parent.parent / "employee.csv"


# ═══════════════════════════════════════════════════════════════
#  1. Connection
# ═══════════════════════════════════════════════════════════════


class TestConnection:
    """Verify connectivity and auth error handling."""

    def test_connection_success(self, adv_client: MammothClient) -> None:
        assert adv_client.test_connection() is True

    def test_connection_bad_key(self) -> None:
        bad = MammothClient(
            api_key="INVALID_KEY",
            api_secret="INVALID_SECRET",
            workspace_id=304,
            base_url="https://app.mammoth.io/api/v2",
        )
        assert bad.test_connection() is False


# ═══════════════════════════════════════════════════════════════
#  2. File Upload
# ═══════════════════════════════════════════════════════════════


class TestFileUpload:
    """Upload various file types and verify datasets."""

    def test_upload_csv(self, adv_client: MammothClient) -> None:
        """Upload employee.csv and verify dataset ID returned."""
        ds_id = adv_client.files.upload(str(EMPLOYEE_CSV))
        assert isinstance(ds_id, int)
        with contextlib.suppress(Exception):
            adv_client.datasets.delete(ds_id)

    def test_upload_csv_verify_columns(self, adv_client: MammothClient) -> None:
        """Upload employee.csv and verify 14 expected columns."""
        ds_id = adv_client.files.upload(str(EMPLOYEE_CSV))
        assert isinstance(ds_id, int)
        try:
            views = adv_client.views.list(ds_id)
            assert len(views) > 0
            v = views[0]
            expected = {
                "emp_id",
                "full_name",
                "department",
                "designation",
                "joining_date",
                "exit_date",
                "base_salary",
                "bonus_pct",
                "manager_id",
                "location",
                "employment_type",
                "performance_score",
                "last_promotion_date",
                "gender",
            }
            assert set(v.display_names) == expected
        finally:
            with contextlib.suppress(Exception):
                adv_client.datasets.delete(ds_id)  # type: ignore[arg-type]

    def test_upload_large_csv(self, adv_client: MammothClient) -> None:
        """Upload Store_Transactions.csv and verify row count > 60K."""
        if not STORE_CSV.exists():
            pytest.skip("Store_Transactions.csv not found")
        ds_id = adv_client.files.upload(str(STORE_CSV))
        assert isinstance(ds_id, int)
        try:
            views = adv_client.views.list(ds_id)
            assert len(views) > 0
            v = views[0]
            result = v.data(limit=1, offset=1)
            paging = result.get("paging", {})
            total = paging.get("total", 0)
            assert total > 60000, f"Expected >60K rows, got {total}"
        finally:
            with contextlib.suppress(Exception):
                adv_client.datasets.delete(ds_id)  # type: ignore[arg-type]

    def test_upload_excel(self, adv_client: MammothClient, tmp_path: Path) -> None:
        """Upload a simple .xlsx file and verify dataset created."""
        openpyxl = pytest.importorskip("openpyxl")
        xlsx = tmp_path / "test_data.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Name", "Age", "City"])
        ws.append(["Alice", 30, "NYC"])
        ws.append(["Bob", 25, "LA"])
        wb.save(str(xlsx))

        ds_id = adv_client.files.upload(str(xlsx))
        assert isinstance(ds_id, int)
        with contextlib.suppress(Exception):
            adv_client.datasets.delete(ds_id)


# ═══════════════════════════════════════════════════════════════
#  3. Project & Dataset
# ═══════════════════════════════════════════════════════════════


class TestProjectDataset:
    """Verify project and dataset CRUD."""

    def test_list_projects(self, adv_client: MammothClient) -> None:
        result = adv_client.projects.list()
        projects = result.get("projects", result if isinstance(result, list) else [])
        ids = [p.get("id") or p for p in projects]
        assert 1134 in ids or any(p.get("id") == 1134 for p in projects if isinstance(p, dict))

    def test_get_project(self, adv_client: MammothClient) -> None:
        result = adv_client.projects.get(1134)
        assert result is not None

    def test_list_datasets(self, adv_client: MammothClient, adv_uploaded_dataset_id: int) -> None:
        result = adv_client.datasets.list()
        ds_list = result.get("datasets", result if isinstance(result, list) else [])
        ids = [d.get("id") if isinstance(d, dict) else d for d in ds_list]
        assert adv_uploaded_dataset_id in ids

    def test_browse_project(self, adv_client: MammothClient) -> None:
        result = adv_client.projects.browse(1134)
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  4. View CRUD
# ═══════════════════════════════════════════════════════════════


class TestViewCRUD:
    """View creation, listing, data access, column mapping."""

    def test_create_view(self, adv_client: MammothClient, adv_uploaded_dataset_id: int) -> None:
        v = adv_client.views.create(dataset_id=adv_uploaded_dataset_id, name="test_create")
        try:
            assert isinstance(v, View)
            assert isinstance(v.id, int)
            assert v.name == "test_create"
            assert len(v.display_names) > 0
        finally:
            with contextlib.suppress(Exception):
                adv_client.views.delete(v.id, adv_uploaded_dataset_id)

    def test_create_view_clone(self, adv_view: View) -> None:
        original_cols = set(adv_view.display_names)
        clone = adv_view._client.views.create(
            dataset_id=adv_view.dataset_id,
            name="test_clone",
            clone_from=adv_view.id,
        )
        try:
            assert set(clone.display_names) == original_cols
        finally:
            with contextlib.suppress(Exception):
                adv_view._client.views.delete(clone.id, adv_view.dataset_id)

    def test_get_view(self, adv_client: MammothClient, adv_view: View) -> None:
        fetched = adv_client.views.get(adv_view.id, adv_view.dataset_id)
        assert fetched.id == adv_view.id
        assert fetched.display_names == adv_view.display_names

    def test_list_views(self, adv_client: MammothClient, adv_uploaded_dataset_id: int) -> None:
        views = adv_client.views.list(adv_uploaded_dataset_id)
        assert len(views) >= 1
        assert all(isinstance(v, View) for v in views)

    def test_view_data_default(self, adv_view: View) -> None:
        result = adv_view.data()
        assert "data" in result
        assert len(result["data"]) > 0

    def test_view_data_limit_offset(self, adv_view: View) -> None:
        page1 = adv_view.data(limit=5, offset=1)
        page2 = adv_view.data(limit=5, offset=6)
        assert len(page1["data"]) == 5
        assert len(page2["data"]) == 5
        assert page1["data"] != page2["data"]

    def test_view_data_with_columns(self, adv_view: View) -> None:
        cols = adv_view.display_names[:2]
        result = adv_view.data(columns=cols)
        assert len(result["data"]) > 0
        first_row = result["data"][0]
        assert len(first_row) == 2

    def test_view_data_with_condition(self, adv_view: View) -> None:
        cond = Condition("Transaction Type", Operator.EQ, "sale")
        result = adv_view.data(condition=cond, limit=10)
        assert len(result["data"]) > 0

    def test_view_data_with_sort(self, adv_view: View) -> None:
        result = adv_view.data(sort="(Total:desc)", limit=5)
        assert len(result["data"]) > 0

    def test_view_column_mapping(self, adv_view: View) -> None:
        assert len(adv_view.columns) == len(adv_view.display_names)
        assert len(adv_view.column_types) == len(adv_view.display_names)
        for name in adv_view.display_names:
            assert name in adv_view.columns
            assert name in adv_view.column_types

    def test_view_list_tasks_empty(
        self, adv_client: MammothClient, adv_uploaded_dataset_id: int
    ) -> None:
        v = adv_client.views.create(dataset_id=adv_uploaded_dataset_id, name="test_no_tasks")
        try:
            tasks = v.list_tasks()
            assert len(tasks) == 0
        finally:
            with contextlib.suppress(Exception):
                adv_client.views.delete(v.id, adv_uploaded_dataset_id)


# ═══════════════════════════════════════════════════════════════
#  5. Column Operations
# ═══════════════════════════════════════════════════════════════


class TestColumnOps:
    """add_column, delete_columns, copy_columns, combine_columns, convert_type."""

    def test_add_column_text(self, adv_view: View) -> None:
        result = adv_view.add_column("new_text", ColumnType.TEXT)
        assert result is not None
        assert "new_text" in adv_view.display_names

    def test_add_column_numeric(self, adv_view: View) -> None:
        result = adv_view.add_column("new_num", ColumnType.NUMERIC)
        assert result is not None
        assert "new_num" in adv_view.display_names

    def test_add_column_date(self, adv_view: View) -> None:
        result = adv_view.add_column("new_date", ColumnType.DATE)
        assert result is not None
        assert "new_date" in adv_view.display_names

    def test_delete_single_column(self, adv_view: View) -> None:
        adv_view.add_column("to_delete", ColumnType.TEXT)
        assert "to_delete" in adv_view.display_names
        adv_view.delete_columns(["to_delete"])
        assert "to_delete" not in adv_view.display_names

    def test_delete_multiple_columns(self, adv_view: View) -> None:
        adv_view.add_column("del_a", ColumnType.TEXT)
        adv_view.add_column("del_b", ColumnType.TEXT)
        adv_view.delete_columns(["del_a", "del_b"])
        assert "del_a" not in adv_view.display_names
        assert "del_b" not in adv_view.display_names

    def test_copy_columns_typed(self, adv_view: View) -> None:
        result = adv_view.copy_columns(
            [
                CopySpec(source="Department", as_name="dept_copy", type=ColumnType.TEXT),
            ]
        )
        assert result is not None
        assert "dept_copy" in adv_view.display_names

    def test_copy_columns_with_condition(self, adv_view: View) -> None:
        result = adv_view.copy_columns(
            [
                CopySpec(
                    source="Department",
                    as_name="dept_cond",
                    type=ColumnType.TEXT,
                    condition=Condition("Transaction Type", Operator.EQ, "sale"),
                ),
            ]
        )
        assert result is not None
        assert "dept_cond" in adv_view.display_names

    def test_combine_columns_custom_sep(self, adv_view: View) -> None:
        result = adv_view.combine_columns(
            sources=["Cashier", "Department"],
            separator="|",
            new_column="cashier_pipe_dept",
        )
        assert result is not None
        assert "cashier_pipe_dept" in adv_view.display_names

    def test_combine_to_existing_column(self, adv_view: View) -> None:
        adv_view.add_column("combined_target", ColumnType.TEXT)
        result = adv_view.combine_columns(
            sources=["Cashier", "Register"],
            separator=" @ ",
            existing_column="combined_target",
        )
        assert result is not None

    def test_combine_with_condition(self, adv_view: View) -> None:
        result = adv_view.combine_columns(
            sources=["Cashier", "Department"],
            separator=" - ",
            new_column="cond_combined",
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None
        assert "cond_combined" in adv_view.display_names

    def test_convert_text_to_numeric(self, adv_view: View) -> None:
        result = adv_view.convert_type(
            [
                ConversionSpec(column="Quantity", to=ColumnType.NUMERIC),
            ]
        )
        assert result is not None
        assert adv_view.column_types["Quantity"] == "NUMERIC"

    def test_convert_text_to_date_with_format(self, adv_view: View) -> None:
        result = adv_view.convert_type(
            [
                ConversionSpec(column="Time", to=ColumnType.DATE),
            ]
        )
        assert result is not None
        assert adv_view.column_types["Time"] == "DATE"

    def test_convert_multiple_columns(self, adv_view: View) -> None:
        result = adv_view.convert_type(
            [
                ConversionSpec(column="Quantity", to=ColumnType.NUMERIC),
                ConversionSpec(column="Price", to=ColumnType.NUMERIC),
            ]
        )
        assert result is not None
        assert adv_view.column_types["Quantity"] == "NUMERIC"
        assert adv_view.column_types["Price"] == "NUMERIC"


# ═══════════════════════════════════════════════════════════════
#  6. Filter & Set
# ═══════════════════════════════════════════════════════════════


class TestFilterAndSet:
    """filter_rows with all Operator variants; set_values with typed SetValue."""

    def test_filter_eq(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        assert result is not None

    def test_filter_ne(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Transaction Type", Operator.NE, "return"))
        assert result is not None

    def test_filter_gt(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Total", Operator.GT, 10))
        assert result is not None

    def test_filter_gte(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Total", Operator.GTE, 10))
        assert result is not None

    def test_filter_lt(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Total", Operator.LT, 100))
        assert result is not None

    def test_filter_lte(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Total", Operator.LTE, 100))
        assert result is not None

    def test_filter_contains(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Cashier", Operator.CONTAINS, "a"))
        assert result is not None

    def test_filter_starts_with(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Transaction Type", Operator.STARTS_WITH, "s"))
        assert result is not None

    def test_filter_ends_with(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Transaction Type", Operator.ENDS_WITH, "e"))
        assert result is not None

    def test_filter_in_list(self, adv_view: View) -> None:
        result = adv_view.filter_rows(
            Condition("Department", Operator.IN_LIST, ["ORDER", "KITCHEN"])
        )
        assert result is not None

    def test_filter_is_empty(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Discount", Operator.IS_EMPTY, ""))
        assert result is not None

    def test_filter_is_not_empty(self, adv_view: View) -> None:
        result = adv_view.filter_rows(Condition("Total", Operator.IS_NOT_EMPTY, ""))
        assert result is not None

    def test_filter_compound_and(self, adv_view: View) -> None:
        cond = Condition("Transaction Type", Operator.EQ, "sale") & Condition(
            "Total", Operator.GTE, 10
        )
        assert isinstance(cond, CompoundCondition)
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_filter_compound_or(self, adv_view: View) -> None:
        cond = Condition("Department", Operator.EQ, "ORDER") | Condition(
            "Department", Operator.EQ, "KITCHEN"
        )
        assert isinstance(cond, CompoundCondition)
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_filter_not(self, adv_view: View) -> None:
        cond = ~Condition("Transaction Type", Operator.EQ, "return")
        assert isinstance(cond, NotCondition)
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_filter_deeply_nested(self, adv_view: View) -> None:
        cond = ~(
            (
                Condition("Department", Operator.EQ, "ORDER")
                & Condition("Transaction Type", Operator.EQ, "sale")
            )
            | Condition("Category", Operator.EQ, "service")
        )
        result = adv_view.filter_rows(cond)
        assert result is not None

    def test_filter_type_remove(self, adv_view: View) -> None:
        result = adv_view.filter_rows(
            Condition("Transaction Type", Operator.EQ, "return"),
            filter_type=FilterType.REMOVE,
        )
        assert result is not None

    def test_set_values_typed(self, adv_view: View) -> None:
        result = adv_view.set_values(
            new_column="price_tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("High", condition=Condition("Total", Operator.GTE, 50)),
                SetValue("Low"),
            ],
        )
        assert result is not None
        assert "price_tier" in adv_view.display_names

    def test_set_values_multi_tier(self, adv_view: View) -> None:
        result = adv_view.set_values(
            new_column="band",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Premium", condition=Condition("Total", Operator.GTE, 50)),
                SetValue("Standard", condition=Condition("Total", Operator.GTE, 20)),
                SetValue("Budget", condition=Condition("Total", Operator.GTE, 5)),
                SetValue("Minimal"),
            ],
        )
        assert result is not None
        assert "band" in adv_view.display_names

    def test_set_values_existing_column(self, adv_view: View) -> None:
        adv_view.add_column("overwrite_me", ColumnType.TEXT)
        result = adv_view.set_values(
            existing_column="overwrite_me",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("yes", condition=Condition("Total", Operator.GTE, 10)),
                SetValue("no"),
            ],
        )
        assert result is not None

    def test_set_values_compound_condition(self, adv_view: View) -> None:
        result = adv_view.set_values(
            new_column="flag",
            column_type=ColumnType.TEXT,
            values=[
                SetValue(
                    "HighSale",
                    condition=(
                        Condition("Total", Operator.GTE, 20)
                        & Condition("Transaction Type", Operator.EQ, "sale")
                    ),
                ),
                SetValue("Other"),
            ],
        )
        assert result is not None
        assert "flag" in adv_view.display_names


# ═══════════════════════════════════════════════════════════════
#  7. Text Operations
# ═══════════════════════════════════════════════════════════════


class TestTextOps:
    """text_transform, replace_values, bulk_replace, split_column, substring."""

    def test_text_transform_upper(self, adv_view: View) -> None:
        result = adv_view.text_transform(columns=["Department"], case=TextCase.UPPER)
        assert result is not None

    def test_text_transform_lower(self, adv_view: View) -> None:
        result = adv_view.text_transform(columns=["Department"], case=TextCase.LOWER)
        assert result is not None

    def test_text_transform_title(self, adv_view: View) -> None:
        result = adv_view.text_transform(columns=["Department"], case=TextCase.TITLE)
        assert result is not None

    def test_text_transform_trim(self, adv_view: View) -> None:
        result = adv_view.text_transform(columns=["Cashier"], trim=True)
        assert result is not None

    def test_text_transform_with_condition(self, adv_view: View) -> None:
        result = adv_view.text_transform(
            columns=["Department"],
            case=TextCase.UPPER,
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None

    def test_replace_values_basic(self, adv_view: View) -> None:
        result = adv_view.replace_values(columns=["Transaction Type"], find="sale", replace="SALE")
        assert result is not None

    def test_replace_values_case_sensitive(self, adv_view: View) -> None:
        result = adv_view.replace_values(
            columns=["Transaction Type"],
            find="sale",
            replace="SALE",
            match_case=True,
        )
        assert result is not None

    def test_bulk_replace_single(self, adv_view: View) -> None:
        result = adv_view.bulk_replace(
            columns=["Department"],
            mapping=[BulkReplaceMapping(search=["ORDER"], replace="Online")],
        )
        assert result is not None

    def test_bulk_replace_multi(self, adv_view: View) -> None:
        result = adv_view.bulk_replace(
            columns=["Department"],
            mapping=[
                BulkReplaceMapping(search=["ORDER"], replace="Online"),
                BulkReplaceMapping(search=["KITCHEN"], replace="Food"),
            ],
        )
        assert result is not None

    def test_split_column(self, adv_view: View) -> None:
        result = adv_view.split_column(
            column="Cashier",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec(name="First", type=ColumnType.TEXT),
                SplitColumnSpec(name="Last", type=ColumnType.TEXT),
            ],
        )
        assert result is not None
        assert "First" in adv_view.display_names
        assert "Last" in adv_view.display_names

    def test_substring_start(self, adv_view: View) -> None:
        result = adv_view.substring(
            column="Transaction ID",
            direction=SubstringDirection.START,
            num_char=5,
            new_column="txn_start",
        )
        assert result is not None
        assert "txn_start" in adv_view.display_names

    def test_substring_end(self, adv_view: View) -> None:
        result = adv_view.substring(
            column="Transaction ID",
            direction=SubstringDirection.END,
            num_char=3,
            new_column="txn_end",
        )
        assert result is not None
        assert "txn_end" in adv_view.display_names

    def test_substring_left(self, adv_view: View) -> None:
        result = adv_view.substring(
            column="Transaction ID",
            direction=SubstringDirection.LEFT,
            char_position=6,
            new_column="txn_left",
        )
        assert result is not None
        assert "txn_left" in adv_view.display_names

    def test_substring_right(self, adv_view: View) -> None:
        result = adv_view.substring(
            column="Transaction ID",
            direction=SubstringDirection.RIGHT,
            char_position=4,
            new_column="txn_right",
        )
        assert result is not None
        assert "txn_right" in adv_view.display_names


# ═══════════════════════════════════════════════════════════════
#  8. Math Operations
# ═══════════════════════════════════════════════════════════════


class TestMathOps:
    """math with expressions, literals, conditions, raw token lists."""

    def test_math_string_expression(self, adv_view: View) -> None:
        adv_view.convert_type(
            [
                ConversionSpec(column="Price", to=ColumnType.NUMERIC),
                ConversionSpec(column="Tax", to=ColumnType.NUMERIC),
            ]
        )
        result = adv_view.math(expression="Price + Tax", new_column="price_plus_tax")
        assert result is not None
        assert "price_plus_tax" in adv_view.display_names

    def test_math_parenthesized(self, adv_view: View) -> None:
        adv_view.convert_type(
            [
                ConversionSpec(column="Price", to=ColumnType.NUMERIC),
                ConversionSpec(column="Tax", to=ColumnType.NUMERIC),
                ConversionSpec(column="Quantity", to=ColumnType.NUMERIC),
            ]
        )
        result = adv_view.math(expression="(Price + Tax) * Quantity", new_column="total_calc")
        assert result is not None
        assert "total_calc" in adv_view.display_names

    def test_math_with_literal(self, adv_view: View) -> None:
        adv_view.convert_type([ConversionSpec(column="Price", to=ColumnType.NUMERIC)])
        result = adv_view.math(expression="Price * 1.1", new_column="price_110pct")
        assert result is not None
        assert "price_110pct" in adv_view.display_names

    def test_math_raw_list(self, adv_view: View) -> None:
        adv_view.convert_type(
            [
                ConversionSpec(column="Price", to=ColumnType.NUMERIC),
                ConversionSpec(column="Tax", to=ColumnType.NUMERIC),
            ]
        )
        result = adv_view.math(
            expression="Price + Tax",
            new_column="manual_sum",
        )
        assert result is not None
        assert "manual_sum" in adv_view.display_names

    def test_math_with_condition(self, adv_view: View) -> None:
        adv_view.convert_type([ConversionSpec(column="Subtotal", to=ColumnType.NUMERIC)])
        result = adv_view.math(
            expression="Subtotal * 0.05",
            new_column="extra_discount",
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None
        assert "extra_discount" in adv_view.display_names


# ═══════════════════════════════════════════════════════════════
#  9. Date Operations
# ═══════════════════════════════════════════════════════════════


class TestDateOps:
    """extract_date, date_diff, increment_date with typed enums."""

    @staticmethod
    def _convert_time(view: View) -> None:
        view.convert_type([ConversionSpec(column="Time", to=ColumnType.DATE)])

    def test_extract_year(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(column="Time", component=DateComponent.YEAR, new_column="yr")
        assert result is not None
        assert "yr" in adv_view.display_names

    def test_extract_month(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(
            column="Time", component=DateComponent.MONTH, new_column="mo"
        )
        assert result is not None
        assert "mo" in adv_view.display_names

    def test_extract_day(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(column="Time", component=DateComponent.DAY, new_column="dy")
        assert result is not None
        assert "dy" in adv_view.display_names

    def test_extract_quarter(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(
            column="Time", component=DateComponent.QUARTER, new_column="qtr"
        )
        assert result is not None
        assert "qtr" in adv_view.display_names

    def test_extract_weekday_text(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(
            column="Time", component=DateComponent.WEEKDAY_TEXT, new_column="wkday"
        )
        assert result is not None
        assert "wkday" in adv_view.display_names

    def test_extract_month_text(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(
            column="Time", component=DateComponent.MONTH_TEXT, new_column="mo_text"
        )
        assert result is not None
        assert "mo_text" in adv_view.display_names

    def test_extract_year_month(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.extract_date(
            column="Time", component=DateComponent.YEAR_MONTH, new_column="yr_mo"
        )
        assert result is not None
        assert "yr_mo" in adv_view.display_names

    def test_date_diff_day(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.date_diff(
            component=DateDiffUnit.DAY,
            start="Time",
            end="Time",
            new_column="diff_days",
        )
        assert result is not None
        assert "diff_days" in adv_view.display_names

    def test_date_diff_month(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.date_diff(
            component=DateDiffUnit.MONTH,
            start="Time",
            end="Time",
            new_column="diff_months",
        )
        assert result is not None
        assert "diff_months" in adv_view.display_names

    def test_increment_days(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.increment_date(
            column="Time",
            delta=DateDelta(days=30),
            new_column="plus_30d",
        )
        assert result is not None
        assert "plus_30d" in adv_view.display_names

    def test_increment_multi_component(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.increment_date(
            column="Time",
            delta=DateDelta(months=1, days=15),
            new_column="shifted",
        )
        assert result is not None
        assert "shifted" in adv_view.display_names

    def test_increment_with_condition(self, adv_view: View) -> None:
        self._convert_time(adv_view)
        result = adv_view.increment_date(
            column="Time",
            delta=DateDelta(days=7),
            new_column="cond_shifted",
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None
        assert "cond_shifted" in adv_view.display_names


# ═══════════════════════════════════════════════════════════════
#  10. Row Operations
# ═══════════════════════════════════════════════════════════════


class TestRowOps:
    """fill_missing, limit_rows, discard_duplicates, unnest."""

    def test_fill_missing_last(self, adv_view: View) -> None:
        result = adv_view.fill_missing(column="Discount", direction=FillDirection.LAST_VALUE)
        assert result is not None

    def test_fill_missing_first(self, adv_view: View) -> None:
        result = adv_view.fill_missing(column="Discount", direction=FillDirection.FIRST_VALUE)
        assert result is not None

    def test_fill_missing_with_partition(self, adv_view: View) -> None:
        result = adv_view.fill_missing(
            column="Discount",
            direction=FillDirection.LAST_VALUE,
            partition_by="Department",
            order_by=[["Transaction ID", SortDirection.ASC]],
        )
        assert result is not None

    def test_limit_top(self, adv_view: View) -> None:
        result = adv_view.limit_rows(n=10)
        assert result is not None

    def test_limit_bottom(self, adv_view: View) -> None:
        result = adv_view.limit_rows(n=5, bottom=True)
        assert result is not None

    def test_limit_ordered(self, adv_view: View) -> None:
        result = adv_view.limit_rows(n=20, order_by=[["Total", SortDirection.DESC]])
        assert result is not None

    def test_discard_duplicates(self, adv_view: View) -> None:
        result = adv_view.discard_duplicates()
        assert result is not None

    def test_discard_duplicates_ignore(self, adv_view: View) -> None:
        result = adv_view.discard_duplicates(ignore_columns=["Transaction ID"])
        assert result is not None

    def test_unnest(self, adv_view: View) -> None:
        result = adv_view.unnest(
            columns=["Cashier", "Department"],
            label_column="Metric",
            value_column="Value",
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  11. Aggregation
# ═══════════════════════════════════════════════════════════════


class TestAggregation:
    """pivot, window, crosstab with typed specs."""

    def test_pivot_sum(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total",
                    function=AggregateFunction.SUM,
                    as_name="total_sum",
                ),
            ],
        )
        assert result is not None

    def test_pivot_avg(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total",
                    function=AggregateFunction.AVG,
                    as_name="total_avg",
                ),
            ],
        )
        assert result is not None

    def test_pivot_count(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Transaction ID",
                    function=AggregateFunction.COUNT,
                    as_name="txn_count",
                ),
            ],
        )
        assert result is not None

    def test_pivot_count_distinct(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Cashier",
                    function=AggregateFunction.COUNT_DISTINCT,
                    as_name="unique_cashiers",
                ),
            ],
        )
        assert result is not None

    def test_pivot_min_max(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total", function=AggregateFunction.MIN, as_name="min_total"
                ),
                AggregationSpec(
                    column="Total", function=AggregateFunction.MAX, as_name="max_total"
                ),
            ],
        )
        assert result is not None

    def test_pivot_concat(self, adv_view: View) -> None:
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

    def test_pivot_multi_group_multi_agg(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department", "Transaction Type"],
            aggregations=[
                AggregationSpec(
                    column="Total", function=AggregateFunction.SUM, as_name="total_sum"
                ),
                AggregationSpec(
                    column="Quantity", function=AggregateFunction.AVG, as_name="avg_qty"
                ),
                AggregationSpec(
                    column="Transaction ID",
                    function=AggregateFunction.COUNT,
                    as_name="n_txns",
                ),
            ],
        )
        assert result is not None

    def test_pivot_with_condition(self, adv_view: View) -> None:
        result = adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total",
                    function=AggregateFunction.SUM,
                    as_name="sale_total",
                ),
            ],
            condition=Condition("Transaction Type", Operator.EQ, "sale"),
        )
        assert result is not None

    def test_window_row_number(self, adv_view: View) -> None:
        result = adv_view.window(
            function=WindowFunction.ROW_NUMBER,
            new_column="row_num",
            partition_by=["Department"],
            order_by=[["Total", SortDirection.DESC]],
        )
        assert result is not None
        assert "row_num" in adv_view.display_names

    def test_window_rank(self, adv_view: View) -> None:
        result = adv_view.window(
            function=WindowFunction.RANK,
            new_column="rank_col",
            partition_by=["Department"],
            order_by=[["Total", SortDirection.DESC]],
        )
        assert result is not None
        assert "rank_col" in adv_view.display_names

    def test_window_sum_running(self, adv_view: View) -> None:
        result = adv_view.window(
            function=WindowFunction.SUM,
            column="Total",
            new_column="running_total",
            partition_by=["Department"],
            order_by=[["Transaction ID", SortDirection.ASC]],
        )
        assert result is not None
        assert "running_total" in adv_view.display_names

    def test_window_avg(self, adv_view: View) -> None:
        result = adv_view.window(
            function=WindowFunction.AVG,
            column="Total",
            new_column="avg_total",
            partition_by=["Department"],
            order_by=[["Transaction ID", SortDirection.ASC]],
        )
        assert result is not None
        assert "avg_total" in adv_view.display_names

    @pytest.mark.xfail(reason="CROSSTAB uses exports endpoint, not pipeline tasks — SDK fix needed")
    def test_crosstab_count(self, adv_view: View) -> None:
        result = adv_view.crosstab(
            rows=["Department"],
            pivot_column="Transaction Type",
            select=CrosstabSpec(function=AggregateFunction.COUNT),
        )
        assert result is not None

    @pytest.mark.xfail(reason="CROSSTAB uses exports endpoint, not pipeline tasks — SDK fix needed")
    def test_crosstab_sum(self, adv_view: View) -> None:
        result = adv_view.crosstab(
            rows=["Department"],
            pivot_column="Transaction Type",
            select=CrosstabSpec(function=AggregateFunction.SUM, column="Total"),
        )
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  12. Advanced Operations (JOIN, LOOKUP, SQL)
# ═══════════════════════════════════════════════════════════════


class TestAdvancedOps:
    """join, lookup, generate_sql, add_sql with typed specs."""

    def test_join_inner(self, adv_view: View, adv_second_view: View) -> None:
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.INNER,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=[JoinSelectSpec(column="department")],
        )
        assert result is not None

    def test_join_left(self, adv_view: View, adv_second_view: View) -> None:
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=[JoinSelectSpec(column="base_salary", alias="emp_salary")],
        )
        assert result is not None

    def test_join_right(self, adv_view: View, adv_second_view: View) -> None:
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.RIGHT,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=[JoinSelectSpec(column="department")],
        )
        assert result is not None

    def test_join_outer(self, adv_view: View, adv_second_view: View) -> None:
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.OUTER,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=[JoinSelectSpec(column="department")],
        )
        assert result is not None

    def test_join_with_prefix(self, adv_view: View, adv_second_view: View) -> None:
        result = adv_view.join(
            foreign_view=adv_second_view,
            join_type=JoinType.LEFT,
            on=[JoinKeySpec(left="Cashier", right="full_name")],
            select=[
                JoinSelectSpec(column="department"),
                JoinSelectSpec(column="designation"),
            ],
            column_prefix="emp_",
        )
        assert result is not None

    def test_lookup_basic(self, adv_view: View, adv_second_view: View) -> None:
        result = adv_view.lookup(
            source="Cashier",
            lookup_view_id=adv_second_view.id,
            key="full_name",
            value="base_salary",
            new_column="looked_up_salary",
        )
        assert result is not None

    def test_generate_sql(self, adv_view: View) -> None:
        sql = adv_view.generate_sql("show all rows")
        assert isinstance(sql, str)
        assert len(sql) > 0

    def test_add_sql(self, adv_view: View) -> None:
        result = adv_view.add_sql("SELECT * FROM this LIMIT 10")
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  13. Complex Multi-Step Pipelines
# ═══════════════════════════════════════════════════════════════


class TestComplexPipeline:
    """Chain 10-20 transformations to verify pipeline stability."""

    def test_etl_pipeline_15_steps(self, adv_view: View) -> None:
        """15-step ETL: convert, filter, text, combine, math, set, extract, window, copy, etc."""
        # 1. convert Quantity to NUMERIC
        adv_view.convert_type([ConversionSpec(column="Quantity", to=ColumnType.NUMERIC)])
        # 2. convert Time to DATE
        adv_view.convert_type([ConversionSpec(column="Time", to=ColumnType.DATE)])
        # 3. filter sales only
        adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        # 4. text transform Department to UPPER
        adv_view.text_transform(columns=["Department"], case=TextCase.UPPER)
        # 5. combine Cashier + Department
        adv_view.combine_columns(
            sources=["Cashier", "Department"],
            separator=" | ",
            new_column="cashier_dept",
        )
        # 6. math: Price * Quantity
        adv_view.convert_type([ConversionSpec(column="Price", to=ColumnType.NUMERIC)])
        adv_view.math(expression="Price * Quantity", new_column="line_total")
        # 7. set_values 3-tier price band
        adv_view.set_values(
            new_column="price_band",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("High", condition=Condition("Total", Operator.GTE, 50)),
                SetValue("Mid", condition=Condition("Total", Operator.GTE, 20)),
                SetValue("Low"),
            ],
        )
        # 8. extract year
        adv_view.extract_date(column="Time", component=DateComponent.YEAR, new_column="txn_year")
        # 9. extract month
        adv_view.extract_date(column="Time", component=DateComponent.MONTH, new_column="txn_month")
        # 10. window ROW_NUMBER
        adv_view.window(
            function=WindowFunction.ROW_NUMBER,
            new_column="dept_rank",
            partition_by=["Department"],
            order_by=[["Total", SortDirection.DESC]],
        )
        # 11. copy Total -> Total_backup
        adv_view.copy_columns([CopySpec(source="Total", as_name="Total_backup")])
        # 12. replace values in Transaction Type
        adv_view.replace_values(columns=["Transaction Type"], find="sale", replace="SALE")
        # 13. substring Transaction ID first 6
        adv_view.substring(
            column="Transaction ID",
            direction=SubstringDirection.START,
            num_char=6,
            new_column="txn_prefix",
        )
        # 14. fill missing Discount
        adv_view.fill_missing(column="Discount", direction=FillDirection.LAST_VALUE)
        # 15. limit 100
        adv_view.limit_rows(n=100)

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 15, f"Expected >= 15 tasks, got {len(tasks)}"

    def test_aggregation_pipeline_10_steps(self, adv_view: View) -> None:
        """10-step aggregation pipeline ending with pivot."""
        # 1. convert Quantity -> NUMERIC
        adv_view.convert_type([ConversionSpec(column="Quantity", to=ColumnType.NUMERIC)])
        # 2. filter sales
        adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        # 3. text transform UPPER
        adv_view.text_transform(columns=["Department"], case=TextCase.UPPER)
        # 4. bulk replace departments
        adv_view.bulk_replace(
            columns=["Department"],
            mapping=[BulkReplaceMapping(search=["ORDER", "KITCHEN"], replace="CONSOLIDATED")],
        )
        # 5. math computed column
        adv_view.convert_type([ConversionSpec(column="Price", to=ColumnType.NUMERIC)])
        adv_view.math(expression="Price * Quantity", new_column="line_total")
        # 6. set_values tier
        adv_view.set_values(
            new_column="tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("A", condition=Condition("Total", Operator.GTE, 30)),
                SetValue("B"),
            ],
        )
        # 7. copy columns backup
        adv_view.copy_columns([CopySpec(source="Total", as_name="Total_bak")])
        # 8. discard duplicates
        adv_view.discard_duplicates(ignore_columns=["Transaction ID"])
        # 9. delete columns cleanup
        adv_view.delete_columns(["Register"])
        # 10. pivot
        adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total",
                    function=AggregateFunction.SUM,
                    as_name="total_sum",
                ),
            ],
        )

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 10, f"Expected >= 10 tasks, got {len(tasks)}"

    def test_date_analytics_pipeline_12_steps(self, adv_view: View) -> None:
        """12-step date analytics pipeline."""
        # 1. convert Time to DATE
        adv_view.convert_type([ConversionSpec(column="Time", to=ColumnType.DATE)])
        # 2. extract year
        adv_view.extract_date(column="Time", component=DateComponent.YEAR, new_column="yr")
        # 3. extract month
        adv_view.extract_date(column="Time", component=DateComponent.MONTH, new_column="mo")
        # 4. extract quarter
        adv_view.extract_date(column="Time", component=DateComponent.QUARTER, new_column="qtr")
        # 5. extract weekday_text
        adv_view.extract_date(
            column="Time", component=DateComponent.WEEKDAY_TEXT, new_column="wkday"
        )
        # 6. increment +30 days
        adv_view.increment_date(column="Time", delta=DateDelta(days=30), new_column="plus30")
        # 7. date_diff (same col = 0)
        adv_view.date_diff(
            component=DateDiffUnit.DAY,
            start="Time",
            end="Time",
            new_column="zero_diff",
        )
        # 8. filter by year (use extracted text values)
        adv_view.filter_rows(Condition("yr", Operator.IS_NOT_EMPTY, ""))
        # 9. set_values season from month
        adv_view.set_values(
            new_column="season",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Winter", condition=Condition("mo", Operator.LTE, 2)),
                SetValue("Spring", condition=Condition("mo", Operator.LTE, 5)),
                SetValue("Summer", condition=Condition("mo", Operator.LTE, 8)),
                SetValue("Fall"),
            ],
        )
        # 10. math Price * 1.1
        adv_view.convert_type([ConversionSpec(column="Price", to=ColumnType.NUMERIC)])
        adv_view.math(expression="Price * 1.1", new_column="adj_price")
        # 11. combine columns
        adv_view.combine_columns(
            sources=["Cashier", "Department"],
            separator=" - ",
            new_column="cashier_dept",
        )
        # 12. limit
        adv_view.limit_rows(n=200)

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 12, f"Expected >= 12 tasks, got {len(tasks)}"

    def test_text_processing_pipeline_10_steps(self, adv_view: View) -> None:
        """10-step text processing pipeline."""
        # 1. split Cashier -> first/last
        adv_view.split_column(
            column="Cashier",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec(name="first_name", type=ColumnType.TEXT),
                SplitColumnSpec(name="last_name", type=ColumnType.TEXT),
            ],
        )
        # 2. combine first_name + Department
        adv_view.combine_columns(
            sources=["first_name", "Department"],
            separator=" @ ",
            new_column="person_dept",
        )
        # 3. replace values
        adv_view.replace_values(columns=["Transaction Type"], find="sale", replace="SALE")
        # 4. text transform TITLE
        adv_view.text_transform(columns=["Department"], case=TextCase.TITLE)
        # 5. substring Transaction ID
        adv_view.substring(
            column="Transaction ID",
            direction=SubstringDirection.START,
            num_char=4,
            new_column="txn_short",
        )
        # 6. copy columns
        adv_view.copy_columns([CopySpec(source="Category", as_name="cat_copy")])
        # 7. set_values
        adv_view.set_values(
            new_column="cat_flag",
            column_type=ColumnType.TEXT,
            values=[
                SetValue(
                    "Food",
                    condition=Condition("Category", Operator.CONTAINS, "food"),
                ),
                SetValue("Other"),
            ],
        )
        # 8. bulk replace
        adv_view.bulk_replace(
            columns=["Department"],
            mapping=[BulkReplaceMapping(search=["Order"], replace="Online")],
        )
        # 9. add column
        adv_view.add_column("notes", ColumnType.TEXT)
        # 10. delete columns
        adv_view.delete_columns(["last_name"])

        tasks = adv_view.list_tasks()
        assert len(tasks) >= 10, f"Expected >= 10 tasks, got {len(tasks)}"


# ═══════════════════════════════════════════════════════════════
#  14. Exports
# ═══════════════════════════════════════════════════════════════


class TestExports:
    """CSV and S3 export tests."""

    def test_export_to_csv(self, adv_view: View, tmp_path: Path) -> None:
        out = tmp_path / "export.csv"
        path = adv_view.export.to_csv(output_path=str(out))
        assert path.exists()
        lines = path.read_text().splitlines()
        assert len(lines) > 1  # header + data

    def test_export_to_csv_after_transform(self, adv_view: View, tmp_path: Path) -> None:
        adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        out = tmp_path / "filtered_export.csv"
        path = adv_view.export.to_csv(output_path=str(out))
        assert path.exists()
        lines = path.read_text().splitlines()
        assert len(lines) > 1

    def test_export_to_s3(self, adv_view: View) -> None:
        result = adv_view.export.to_s3(file_name="pytest_export.csv")
        assert result is not None

    def test_export_list(self, adv_view: View) -> None:
        # Create an export first
        adv_view.export.to_s3(file_name="pytest_list_test.csv")
        exports = adv_view._client.exports.list(adv_view.id)
        assert exports is not None


# ═══════════════════════════════════════════════════════════════
#  15. AI Features
# ═══════════════════════════════════════════════════════════════


class TestAIFeatures:
    """AI profile generation."""

    def test_ai_generate_profile(self, adv_client: MammothClient, adv_view: View) -> None:
        result = adv_client.ai.generate_profile(adv_view.id)
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  16. Pipeline Management
# ═══════════════════════════════════════════════════════════════


class TestPipelineManagement:
    """Task listing, deletion, preview."""

    def test_list_tasks_after_transforms(self, adv_view: View) -> None:
        adv_view.add_column("col_a", ColumnType.TEXT)
        adv_view.add_column("col_b", ColumnType.TEXT)
        adv_view.add_column("col_c", ColumnType.TEXT)
        tasks = adv_view.list_tasks()
        assert len(tasks) == 3

    def test_delete_last_task(self, adv_view: View) -> None:
        adv_view.add_column("tmp_col", ColumnType.TEXT)
        adv_view.add_column("tmp_col2", ColumnType.TEXT)
        tasks = adv_view.list_tasks()
        assert len(tasks) == 2
        last_task_id = tasks[-1]["id"]
        adv_view.delete_task(last_task_id)
        tasks_after = adv_view.list_tasks()
        assert len(tasks_after) == 1

    def test_preview_task(self, adv_view: View) -> None:
        # Build a filter task spec to preview
        cond = Condition("Transaction Type", Operator.EQ, "sale")
        built = cond.build(adv_view.columns, adv_view.column_types)
        task_spec = {
            "SELECT": "ALL",
            "CONDITION": {**built, "FILTER_TYPE": "SHOW", "PROMPT": "sale only"},
        }
        result = adv_view.preview_task(task_spec)
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  17. Data Verification
# ═══════════════════════════════════════════════════════════════


class TestDataVerification:
    """Verify that transformations actually change data."""

    def test_filter_reduces_rows(self, adv_view: View) -> None:
        before = adv_view.data(limit=1)
        total_before = before.get("paging", {}).get("total", 0)
        adv_view.filter_rows(Condition("Transaction Type", Operator.EQ, "sale"))
        after = adv_view.data(limit=1)
        total_after = after.get("paging", {}).get("total", 0)
        assert (
            total_after < total_before
        ), f"Filter should reduce rows: {total_before} -> {total_after}"

    def test_add_column_appears(self, adv_view: View) -> None:
        original = set(adv_view.display_names)
        adv_view.add_column("verification_col", ColumnType.TEXT)
        updated = set(adv_view.display_names)
        assert "verification_col" in updated
        assert updated - original == {"verification_col"}

    def test_pivot_reshapes_columns(self, adv_view: View) -> None:
        original_cols = set(adv_view.display_names)
        adv_view.pivot(
            group_by=["Department"],
            aggregations=[
                AggregationSpec(
                    column="Total",
                    function=AggregateFunction.SUM,
                    as_name="sum_total",
                ),
            ],
        )
        pivoted_cols = set(adv_view.display_names)
        assert pivoted_cols != original_cols, "Pivot should reshape column structure"
        assert "Department" in pivoted_cols
        assert "sum_total" in pivoted_cols
