"""Live: a folder has ONE id in CLI output, the one the web app opens it by (QA RS-12).

The agent made a folder and listed it under its label id (510) while the app opens it
by its resource id (15089): two cards for one folder, one link broken. The CLI now shows
and accepts only the resource id. ``browse ancestors`` looks a folder up by resource id
on the server, so it is the independent oracle that the id the CLI printed is the real one.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_folder_open_id.py -m live -v
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _eventually(check: Callable[[], object]) -> bool:
    """Moves and deletes run as jobs: true once ``check`` holds, within a minute."""
    for _ in range(12):
        if check():
            return True
        time.sleep(5)
    return False


def _only(rows: list[dict[str, object]], name: str) -> dict[str, object]:
    (row,) = [r for r in rows if r["name"] == name]
    return row


def test_created_folder_id_is_the_id_the_app_opens_and_works_in_every_folder_command(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    project = sales_data.project
    created, _ = live_cli.ok("folder", "create", "RS-12 folder", project=project)
    folder = int(created["id"])

    # The server finds the folder by this number as a resource id.
    path, _ = live_cli.ok("browse", "ancestors", str(folder), project=project)
    assert [row["id"] for row in path["resources"]] == [folder]
    # One id: no second folder id beside it.
    assert "resource_id" not in created

    listed, _ = live_cli.ok("folder", "list", project=project)
    assert _only(listed["folders"], "RS-12 folder")["id"] == folder
    found, _ = live_cli.ok("folder", "find", "RS-12 folder", project=project)
    assert [m["id"] for m in found["matches"]] == [folder]
    tree, _ = live_cli.ok("browse", "project", project=project)
    assert _only(tree["resources"], "RS-12 folder")["id"] == folder
    rows, _ = live_cli.ok("browse", "resources", project=project)
    assert _only(rows["resources"], "RS-12 folder")["id"] == folder

    got, _ = live_cli.ok("folder", "get", str(folder), project=project)
    assert got["id"] == folder
    renamed, _ = live_cli.ok(
        *("folder", "update", str(folder)),
        *("--input", json.dumps({"name": "RS-12 renamed"})),
        project=project,
    )
    assert renamed["id"] == folder and renamed["name"] == "RS-12 renamed"

    live_cli.ok(
        *("folder", "move", "--input"),
        json.dumps({"dataset_ids": [sales_data.dataset], "target_folder_resource_id": folder}),
        project=project,
    )
    assert _eventually(
        lambda: live_cli.ok("browse", "folder", str(folder), project=project)[0]["resources"]
    )

    live_cli.ok("folder", "trash", str(folder), project=project)


def test_deleting_a_folder_by_its_id_removes_that_folder(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    project = sales_data.project
    created, _ = live_cli.ok("folder", "create", "RS-12 delete", project=project)
    folder = int(created["id"])

    live_cli.ok("folder", "delete", str(folder), "--yes", project=project)

    assert _eventually(
        lambda: live_cli.run("folder", "get", str(folder), project=project)
        .get("error", {})
        .get("code")
        == "resource_not_found"
    )
