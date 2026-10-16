"""Live: the fixes for the errors the in-product agent hit (PRD-3091), against a real server.

Replaces the fake-service unit tests that stood in for these paths:
``browse search`` taking ``folder``/``dataset``, ``browse resource`` taking ``dataset``,
``browse ancestors`` of a non-folder, and ``view delete`` ending in success.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_agent_run_errors.py -m live -v
"""

from __future__ import annotations

import json

import pytest
from live_harness import LiveCli, upload_csv

pytestmark = pytest.mark.live

_CSV = "Item,Cost\nwidget,10\ngizmo,20\n"


@pytest.fixture(scope="module")
def dataset(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> int:
    folder = tmp_path_factory.mktemp("agent_run_errors")
    dataset_id, _ = upload_csv(live_cli, scratch_project, folder / "items.csv", _CSV)
    return dataset_id


def test_browse_resource_takes_dataset_as_the_datasource_type(
    live_cli: LiveCli, scratch_project: int, dataset: int
) -> None:
    data, _ = live_cli.ok("browse", "resource", "dataset", str(dataset), project=scratch_project)

    assert data["resource"]


@pytest.mark.parametrize("resource_type", ["dataset", "folder"])
def test_browse_search_takes_dataset_and_folder_as_resource_types(
    live_cli: LiveCli, scratch_project: int, resource_type: str
) -> None:
    document = json.dumps({"search": "items", "resource_type": resource_type, "limit": 5})

    live_cli.ok("browse", "search", "--input", document, project=scratch_project)


def test_browse_ancestors_of_a_dataset_says_it_needs_a_folder_id(
    live_cli: LiveCli, scratch_project: int, dataset: int
) -> None:
    error = live_cli.err("browse", "ancestors", str(dataset), project=scratch_project)

    assert "FOLDER id" in error["message"]
    assert "parent_resource_id" in error["hint"]


def test_view_delete_succeeds_without_a_read_back_error(
    live_cli: LiveCli, scratch_project: int, dataset: int
) -> None:
    created, _ = live_cli.ok("view", "create", str(dataset), "--yes", project=scratch_project)
    view = int(created["id"])
    parent = json.dumps({"dataset_id": dataset})
    live_cli.ok(
        *("view", "transform", "limit-rows", str(view)),
        *("--input", json.dumps({"n": 1, "dataset_id": dataset}), "--yes"),
        project=scratch_project,
    )

    live_cli.ok(
        *("view", "delete", str(view), "--yes", "--confirm", str(view), "--input", parent),
        project=scratch_project,
    )

    listed, _ = live_cli.ok("view", "list", str(dataset), project=scratch_project)
    assert view not in [row["id"] for row in listed["dataviews"]]
