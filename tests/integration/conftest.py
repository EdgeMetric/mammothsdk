"""Integration test fixtures: live API client and dataset management.

Credentials are read **exclusively from environment variables** — there are no
hardcoded keys/secrets and no default base URL. A fixture whose credential group
is not configured calls ``pytest.skip(...)``, so an unconfigured run skips the
affected tests rather than silently falling back to a production instance.

Three independent credential groups (each a env-var prefix):
    MAMMOTH_*  — advanced / exhaustive transform tests (``adv_client``)
    VAL_*      — full validation tests (``val_client``)
    MM_REL_*   — base transform tests (``client``)

Each group expects: ``<PREFIX>_BASE_URL``, ``<PREFIX>_API_KEY``,
``<PREFIX>_API_SECRET``, ``<PREFIX>_WORKSPACE_ID``, ``<PREFIX>_PROJECT_ID``.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

import pytest

from mammoth import MammothClient

_DATA_DIR = Path(__file__).resolve().parent.parent.parent
CSV_PATH = _DATA_DIR / "employee.csv"
STORE_CSV_PATH = _DATA_DIR / "Store_Transactions.csv"
EMPLOYEE_CSV_PATH = CSV_PATH

_CRED_SUFFIXES = ("BASE_URL", "API_KEY", "API_SECRET", "WORKSPACE_ID", "PROJECT_ID")


def _client_from_env(
    prefix: str, *, timeout: int | None = None, job_timeout: int | None = None
) -> MammothClient:
    """Build a ``MammothClient`` from the ``<prefix>_*`` env vars.

    Skips the requesting test (rather than connecting to any default host) when
    any credential in the group is missing, so tests never write to an
    unintended instance.
    """
    names = {suffix: f"{prefix}_{suffix}" for suffix in _CRED_SUFFIXES}
    missing = [name for name in names.values() if not os.environ.get(name)]
    if missing:
        pytest.skip(f"integration credentials not set: {', '.join(missing)}")
    kwargs: dict[str, int] = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    if job_timeout is not None:
        kwargs["job_timeout"] = job_timeout
    c = MammothClient(
        api_key=os.environ[names["API_KEY"]],
        api_secret=os.environ[names["API_SECRET"]],
        workspace_id=int(os.environ[names["WORKSPACE_ID"]]),
        base_url=os.environ[names["BASE_URL"]],
        **kwargs,
    )
    c.set_project_id(int(os.environ[names["PROJECT_ID"]]))
    return c


def _upload(client: MammothClient, csv_path: Path) -> int:
    assert csv_path.exists(), f"Test CSV not found: {csv_path}"
    ds_id = client.files.upload(str(csv_path))
    assert isinstance(ds_id, int), f"upload did not return a single dataset id: {ds_id!r}"
    return ds_id


# ── Base transform tests (MM_REL_*) ──────────────────────────


@pytest.fixture(scope="session")
def client() -> MammothClient:
    """Authenticated MammothClient for the base transform tests."""
    return _client_from_env("MM_REL")


@pytest.fixture(scope="session")
def uploaded_dataset_id(client: MammothClient):
    """Upload employee.csv once, return dataset_id, delete after session."""
    ds_id = _upload(client, CSV_PATH)
    yield ds_id
    with contextlib.suppress(Exception):
        client.datasets.delete(ds_id)


@pytest.fixture(scope="session")
def base_view_id(client: MammothClient, uploaded_dataset_id: int) -> int:
    """Get the default view created by the upload."""
    views = client.views.list(uploaded_dataset_id)
    assert len(views) > 0, "No views found for uploaded dataset"
    return views[0].id


@pytest.fixture
def view(client: MammothClient, uploaded_dataset_id: int):
    """Create a fresh view for each test, delete after."""
    v = client.views.create(dataset_id=uploaded_dataset_id, name="pytest_temp")
    yield v
    with contextlib.suppress(Exception):
        client.views.delete(v.id)


# ── Advanced / exhaustive transform tests (MAMMOTH_*) ─────────


@pytest.fixture(scope="session")
def adv_client() -> MammothClient:
    """Authenticated MammothClient for advanced integration tests."""
    return _client_from_env("MAMMOTH", timeout=120, job_timeout=180)


@pytest.fixture(scope="session")
def adv_uploaded_dataset_id(adv_client: MammothClient):
    """Upload Store_Transactions.csv for advanced tests."""
    csv = STORE_CSV_PATH if STORE_CSV_PATH.exists() else CSV_PATH
    ds_id = _upload(adv_client, csv)
    yield ds_id
    with contextlib.suppress(Exception):
        adv_client.datasets.delete(ds_id)


@pytest.fixture
def adv_view(adv_client: MammothClient, adv_uploaded_dataset_id: int):
    """Create a fresh view for each advanced test, delete after."""
    v = adv_client.views.create(dataset_id=adv_uploaded_dataset_id, name="pytest_adv_temp")
    yield v
    with contextlib.suppress(Exception):
        adv_client.views.delete(v.id)


@pytest.fixture(scope="session")
def adv_second_dataset_id(adv_client: MammothClient):
    """Upload employee.csv as a second dataset for JOIN/LOOKUP tests."""
    ds_id = _upload(adv_client, EMPLOYEE_CSV_PATH)
    yield ds_id
    with contextlib.suppress(Exception):
        adv_client.datasets.delete(ds_id)


@pytest.fixture
def adv_second_view(adv_client: MammothClient, adv_second_dataset_id: int):
    """Create a fresh view on the second (employee) dataset."""
    v = adv_client.views.create(dataset_id=adv_second_dataset_id, name="pytest_adv_second")
    yield v
    with contextlib.suppress(Exception):
        adv_client.views.delete(v.id)


# ── Full validation tests (VAL_*) ────────────────────────────


@pytest.fixture(scope="session")
def val_client() -> MammothClient:
    """Authenticated MammothClient for full validation tests."""
    return _client_from_env("VAL", timeout=120, job_timeout=180)


@pytest.fixture(scope="session")
def val_uploaded_dataset_id(val_client: MammothClient):
    """Upload employee.csv for validation tests."""
    ds_id = _upload(val_client, CSV_PATH)
    yield ds_id
    with contextlib.suppress(Exception):
        val_client.datasets.delete(ds_id)


@pytest.fixture
def val_view(val_client: MammothClient, val_uploaded_dataset_id: int):
    """Create a fresh view for each validation test, delete after."""
    v = val_client.views.create(dataset_id=val_uploaded_dataset_id, name="pytest_val_temp")
    yield v
    with contextlib.suppress(Exception):
        val_client.views.delete(v.id)


@pytest.fixture(scope="session")
def val_second_dataset_id(val_client: MammothClient):
    """Upload employee.csv as a second dataset for branch-out tests."""
    ds_id = _upload(val_client, EMPLOYEE_CSV_PATH)
    yield ds_id
    with contextlib.suppress(Exception):
        val_client.datasets.delete(ds_id)
