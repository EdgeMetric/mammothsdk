"""Integration test fixtures: live API client and dataset management."""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

from mammoth import MammothClient

# ── Config ────────────────────────────────────────────────────

BASE_URL = "https://release.mammoth.io/api/v2"
API_KEY = "RHXpAc2Z9HHOkZhYjICEcAcWyDAk"
API_SECRET = "1RZT8E7KoNnfkP2XU1kPojzkwHSscWB97w"
WORKSPACE_ID = 2
PROJECT_ID = 697
CSV_PATH = Path(__file__).resolve().parent.parent.parent / "employee.csv"


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
    with contextlib.suppress(Exception):
        client.datasets.delete(ds_id)


@pytest.fixture(scope="session")
def base_view_id(client, uploaded_dataset_id):
    """Get the default view created by the upload."""
    views = client.views.list(uploaded_dataset_id)
    assert len(views) > 0, "No views found for uploaded dataset"
    return views[0].id


@pytest.fixture
def view(client, uploaded_dataset_id):
    """Create a fresh view for each test, delete after."""
    v = client.views.create(dataset_id=uploaded_dataset_id, name="pytest_temp")
    yield v
    with contextlib.suppress(Exception):
        client.views.delete(v.id, uploaded_dataset_id)
