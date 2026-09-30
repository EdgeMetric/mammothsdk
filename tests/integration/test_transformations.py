"""End-to-end integration tests: upload -> transform -> export.

Target: release.mammoth.io
Dataset used: employee.csv (uploaded fresh per session, cleaned up after)

Run:
    pytest tests/integration/test_transformations.py -v
    pytest tests/integration/ -v -k TestTransformations
"""

from __future__ import annotations

import pytest

from mammoth import (
    AggregateFunction,
    AggregationSpec,
    ColumnType,
    Condition,
    ConversionSpec,
    CopySpec,
    DateComponent,
    DateDelta,
    DateDiffUnit,
    FillDirection,
    Operator,
    SetValue,
    SortDirection,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
    WindowFunction,
)

# The session fixtures open the client's connection pool; tests must share their loop.
pytestmark = pytest.mark.asyncio(loop_scope="session")

# ═══════════════════════════════════════════════════════════════
#  Phase 1: Upload & Dataset
# ═══════════════════════════════════════════════════════════════


class TestUploadAndDataset:
    """Verify file upload creates a usable dataset."""

    async def test_upload_creates_dataset(self, uploaded_dataset_id):
        assert isinstance(uploaded_dataset_id, int)

    async def test_dataset_appears_in_list(self, client, uploaded_dataset_id):
        datasets = await client.datasets.list()
        ds_ids = [d["id"] for d in datasets.get("datasets", [])]
        assert uploaded_dataset_id in ds_ids

    async def test_dataset_has_views(self, client, uploaded_dataset_id):
        views = await client.views.list(uploaded_dataset_id)
        assert len(views) >= 1

    async def test_default_view_has_columns(self, client, uploaded_dataset_id, base_view_id):
        view = await client.views.get(base_view_id, uploaded_dataset_id)
        assert len(view.display_names) == 14
        assert "emp_id" in view.columns
        assert "base_salary" in view.columns
        assert "joining_date" in view.columns


# ═══════════════════════════════════════════════════════════════
#  Phase 2: View Operations
# ═══════════════════════════════════════════════════════════════


class TestViewOperations:
    """Test view CRUD and metadata."""

    async def test_create_view(self, client, uploaded_dataset_id):
        v = await client.views.create(dataset_id=uploaded_dataset_id, name="test_create")
        assert v.id is not None
        assert len(v.display_names) == 14
        await client.views.delete(v.id, uploaded_dataset_id)

    async def test_get_view(self, client, uploaded_dataset_id, base_view_id):
        v = await client.views.get(base_view_id, uploaded_dataset_id)
        assert v.id == base_view_id
        assert v.name is not None

    async def test_get_column_mapping(self, view):
        mapping = view.get_column_mapping()
        assert "emp_id" in mapping
        assert mapping["emp_id"].startswith("column_")

    async def test_data_access(self, view):
        data = await view.data(limit=5)
        assert data is not None

    async def test_list_tasks_empty(self, view):
        tasks = await view.list_tasks()
        assert isinstance(tasks, list)

    async def test_refresh(self, view):
        await view.refresh()
        assert len(view.display_names) == 14


# ═══════════════════════════════════════════════════════════════
#  Phase 3: Transformations
# ═══════════════════════════════════════════════════════════════


