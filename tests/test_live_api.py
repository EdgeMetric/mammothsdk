"""End-to-end integration tests: upload → transform → export.

Target: release.mammoth.io
Dataset used: employee.csv (uploaded fresh per session, cleaned up after)

Run:
    pytest tests/test_live_api.py -v
    pytest tests/test_live_api.py -v -k TestTransformations
    pytest tests/test_live_api.py -v -k test_filter_rows
"""

import contextlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytestmark = pytest.mark.integration

from mammoth import Condition, MammothClient, Operator

# ── Config ────────────────────────────────────────────────────

BASE_URL = "https://release.mammoth.io/api/v2"
API_KEY = "RHXpAc2Z9HHOkZhYjICEcAcWyDAk"
API_SECRET = "1RZT8E7KoNnfkP2XU1kPojzkwHSscWB97w"
WORKSPACE_ID = 2
PROJECT_ID = 697
CSV_PATH = Path(__file__).resolve().parent.parent / "employee.csv"


# ── Session-scoped fixtures ───────────────────────────────────


@pytest.fixture(scope="session")
def client():
    """Authenticated MammothClient for the entire test session."""
    c = MammothClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )
    c.set_project_id(PROJECT_ID)
    return c


@pytest.fixture(scope="session")
def uploaded_dataset_id(client):
    """Upload employee.csv once, return dataset_id, delete after session."""
    assert CSV_PATH.exists(), f"Test CSV not found: {CSV_PATH}"
    ds_id = client.files.upload(str(CSV_PATH))
    assert ds_id is not None, "Upload returned None"
    yield ds_id
    # Cleanup: delete the dataset after all tests
    with contextlib.suppress(Exception):
        client.datasets.delete(ds_id)


@pytest.fixture(scope="session")
def base_view_id(client, uploaded_dataset_id):
    """Get the default view created by the upload."""
    views = client.views.list(uploaded_dataset_id)
    assert len(views) > 0, "No views found for uploaded dataset"
    return views[0].id


# ── Per-test fixture: fresh view ──────────────────────────────


@pytest.fixture
def view(client, uploaded_dataset_id):
    """Create a fresh view for each test, delete after."""
    v = client.views.create(dataset_id=uploaded_dataset_id, name="pytest_temp")
    yield v
    with contextlib.suppress(Exception):
        client.views.delete(v.id, uploaded_dataset_id)


# ═══════════════════════════════════════════════════════════════
#  Phase 1: Upload & Dataset
# ═══════════════════════════════════════════════════════════════


class TestUploadAndDataset:
    """Verify file upload creates a usable dataset."""

    def test_upload_creates_dataset(self, uploaded_dataset_id):
        assert isinstance(uploaded_dataset_id, int)

    def test_dataset_appears_in_list(self, client, uploaded_dataset_id):
        datasets = client.datasets.list()
        ds_ids = [d["id"] for d in datasets.get("datasets", [])]
        assert uploaded_dataset_id in ds_ids

    def test_dataset_has_views(self, client, uploaded_dataset_id):
        views = client.views.list(uploaded_dataset_id)
        assert len(views) >= 1

    def test_default_view_has_columns(self, client, uploaded_dataset_id, base_view_id):
        view = client.views.get(base_view_id, uploaded_dataset_id)
        assert len(view.display_names) == 14
        assert "emp_id" in view.columns
        assert "base_salary" in view.columns
        assert "joining_date" in view.columns


# ═══════════════════════════════════════════════════════════════
#  Phase 2: View Operations
# ═══════════════════════════════════════════════════════════════


class TestViewOperations:
    """Test view CRUD and metadata."""

    def test_create_view(self, client, uploaded_dataset_id):
        v = client.views.create(dataset_id=uploaded_dataset_id, name="test_create")
        assert v.id is not None
        assert len(v.display_names) == 14
        client.views.delete(v.id, uploaded_dataset_id)

    def test_get_view(self, client, uploaded_dataset_id, base_view_id):
        v = client.views.get(base_view_id, uploaded_dataset_id)
        assert v.id == base_view_id
        assert v.name is not None

    def test_get_column_mapping(self, view):
        mapping = view.get_column_mapping()
        assert "emp_id" in mapping
        assert mapping["emp_id"].startswith("column_")

    def test_data_access(self, view):
        data = view.data(limit=5)
        assert data is not None

    def test_list_tasks_empty(self, view):
        tasks = view.list_tasks()
        assert isinstance(tasks, list)

    def test_refresh(self, view):
        view.refresh()
        assert len(view.display_names) == 14


