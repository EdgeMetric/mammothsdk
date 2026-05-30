"""End-to-end CSV-upload + transform pipeline test against a real Mammoth DEV instance.

Unlike ``test_workflow_agent_e2e.py`` (which mutates an existing view and restores
it), this test exercises the FULL data lifecycle the SDK promises:

    upload a CSV  ->  resolve the created view  ->  apply a transform  ->
    read the transformed output  ->  delete the dataset (cleanup)

It therefore covers the upload path (``client.files.upload``) and the refactored
transform mixins together, end to end, and asserts the *observable data effect*
of each transform — not merely that the backend accepted the call.

Reading the transformed data
----------------------------
``View.data()`` reads ``sequence=0`` (the original uploaded rows), so it never
reflects applied tasks. Pipeline output lives at the task's sequence number, so
these tests read via ``query_data(..., sequence=<latest task sequence>)``.

DEV-only; skipped unless the credential env vars are set, and it always deletes
the dataset it creates.

Required env vars: MAMMOTH_BASE_URL, MAMMOTH_API_KEY, MAMMOTH_API_SECRET,
MAMMOTH_WORKSPACE_ID, MAMMOTH_PROJECT_ID.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from mammoth import MammothClient
from mammoth.condition import Condition
from mammoth.models.pipeline import ColumnType, ConversionSpec, FilterType, Operator, TextCase
from mammoth.view import View

_REQUIRED_ENV = (
    "MAMMOTH_BASE_URL",
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_PROJECT_ID",
)
_missing = [v for v in _REQUIRED_ENV if not os.environ.get(v)]
pytestmark = pytest.mark.skipif(bool(_missing), reason=f"Missing env vars: {', '.join(_missing)}")

# salary values are plain integers -> the backend types this column as NUMERIC on upload.
_CSV = """name,department,salary
alice,Engineering,100
bob,Sales,90
alice,Engineering,100
carol,Marketing,80
"""


@pytest.fixture(scope="module")
def client() -> MammothClient:
    c = MammothClient(
        api_key=os.environ["MAMMOTH_API_KEY"],
        api_secret=os.environ["MAMMOTH_API_SECRET"],
        workspace_id=int(os.environ["MAMMOTH_WORKSPACE_ID"]),
        base_url=os.environ["MAMMOTH_BASE_URL"],
    )
    c.set_project_id(int(os.environ["MAMMOTH_PROJECT_ID"]))
    return c


@pytest.fixture
def uploaded_view(client: MammothClient, tmp_path: Path) -> Iterator[View]:
    """Upload a small CSV, yield its (single) view, and delete the dataset after."""
    csv_path = tmp_path / "e2e_people.csv"
    csv_path.write_text(_CSV)

    ds_id = client.files.upload(str(csv_path))
    assert isinstance(ds_id, int), f"upload did not return a single dataset id: {ds_id!r}"
    try:
        views = [v for v in client.views.list(dataset_id=ds_id) if v.display_names]
        assert views, f"no view with columns on uploaded dataset {ds_id}"
        yield views[0]
    finally:
        with contextlib.suppress(Exception):
            client.datasets.delete(ds_id)


def _latest_sequence(view: View) -> int:
    """The highest pipeline task sequence (0 when no tasks have been applied)."""
    seqs = [int(t.get("sequence", 0)) for t in view.list_tasks()]
    return max(seqs) if seqs else 0


def _rows(view: View, sequence: int | None = None) -> list[dict[str, Any]]:
    """Fetch data rows at *sequence* (defaults to the latest applied task)."""
    seq = _latest_sequence(view) if sequence is None else sequence
    resp = view._client.dataviews.query_data(
        dataset_id=view.dataset_id, dataview_id=view.id, sequence=seq, limit=100
    )
    return resp.get("data", [])


def _values(view: View, display_name: str) -> list[Any]:
    """Values of one column across all rows at the latest sequence."""
    internal = view.columns[display_name]
    return [str(r.get(internal)).strip() for r in _rows(view)]


class TestCsvUploadPipeline:
    def test_upload_creates_expected_schema(self, uploaded_view: View) -> None:
        """The uploaded CSV materializes a view with the 3 source columns and 4 base rows."""
        v = uploaded_view
        assert set(v.display_names) >= {"name", "department", "salary"}
        assert v.column_types["salary"].upper() == "NUMERIC"
        assert len(_rows(v, sequence=0)) == 4

    def test_text_transform_uppercases_values(self, uploaded_view: View) -> None:
        """text_transform UPPER rewrites the data, visible at the task's sequence."""
        v = uploaded_view
        assert v.text_transform(columns=["name"], case=TextCase.UPPER) is not None
        assert sorted(_values(v, "name")) == ["ALICE", "ALICE", "BOB", "CAROL"]

    def test_filter_rows_keeps_only_matching(self, uploaded_view: View) -> None:
        """filter_rows SHOW keeps only rows matching the condition."""
        v = uploaded_view
        result = v.filter_rows(
            Condition("department", Operator.EQ, "Engineering"), filter_type=FilterType.SHOW
        )
        assert result is not None
        assert set(_values(v, "department")) == {"Engineering"}

    def test_discard_duplicates_removes_dupe_row(self, uploaded_view: View) -> None:
        """discard_duplicates collapses the repeated alice/Engineering/100 row (4 -> 3)."""
        v = uploaded_view
        assert v.discard_duplicates() is not None
        assert len(_rows(v)) == 3

    def test_convert_and_add_column_accepted(self, uploaded_view: View) -> None:
        """convert_type (NUMERIC->TEXT) and add_column both execute without backend error.

        ``_add_task`` waits for the pipeline, so a returned (non-None) result with no
        raised ``MammothTransformError`` means the backend applied the task cleanly.
        """
        v = uploaded_view
        assert v.convert_type([ConversionSpec(column="salary", to=ColumnType.TEXT)]) is not None
        assert v.add_column("status", column_type=ColumnType.TEXT) is not None
        assert len(v.list_tasks()) == 2
