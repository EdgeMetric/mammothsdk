"""Integration test fixtures: live API client and dataset management."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

import pytest

from mammoth import MammothClient

# ── Config (existing release.mammoth.io env) ─────────────────

BASE_URL = "https://release.mammoth.io/api/v2"
API_KEY = "RHXpAc2Z9HHOkZhYjICEcAcWyDAk"
API_SECRET = "1RZT8E7KoNnfkP2XU1kPojzkwHSscWB97w"
WORKSPACE_ID = 2
PROJECT_ID = 697
CSV_PATH = Path(__file__).resolve().parent.parent.parent / "employee.csv"

# ── Config (advanced tests — env vars with defaults) ──────────

ADV_BASE_URL = os.environ.get("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2")
ADV_API_KEY = os.environ.get("MAMMOTH_API_KEY", "REDACTED_CREDENTIAL")
ADV_API_SECRET = os.environ.get("MAMMOTH_API_SECRET", "REDACTED_CREDENTIAL")
ADV_WORKSPACE_ID = int(os.environ.get("MAMMOTH_WORKSPACE_ID", "304"))
ADV_PROJECT_ID = int(os.environ.get("MAMMOTH_PROJECT_ID", "1134"))
STORE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "Store_Transactions.csv"


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
def adv_client():
    """Authenticated MammothClient for advanced integration tests."""
    c = MammothClient(
        api_key=ADV_API_KEY,
        api_secret=ADV_API_SECRET,
        workspace_id=ADV_WORKSPACE_ID,
        base_url=ADV_BASE_URL,
        timeout=120,
        job_timeout=180,
    )
    c.set_project_id(ADV_PROJECT_ID)
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


@pytest.fixture(scope="session")
def adv_uploaded_dataset_id(adv_client):
    """Upload Store_Transactions.csv for advanced tests."""
    csv = STORE_CSV_PATH if STORE_CSV_PATH.exists() else CSV_PATH
    assert csv.exists(), f"Test CSV not found: {csv}"
    ds_id = adv_client.files.upload(str(csv))
    assert ds_id is not None, "Upload returned None"
    yield ds_id
    with contextlib.suppress(Exception):
        adv_client.datasets.delete(ds_id)


@pytest.fixture
def adv_view(adv_client, adv_uploaded_dataset_id):
    """Create a fresh view for each advanced test, delete after."""
    v = adv_client.views.create(dataset_id=adv_uploaded_dataset_id, name="pytest_adv_temp")
    yield v
    with contextlib.suppress(Exception):
        adv_client.views.delete(v.id, adv_uploaded_dataset_id)
