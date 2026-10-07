"""Live: ``view pipeline rerun --dry-run`` names the exports it fires and the columns they blank.

A real source view with an end-of-pipeline export that appends into a real destination
dataset. Run on the box with the test identity (see ``conftest.py``)::

    pytest tests/live/test_rerun_dry_run_exports.py -m live -v
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli, upload_csv

pytestmark = pytest.mark.live


@dataclass(frozen=True)
class Pipes:
    project: int
    dataset: int
    view: int
    target: int
    folder: Path


def _export_into(live_cli: LiveCli, pipes: Pipes, target: int, **document: Any) -> int:
    """Create the append-into-``target`` export on the source view; return its id."""
    body = {
        "dataset_name": "append",
        "dataset_id": pipes.dataset,
        "target_ds_id": target,
        "save_as_mode": "APPEND_TO_DS",
    }
    live_cli.ok(
        *("view", "export", "dataset", str(pipes.view), "--input", json.dumps(body | document)),
        "--yes",
        project=pipes.project,
    )
    listed, _ = live_cli.ok(
        *("view", "export", "list", str(pipes.view), str(pipes.dataset)), project=pipes.project
    )
    return max(int(e["id"]) for e in listed["exports"])


def _dry_run(live_cli: LiveCli, pipes: Pipes) -> list[dict[str, Any]]:
    envelope = live_cli.run(
        *("view", "pipeline", "rerun", str(pipes.view), "--dry-run"),
        *("--input", json.dumps({"dataset_id": pipes.dataset})),
        project=pipes.project,
    )
    assert "error" not in envelope, envelope
    fired: list[dict[str, Any]] = envelope["data"]["exports_fired"]
    return fired


@pytest.fixture
def pipes(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> Pipes:
    """A fresh source view (``Donor``, ``Gift``) and a destination with an extra ``Notes``."""
    folder = tmp_path_factory.mktemp("rerun")
    stamp = int(time.time() * 1000)
    source, view = upload_csv(
        live_cli, scratch_project, folder / f"src_{stamp}.csv", "Donor,Gift\nann,5\nbob,7\n"
    )
    target, _ = upload_csv(
        live_cli, scratch_project, folder / f"dst_{stamp}.csv", "Donor,Gift,Notes\nzed,1,x\n"
    )
    return Pipes(scratch_project, source, view, target, folder)


def test_dry_run_names_the_destination_columns_an_append_leaves_blank(
    live_cli: LiveCli, pipes: Pipes
) -> None:
    export = _export_into(live_cli, pipes, pipes.target, blank_columns=["Notes"])

    (fired,) = _dry_run(live_cli, pipes)

    assert fired.get("export_id") == export
    assert fired["handler_type"] == "internal_dataset"
    assert fired.get("blank_columns") == ["Notes"]
    assert fired["target"]["TARGET_DS_ID"] == pipes.target
    assert fired["target"]["SAVE_AS_DS_MODE"] == "APPEND_TO_DS"


def test_an_append_that_fills_every_destination_column_reports_none_blank(
    live_cli: LiveCli, pipes: Pipes
) -> None:
    same, _ = upload_csv(
        live_cli,
        pipes.project,
        pipes.folder / f"same_{int(time.time() * 1000)}.csv",
        "Donor,Gift\nz,1\n",
    )
    _export_into(live_cli, pipes, same)

    (fired,) = _dry_run(live_cli, pipes)

    assert fired.get("blank_columns") == []
