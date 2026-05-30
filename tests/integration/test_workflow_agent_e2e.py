"""End-to-end workflow-agent integration tests against a real Mammoth DEV instance.

Targets a DEV instance only — NOT production.  Credentials are read exclusively
from environment variables; the module is skipped when any of them is unset so
the test suite stays green in CI without secrets.

Required environment variables
-------------------------------
MAMMOTH_BASE_URL       e.g. https://dev.mammoth.io/api/v2
MAMMOTH_API_KEY        API key for the test account
MAMMOTH_API_SECRET     API secret for the test account
MAMMOTH_WORKSPACE_ID   Numeric workspace ID (will be cast to int)

Run against a DEV instance::

    MAMMOTH_BASE_URL=https://dev.mammoth.io/api/v2 \\
    MAMMOTH_API_KEY=... MAMMOTH_API_SECRET=... MAMMOTH_WORKSPACE_ID=5 \\
    pytest tests/integration/test_workflow_agent_e2e.py -v

Tests apply transforms in draft mode where supported and clean up created
tasks in teardown, leaving the workspace exactly as it was found.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from mammoth import MammothClient
from mammoth.condition import Condition
from mammoth.models.pipeline import ColumnType, FilterType, JsonType, Operator, TextCase

# ── Env-var guards ────────────────────────────────────────────────────────────

_REQUIRED_ENV = (
    "MAMMOTH_BASE_URL",
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
)

_missing = [v for v in _REQUIRED_ENV if not os.environ.get(v)]

pytestmark = pytest.mark.skipif(
    bool(_missing),
    reason=f"Missing env vars: {', '.join(_missing)}",
)

# ── Session-scoped client ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client() -> MammothClient:
    """Authenticated MammothClient built from environment variables.

    A project id is required for the project-scoped dataview/dataset endpoints,
    so it is set on the client when ``MAMMOTH_PROJECT_ID`` is provided.
    """
    c = MammothClient(
        api_key=os.environ["MAMMOTH_API_KEY"],
        api_secret=os.environ["MAMMOTH_API_SECRET"],
        workspace_id=int(os.environ["MAMMOTH_WORKSPACE_ID"]),
        base_url=os.environ["MAMMOTH_BASE_URL"],
    )
    project_id = os.environ.get("MAMMOTH_PROJECT_ID")
    if project_id:
        c.set_project_id(int(project_id))
    return c


@pytest.fixture(scope="module")
def dataset_id(client: MammothClient) -> Iterator[int]:
    """Provide a dataset with a hydrated view to run e2e transforms against.

    Honors an explicit ``MAMMOTH_DATASET_ID`` when set; otherwise uploads a
    small CSV and deletes it in teardown, so the test is self-contained and
    safe to re-run without depending on pre-existing project data (the list
    endpoint does not report a usable per-dataset ``status`` on this backend).
    """
    explicit = os.environ.get("MAMMOTH_DATASET_ID")
    if explicit:
        yield int(explicit)
        return
    csv_path = Path(__file__).resolve().parent.parent.parent / "employee.csv"
    ds_id = client.files.upload(str(csv_path))
    assert isinstance(ds_id, int), f"upload did not return a single dataset id: {ds_id!r}"
    try:
        yield ds_id
    finally:
        with contextlib.suppress(Exception):
            client.datasets.delete(ds_id)


def _task_ids(view) -> set[int]:
    """Return the set of pipeline task ids currently on a view."""
    ids: set[int] = set()
    for t in view.list_tasks():
        tid = t.get("id") or t.get("task_id")
        if tid is not None:
            ids.add(int(tid))
    return ids


@pytest.fixture
def view(client: MammothClient, dataset_id: int):
    """Yield an EXISTING ready view and restore its pipeline in teardown.

    Applying a transform mutates a real view, so we snapshot the task ids
    before the test and delete any task added during it — leaving the view's
    pipeline exactly as found.  An explicit ``MAMMOTH_VIEW_ID`` is honored;
    otherwise the first view in the dataset that has columns is used.  We use
    an existing view (not ``views.create``) because the create endpoint returns
    an unhydrated stub on this backend.
    """
    explicit = os.environ.get("MAMMOTH_VIEW_ID")
    if explicit:
        v = client.views.get(int(explicit))
    else:
        candidates = [c for c in client.views.list(dataset_id=dataset_id) if c.display_names]
        assert candidates, f"No view with columns found on dataset {dataset_id}"
        v = candidates[0]
    before = _task_ids(v)
    yield v
    with contextlib.suppress(Exception):
        v.refresh()
        for tid in _task_ids(v) - before:
            with contextlib.suppress(Exception):
                v.delete_task(tid)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _first_text_column(view) -> str:
    """Return the display name of the first TEXT-type column in the view."""
    for name, col_type in view.column_types.items():
        if col_type.upper() in ("TEXT", "STRING"):
            return name
    # Fall back to whatever the first column is
    assert view.display_names, "View has no columns"
    return view.display_names[0]


# ═══════════════════════════════════════════════════════════════════════════
#  Core transform acceptance tests
#  Each test verifies that the backend ACCEPTS the SDK call (no error, non-None
#  result).  No assertions are made about transformed row counts since we do
#  not control the upstream data.
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkflowAgentE2E:
    """Representative transforms exercised end-to-end against the DEV backend."""

    def test_convert_type_to_text(self, view):
        """convert_type: cast first column → TEXT.

        Verifies the backend accepts a CONVERT task built by the SDK's pure
        build_convert_params path.
        """
        col = view.display_names[0]
        result = view.convert_type([{"column": col, "to": ColumnType.TEXT.value}])
        assert result is not None

    def test_text_transform_trim_upper(self, view):
        """text_transform: trim + UPPER on first TEXT column.

        Verifies the backend accepts a TEXT_TRANSFORM task with both TRIM and
        CASE set — exercises the combined optional-arg path.
        """
        col = _first_text_column(view)
        result = view.text_transform(columns=[col], case=TextCase.UPPER, trim=True)
        assert result is not None

    def test_discard_duplicates(self, view):
        """discard_duplicates: no ignore_columns → consider all columns.

        Verifies the backend accepts DISCARD_DUPLICATES: True with an empty
        IGNORE_COLUMNS list.
        """
        result = view.discard_duplicates()
        assert result is not None

    def test_filter_rows_show(self, view):
        """filter_rows: keep rows matching a simple condition.

        Builds a Condition against the first column (type-agnostic EQ check)
        and verifies the SELECT task is accepted.
        """
        col = _first_text_column(view)
        cond = Condition(col, Operator.EQ, "")
        result = view.filter_rows(cond, filter_type=FilterType.SHOW)
        assert result is not None

    def test_filter_rows_remove(self, view):
        """filter_rows REMOVE: discard matching rows (REMOVE variant)."""
        col = _first_text_column(view)
        cond = Condition(col, Operator.EQ, "")
        result = view.filter_rows(cond, filter_type=FilterType.REMOVE)
        assert result is not None

    def test_add_column(self, view):
        """add_column: create a new TEXT column with a fresh internal name."""
        result = view.add_column(name="e2e_new_col", column_type=ColumnType.TEXT)
        assert result is not None

    def test_text_transform_trim_only(self, view):
        """text_transform: trim only (no case change) — exercises trim=True path."""
        col = _first_text_column(view)
        result = view.text_transform(columns=[col], trim=True)
        assert result is not None

    def test_unnest(self, view):
        """unnest: unpivot columns to rows — LABEL and VALUE dicts include INTERNAL_NAME.

        Verifies that the fixed build_unnest_params path (D1) produces a payload
        the backend accepts — previously KeyError'd on missing INTERNAL_NAME
        (validation.py:654,665).
        """
        col = _first_text_column(view)
        result = view.unnest([col])
        assert result is not None

    def test_json_extract_keys(self, view):
        """json_extract: extract keys from a JSON/TEXT column.

        Verifies that the fixed build_json_extract_params path (D2) produces
        a payload the backend accepts — each JSON_EXTRACT item now carries
        INTERNAL_NAME (validation.py:809) and TYPE in {NUMERIC,TEXT}
        (validation.py:811-812).
        """
        col = _first_text_column(view)
        result = view.json_extract(col, json_type=JsonType.OBJECT, keys=["key1"])
        assert result is not None

    def test_fill_value_emits_set_task(self, view):
        """fill_value: fill empty cells with a constant → SET task with IS_EMPTY condition.

        The FILL task silently drops literal WITH values (data corruption).
        build_fill_value_params (D3) now emits a VERSION-2 SET task with an
        IS_EMPTY condition on the target column so only empty cells are filled.
        Verifies the backend accepts the corrected SET shape.
        """
        from mammoth._pure.builders import build_fill_value_params

        col = _first_text_column(view)
        task_spec = build_fill_value_params(col, "N/A", view.columns, view._internal_names)
        # Must be a SET task, not a FILL
        assert "SET" in task_spec
        assert task_spec["VERSION"] == 2
        result = view._add_task(task_spec)
        assert result is not None

    def test_convert_to_date_with_format(self, view):
        """convert_type to DATE with FORMAT dict — exercises the D4 fix.

        build_date_normalize_params now emits FORMAT as {"date_format": <fmt>}
        (FORMAT_INFO_KEYS.DATE_FORMAT, const.py:1386; validation.py:374-383).
        A bare string FORMAT is rejected by the backend validator.
        Verifies the backend accepts the corrected dict-shaped FORMAT.
        """
        from mammoth._pure.builders import build_date_normalize_params

        col = _first_text_column(view)
        task_spec = build_date_normalize_params(
            col, view.columns, view._internal_names, formats=["%m/%d/%Y"]
        )
        assert task_spec["CONVERT"][0]["FORMAT"] == {"date_format": "%m/%d/%Y"}
        result = view._add_task(task_spec)
        assert result is not None

    # ── Cleanup verification ───────────────────────────────────────────────

    def test_tasks_are_recorded(self, view):
        """After applying at least one transform, list_tasks returns a non-empty list."""
        col = view.display_names[0]
        view.convert_type([{"column": col, "to": "TEXT"}])
        tasks = view.list_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