# ═══════════════════════════════════════════════════════════════
#  Phase 3: Transformations
# ═══════════════════════════════════════════════════════════════


class TestTransformations:
    """Test every transformation method against the live API."""

    # ── Column operations ─────────────────────────────────────

    def test_add_column(self, view):
        result = view.add_column(name="new_col", column_type="TEXT")
        assert result is not None

    def test_delete_columns(self, view):
        result = view.delete_columns(["gender"])
        assert result is not None

    def test_copy_columns(self, view):
        result = view.copy_columns(
            [
                {"source": "emp_id", "as": "emp_id_copy", "type": "TEXT"},
            ]
        )
        assert result is not None

    # ── Filter & Select ───────────────────────────────────────

    def test_filter_rows_eq(self, view):
        cond = Condition("department", Operator.EQ, "Engineering")
        result = view.filter_rows(cond)
        assert result is not None

    def test_filter_rows_compound(self, view):
        cond = Condition("department", Operator.EQ, "Engineering") & Condition(
            "base_salary", Operator.GTE, 80000
        )
        result = view.filter_rows(cond)
        assert result is not None

    def test_filter_rows_or(self, view):
        cond = Condition("department", Operator.EQ, "Engineering") | Condition(
            "department", Operator.EQ, "Sales"
        )
        result = view.filter_rows(cond)
        assert result is not None

    # ── SET (label/insert) ────────────────────────────────────

    def test_set_values_new_column(self, view):
        result = view.set_values(
            new_column="salary_tier",
            column_type="TEXT",
            values=[
                {"value": "High", "condition": Condition("base_salary", Operator.GTE, 100000)},
                {"value": "Medium", "condition": Condition("base_salary", Operator.GTE, 50000)},
                {"value": "Low"},
            ],
        )
        assert result is not None

    def test_set_values_existing_column(self, view):
        result = view.set_values(
            existing_column="employment_type",
            values=[{"value": "Active"}],
        )
        assert result is not None

    # ── Text operations ───────────────────────────────────────

    def test_combine_columns(self, view):
        result = view.combine_columns(
            sources=["full_name", "department"],
            separator=" - ",
            new_column="name_dept",
        )
        assert result is not None

    def test_replace_values(self, view):
        result = view.replace_values(
            columns=["department"],
            find="Engineering",
            replace="Eng",
        )
        assert result is not None

    def test_text_transform_upper(self, view):
        result = view.text_transform(columns=["department"], case="UPPER")
        assert result is not None

    def test_text_transform_trim(self, view):
        result = view.text_transform(columns=["full_name"], trim=True)
        assert result is not None

    def test_split_column(self, view):
        result = view.split_column(
            column="full_name",
            delimiter=" ",
            new_columns=[
                {"name": "First", "type": "TEXT"},
                {"name": "Last", "type": "TEXT"},
            ],
        )
        assert result is not None

    def test_substring_start(self, view):
        result = view.substring(
            column="full_name",
            direction="START",
            num_char=5,
            new_column="name_prefix",
        )
        assert result is not None

    # ── Type conversion ───────────────────────────────────────

    def test_convert_type(self, view):
        result = view.convert_type([{"column": "emp_id", "to": "TEXT"}])
        assert result is not None

    # ── Math ──────────────────────────────────────────────────

    def test_math(self, view):
        result = view.math(
            expression=[
                {"TYPE": "COLUMN", "VALUE": "base_salary"},
                {"TYPE": "OPERATOR", "VALUE": "*"},
                {"TYPE": "COLUMN", "VALUE": "bonus_pct"},
            ],
            new_column="bonus_amount",
        )
        assert result is not None

    # ── Date operations ───────────────────────────────────────

    def test_extract_date_year(self, view):
        # joining_date is TEXT in CSV upload; convert to DATE first
        view.convert_type([{"column": "joining_date", "to": "DATE"}])
        result = view.extract_date(
            column="joining_date",
            component="year",
            new_column="join_year",
        )
        assert result is not None

    def test_extract_date_month(self, view):
        view.convert_type([{"column": "joining_date", "to": "DATE"}])
        result = view.extract_date(
            column="joining_date",
            component="month",
            new_column="join_month",
        )
        assert result is not None

    def test_increment_date(self, view):
        view.convert_type([{"column": "joining_date", "to": "DATE"}])
        result = view.increment_date(
            column="joining_date",
            delta={"DAY": 30},
            new_column="joining_plus_30",
        )
        assert result is not None

    def test_date_diff(self, view):
        view.convert_type([{"column": "joining_date", "to": "DATE"}])
        result = view.date_diff(
            component="DAY",
            start="joining_date",
            end="joining_date",
            new_column="zero_diff",
        )
        assert result is not None

    # ── Row operations ────────────────────────────────────────

    def test_fill_missing(self, view):
        result = view.fill_missing(
            column="exit_date",
            direction="LAST_VALUE",
        )
        assert result is not None

    def test_limit_rows(self, view):
        result = view.limit_rows(n=5)
        assert result is not None

    def test_limit_rows_with_order(self, view):
        result = view.limit_rows(
            n=5,
            order_by=[["base_salary", "DESC"]],
        )
        assert result is not None

    def test_discard_duplicates(self, view):
        result = view.discard_duplicates()
        assert result is not None

    def test_discard_duplicates_ignore(self, view):
        result = view.discard_duplicates(ignore_columns=["emp_id"])
        assert result is not None

    # ── Aggregation ───────────────────────────────────────────

    def test_pivot(self, view):
        result = view.pivot(
            group_by=["department"],
            aggregations=[
                {"column": "base_salary", "function": "AVG", "as": "avg_salary"},
            ],
        )
        assert result is not None

    def test_pivot_multi_agg(self, view):
        result = view.pivot(
            group_by=["department"],
            aggregations=[
                {"column": "base_salary", "function": "SUM", "as": "total_salary"},
                {"column": "base_salary", "function": "COUNT", "as": "headcount"},
            ],
        )
        assert result is not None

    # ── Window functions ──────────────────────────────────────

    def test_window_row_number(self, view):
        result = view.window(
            function="ROW_NUMBER",
            new_column="row_num",
            partition_by=["department"],
            order_by=[["base_salary", "DESC"]],
        )
        assert result is not None

    def test_window_sum(self, view):
        result = view.window(
            function="SUM",
            column="base_salary",
            new_column="running_salary",
            partition_by=["department"],
            order_by=[["base_salary", "ASC"]],
        )
        assert result is not None

    # ── SQL ───────────────────────────────────────────────────

    def test_sql(self, view):
        result = view.sql(intent="count employees by department")
        assert result is not None


