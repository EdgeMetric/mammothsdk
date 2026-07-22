"""Read-only live smoke tests against a real Mammoth tenant.

Every test drives the real CLI in-process with real credentials and asserts
the command reaches the live API and renders a well-formed success envelope.
Nothing here mutates server state: only list/get/read commands are exercised.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from mammoth_cli.testing import make_runner

pytestmark = pytest.mark.live


def _run(args: list[str], env: dict[str, str]) -> dict[str, Any]:
    """Invoke the CLI, assert a clean exit, and return the parsed envelope."""
    result = make_runner().invoke([*args, "--output", "json", "--no-input"], env=env)
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.output)
    assert not envelope.get("error"), envelope.get("error")
    assert "data" in envelope
    return envelope


def _projects(env: dict[str, str]) -> list[dict[str, Any]]:
    """Return the workspace project list from a live ``project list`` call."""
    data = _run(["project", "list"], env)["data"]
    projects = data.get("projects") if isinstance(data, dict) else data
    assert isinstance(projects, list)
    return projects


def test_authenticated_project_list(live_env: dict[str, str]) -> None:
    """`project list` authenticates and returns the workspace projects."""
    projects = _projects(live_env)
    assert all("id" in p for p in projects)


def test_configured_project_visible(live_env: dict[str, str], live_project: str) -> None:
    """The configured test project id appears in the live project list."""
    ids = {str(p.get("id")) for p in _projects(live_env)}
    assert live_project in ids, f"project {live_project} not visible in {sorted(ids)}"


def test_dataset_list(live_env: dict[str, str], live_project: str) -> None:
    """`dataset list` returns the datasets of the configured project."""
    data = _run(["dataset", "list", "--project", live_project], live_env)["data"]
    datasets = data.get("datasets") if isinstance(data, dict) else data
    assert isinstance(datasets, list)


def test_view_list_missing_id_is_usage_error(live_env: dict[str, str], live_project: str) -> None:
    """`view list` without its required dataset id fails as a usage error."""
    result = make_runner().invoke(
        ["view", "list", "--project", live_project, "--output", "json", "--no-input"],
        env=live_env,
    )
    assert result.exit_code == 2, result.output


def test_view_list_and_draft_status(live_env: dict[str, str], live_project: str) -> None:
    """List a dataset's views and read server-backed draft status, read-only.

    Skips when the configured project has no dataset to inspect, so the suite
    stays green against an empty tenant.
    """
    ds_data = _run(["dataset", "list", "--project", live_project], live_env)["data"]
    datasets = ds_data.get("datasets") if isinstance(ds_data, dict) else ds_data
    if not datasets:
        pytest.skip("no dataset in the configured project to inspect")
    dataset_id = str(datasets[0]["id"])

    view_data = _run(["view", "list", dataset_id, "--project", live_project], live_env)["data"]
    views = (
        view_data
        if isinstance(view_data, list)
        else (view_data.get("dataviews") or view_data.get("views") or [])
    )
    if not views:
        pytest.skip("no dataview to read draft status for")
    view_id = str(views[0]["id"])

    status = _run(["view", "draft", "status", view_id, "--project", live_project], live_env)["data"]
    # The server-backed status seam always reports a concrete draft flag.
    assert "is_draft" in status
