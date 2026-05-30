"""Unit test fixtures: mock client, mock view data."""

from __future__ import annotations

from typing import Any, NamedTuple
from unittest.mock import MagicMock, patch

import pytest

from mammoth.client import MammothClient
from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.view import View

# Stub id the mocked export seam returns for a NEW dataset (no target_ds_id).
FAKE_NEW_DATASET_ID = 9999


class CapturedExport(NamedTuple):
    """One captured internal-dataset export call (crosstab / branch-out).

    Typed so tests assert ``capture.target_properties`` / ``capture.condition``
    instead of indexing magic string keys.
    """

    target_properties: dict[str, Any]
    timeout: int | None
    condition: Condition | CompoundCondition | NotCondition | None


# ── Sample metadata matching real API shape ──────────────────

SAMPLE_COLUMNS = [
    {
        "display_name": "emp_id",
        "internal_name": "column_abc1234567",
        "type": "TEXT",
    },
    {
        "display_name": "full_name",
        "internal_name": "column_def1234567",
        "type": "TEXT",
    },
    {
        "display_name": "department",
        "internal_name": "column_ghi1234567",
        "type": "TEXT",
    },
    {
        "display_name": "base_salary",
        "internal_name": "column_jkl1234567",
        "type": "NUMERIC",
    },
    {
        "display_name": "joining_date",
        "internal_name": "column_mno1234567",
        "type": "DATE",
    },
    {
        "display_name": "exit_date",
        "internal_name": "column_pqr1234567",
        "type": "DATE",
    },
    {
        "display_name": "gender",
        "internal_name": "column_stu1234567",
        "type": "TEXT",
    },
    {
        "display_name": "bonus_pct",
        "internal_name": "column_vwx1234567",
        "type": "NUMERIC",
    },
]

SAMPLE_VIEW_DATA = {
    "id": 1001,
    "name": "Test View",
    "properties": {
        "columns": SAMPLE_COLUMNS,
    },
}

SAMPLE_DATASET_ID = 500


@pytest.fixture
def mock_client() -> MammothClient:
    """MammothClient with a mocked session (no real HTTP calls)."""
    with patch("mammoth.client.requests.Session"):
        client = MammothClient(
            api_key="test-key",
            api_secret="test-secret",
            workspace_id=1,
        )
    client.project_id = 100
    client._request = MagicMock(return_value={})
    client.jobs = MagicMock()
    client.jobs.wait_for_job = MagicMock(return_value={"status": "SUCCESS"})
    client.pipeline = MagicMock()
    client.pipeline.add_task = MagicMock(return_value={"id": 999})
    client.pipeline.get_pipeline = MagicMock(return_value={"tasks": []})
    client.pipeline.draft_mode = MagicMock(return_value={"state": "ok"})
    client.pipeline.edit_pipeline = MagicMock(return_value={"state": "ready"})
    client.pipeline.wait_for_pipeline = MagicMock(return_value={"state": "ready"})
    return client


@pytest.fixture
def mock_view(mock_client: MammothClient) -> View:
    """View object with sample metadata and mocked _add_task."""
    view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)

    # Mock _add_task to capture payloads without HTTP calls
    captured_payloads: list[dict[str, Any]] = []

    def fake_add_task(params: dict[str, Any]) -> dict[str, Any]:
        captured_payloads.append(params)
        return {"id": len(captured_payloads), "status": "SUCCESS"}

    view._add_task = fake_add_task  # type: ignore[assignment]
    view._captured_payloads = captured_payloads  # type: ignore[attr-defined]

    # Mock the internal-dataset export seam (crosstab / branch-out) too, so
    # those mixin methods can be unit-tested without HTTP. Captures the built
    # target_properties + condition; returns a job-shaped success dict.
    captured_exports: list[CapturedExport] = []

    def fake_run_export(
        target_properties: dict[str, Any],
        timeout: int | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> int:
        captured_exports.append(CapturedExport(target_properties, timeout, condition))
        # The seam resolves and returns the materialised dataset's id (int);
        # for an existing target that's the id passed in, else a fixed stub.
        return int(target_properties.get("TARGET_DS_ID") or FAKE_NEW_DATASET_ID)

    view._run_internal_dataset_export = fake_run_export  # type: ignore[assignment]
    view._captured_exports = captured_exports  # type: ignore[attr-defined]
    return view


# ── Foreign view for JOIN tests ──────────────────────────────

FOREIGN_COLUMNS = [
    {
        "display_name": "cust_id",
        "internal_name": "column_f_abc12345",
        "type": "TEXT",
    },
    {
        "display_name": "category",
        "internal_name": "column_f_def12345",
        "type": "TEXT",
    },
    {
        "display_name": "region",
        "internal_name": "column_f_ghi12345",
        "type": "TEXT",
    },
]

FOREIGN_VIEW_DATA = {
    "id": 2050,
    "name": "Foreign View",
    "properties": {
        "columns": FOREIGN_COLUMNS,
    },
}


@pytest.fixture
def mock_foreign_view(mock_client: MammothClient) -> View:
    """Foreign View for JOIN tests — has its own columns."""
    return View(mock_client, FOREIGN_VIEW_DATA, 600)