class TestTransformations:
    """Test every transformation method against the live API."""

    # ── Column operations ─────────────────────────────────────

    async def test_add_column(self, view):
        result = await view.add_column(name="new_col", column_type=ColumnType.TEXT)
        assert result is not None

    async def test_delete_columns(self, view):
        result = await view.delete_columns(["gender"])
        assert result is not None

    async def test_copy_columns(self, view):
        result = await view.copy_columns(
            [
                CopySpec(source="emp_id", as_name="emp_id_copy", type=ColumnType.TEXT),
            ]
        )
        assert result is not None

    # ── Filter & Select ───────────────────────────────────────

    async def test_filter_rows_eq(self, view):
        cond = Condition("department", Operator.EQ, "Engineering")
        result = await view.filter_rows(cond)
        assert result is not None

    async def test_filter_rows_compound(self, view):
        cond = Condition("department", Operator.EQ, "Engineering") & Condition(
            "base_salary", Operator.GTE, 80000
        )
        result = await view.filter_rows(cond)
        assert result is not None

    async def test_filter_rows_or(self, view):
        cond = Condition("department", Operator.EQ, "Engineering") | Condition(
            "department", Operator.EQ, "Sales"
        )
        result = await view.filter_rows(cond)
        assert result is not None

    # ── SET (label/insert) ────────────────────────────────────

    async def test_set_values_new_column(self, view):
        result = await view.set_values(
            new_column="salary_tier",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("High", condition=Condition("base_salary", Operator.GTE, 100000)),
                SetValue("Medium", condition=Condition("base_salary", Operator.GTE, 50000)),
                SetValue("Low"),
            ],
        )
        assert result is not None

    async def test_set_values_existing_column(self, view):
        result = await view.set_values(
            existing_column="employment_type",
            values=[SetValue("Active")],
        )
        assert result is not None

    # ── Text operations ───────────────────────────────────────

    async def test_combine_columns(self, view):
        result = await view.combine_columns(
            sources=["full_name", "department"],
            separator=" - ",
            new_column="name_dept",
        )
        assert result is not None

    async def test_replace_values(self, view):
        result = await view.replace_values(
            columns=["department"],
            find="Engineering",
            replace="Eng",
        )
        assert result is not None

    async def test_text_transform_upper(self, view):
        result = await view.text_transform(columns=["department"], case=TextCase.UPPER)
        assert result is not None

    async def test_text_transform_trim(self, view):
        result = await view.text_transform(columns=["full_name"], trim=True)
        assert result is not None

    async def test_split_column(self, view):
        result = await view.split_column(
            column="full_name",
            delimiter=" ",
            new_columns=[
                SplitColumnSpec(name="First", type=ColumnType.TEXT),
                SplitColumnSpec(name="Last", type=ColumnType.TEXT),
            ],
        )
        assert result is not None

    async def test_substring_start(self, view):
        result = await view.substring(
            column="full_name",
            direction=SubstringDirection.START,
            num_char=5,
            new_column="name_prefix",
        )
        assert result is not None

    # ── Type conversion ───────────────────────────────────────

    async def test_convert_type(self, view):
        result = await view.convert_type([ConversionSpec(column="emp_id", to=ColumnType.TEXT)])
        assert result is not None

    # ── Math ──────────────────────────────────────────────────

    async def test_math(self, view):
        result = await view.math(
            expression="base_salary * bonus_pct",
            new_column="bonus_amount",
        )
        assert result is not None

    async def test_math_string_expression(self, view):
        result = await view.math(
            expression="base_salary * bonus_pct",
            new_column="bonus_calc",
        )
        assert result is not None

    # ── Date operations ───────────────────────────────────────

    async def test_extract_date_year(self, view):
        await view.convert_type([ConversionSpec(column="joining_date", to=ColumnType.DATE)])
        result = await view.extract_date(
            column="joining_date",
            component=DateComponent.YEAR,
            new_column="join_year",
        )
        assert result is not None

    async def test_extract_date_month(self, view):
        await view.convert_type([ConversionSpec(column="joining_date", to=ColumnType.DATE)])
        result = await view.extract_date(
            column="joining_date",
            component=DateComponent.MONTH,
            new_column="join_month",
        )
        assert result is not None

    async def test_increment_date(self, view):
        await view.convert_type([ConversionSpec(column="joining_date", to=ColumnType.DATE)])
        result = await view.increment_date(
            column="joining_date",
            delta=DateDelta(days=30),
            new_column="joining_plus_30",
        )
        assert result is not None

    async def test_date_diff(self, view):
        await view.convert_type([ConversionSpec(column="joining_date", to=ColumnType.DATE)])
        result = await view.date_diff(
            component=DateDiffUnit.DAY,
            start="joining_date",
            end="joining_date",
            new_column="zero_diff",
        )
        assert result is not None

    # ── Row operations ────────────────────────────────────────

    async def test_fill_missing(self, view):
        result = await view.fill_missing(
            column="exit_date",
            direction=FillDirection.LAST_VALUE,
        )
        assert result is not None

    async def test_limit_rows(self, view):
        result = await view.limit_rows(n=5)
        assert result is not None

    async def test_limit_rows_with_order(self, view):
        result = await view.limit_rows(
            n=5,
            order_by=[["base_salary", SortDirection.DESC]],
        )
        assert result is not None

    async def test_discard_duplicates(self, view):
        result = await view.discard_duplicates()
        assert result is not None

    async def test_discard_duplicates_ignore(self, view):
        result = await view.discard_duplicates(ignore_columns=["emp_id"])
        assert result is not None

    # ── Aggregation ───────────────────────────────────────────

    async def test_pivot(self, view):
        result = await view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="base_salary",
                    function=AggregateFunction.AVG,
                    as_name="avg_salary",
                ),
            ],
        )
        assert result is not None

    async def test_pivot_multi_agg(self, view):
        result = await view.pivot(
            group_by=["department"],
            aggregations=[
                AggregationSpec(
                    column="base_salary",
                    function=AggregateFunction.SUM,
                    as_name="total_salary",
                ),
                AggregationSpec(
                    column="base_salary",
                    function=AggregateFunction.COUNT,
                    as_name="headcount",
                ),
            ],
        )
        assert result is not None

    # ── Window functions ──────────────────────────────────────

    async def test_window_row_number(self, view):
        result = await view.window(
            function=WindowFunction.ROW_NUMBER,
            new_column="row_num",
            partition_by=["department"],
            order_by=[["base_salary", SortDirection.DESC]],
        )
        assert result is not None

    async def test_window_sum(self, view):
        result = await view.window(
            function=WindowFunction.SUM,
            column="base_salary",
            new_column="running_salary",
            partition_by=["department"],
            order_by=[["base_salary", SortDirection.ASC]],
        )
        assert result is not None

    # ── SQL ───────────────────────────────────────────────────

    async def test_sql(self, view):
        result = await view.generate_sql(intent="count employees by department")
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Phase 4: Multi-step pipeline
# ═══════════════════════════════════════════════════════════════