# ═══════════════════════════════════════════════════════════════
#  Phase 4: Multi-step pipeline
# ═══════════════════════════════════════════════════════════════


class TestMultiStepPipeline:
    """Apply multiple transforms on one view to verify chaining."""

    def test_chain_filter_then_math(self, view):
        # Step 1: filter
        r1 = view.filter_rows(Condition("department", Operator.EQ, "Engineering"))
        assert r1 is not None
        # Step 2: math on filtered view
        r2 = view.math(
            expression=[
                {"TYPE": "COLUMN", "VALUE": "base_salary"},
                {"TYPE": "OPERATOR", "VALUE": "*"},
                {"TYPE": "NUMBER", "VALUE": 1.1},
            ],
            new_column="salary_with_raise",
        )
        assert r2 is not None
        # Verify both tasks exist in pipeline
        tasks = view.list_tasks()
        assert len(tasks) >= 2

    def test_chain_add_set_delete(self, view):
        # Step 1: set values (creates new column)
        r1 = view.set_values(
            new_column="status_label",
            column_type="TEXT",
            values=[
                {"value": "Senior", "condition": Condition("base_salary", Operator.GTE, 100000)},
                {"value": "Junior"},
            ],
        )
        assert r1 is not None
        # Step 2: delete original column
        r2 = view.delete_columns(["gender"])
        assert r2 is not None
        # Verify both tasks exist in pipeline
        tasks = view.list_tasks()
        assert len(tasks) >= 2


# ═══════════════════════════════════════════════════════════════
#  Phase 5: Export
# ═══════════════════════════════════════════════════════════════


class TestExport:
    """Test export to CSV (download)."""

    def test_export_to_csv(self, view, tmp_path):
        out = tmp_path / "export.csv"
        path = view.export.to_csv(output_path=str(out))
        assert path.exists()
        content = path.read_text()
        assert "emp_id" in content
        assert len(content.splitlines()) > 1