class TestMultiStepPipeline:
    """Apply multiple transforms on one view to verify chaining."""

    async def test_chain_filter_then_math(self, view):
        r1 = await view.filter_rows(Condition("department", Operator.EQ, "Engineering"))
        assert r1 is not None
        r2 = await view.math(
            expression="base_salary * 1.1",
            new_column="salary_with_raise",
        )
        assert r2 is not None
        tasks = await view.list_tasks()
        assert len(tasks) >= 2

    async def test_chain_add_set_delete(self, view):
        r1 = await view.set_values(
            new_column="status_label",
            column_type=ColumnType.TEXT,
            values=[
                SetValue("Senior", condition=Condition("base_salary", Operator.GTE, 100000)),
                SetValue("Junior"),
            ],
        )
        assert r1 is not None
        r2 = await view.delete_columns(["gender"])
        assert r2 is not None
        tasks = await view.list_tasks()
        assert len(tasks) >= 2


# ═══════════════════════════════════════════════════════════════
#  Phase 5: Export
# ═══════════════════════════════════════════════════════════════


class TestExport:
    """Test export to CSV (download)."""

    async def test_export_to_csv(self, view, tmp_path):
        out = tmp_path / "export.csv"
        path = await view.export.to_csv(output_path=str(out))
        assert path.exists()
        content = path.read_text()
        assert "emp_id" in content
        assert len(content.splitlines()) > 1
