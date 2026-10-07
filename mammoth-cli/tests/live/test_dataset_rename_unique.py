"""Live: ``dataset rename`` with ``{"unique": true}`` asks the server for a free name.

Two real datasets in a scratch project; the second is renamed to the first's name.
Run on the box with the test identity (see ``conftest.py``)::

    pytest tests/live/test_dataset_rename_unique.py -m live -v
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest
from live_harness import LiveCli, upload_csv

pytestmark = pytest.mark.live

_CSV = "a,b\n1,2\n3,4\n"


@pytest.fixture(scope="module")
def datasets(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> tuple[int, str]:
    """``(other, taken_name)``: a dataset to rename, and a name another dataset already holds."""
    stamp = int(time.time())
    folder = tmp_path_factory.mktemp("rename")
    taken, _ = upload_csv(live_cli, scratch_project, folder / f"taken_{stamp}.csv", _CSV)
    other, _ = upload_csv(live_cli, scratch_project, folder / f"other_{stamp}.csv", _CSV)
    name = f"Renamed {stamp}"
    live_cli.ok(
        *("dataset", "rename", str(taken), "--input", json.dumps({"name": name}), "--yes"),
        project=scratch_project,
    )
    return other, name


def _rename(live_cli: LiveCli, project: int, dataset: int, **document: Any) -> dict[str, Any]:
    return live_cli.run(
        *("dataset", "rename", str(dataset), "--input", json.dumps(document), "--yes"),
        project=project,
    )


def _name_of(live_cli: LiveCli, project: int, dataset: int) -> str:
    listed, _ = live_cli.ok("dataset", "list", project=project)
    return str(next(d["name"] for d in listed["datasets"] if d["id"] == dataset))


def test_unique_true_renames_to_the_free_name_the_server_picks(
    live_cli: LiveCli, scratch_project: int, datasets: tuple[int, str]
) -> None:
    other, taken_name = datasets

    envelope = _rename(live_cli, scratch_project, other, name=taken_name, unique=True)

    assert "error" not in envelope, envelope
    applied = envelope["data"]["name"]
    assert applied != taken_name and applied.startswith(taken_name)
    assert _name_of(live_cli, scratch_project, other) == applied


def test_without_unique_a_taken_name_is_not_applied_as_is(
    live_cli: LiveCli, scratch_project: int, datasets: tuple[int, str]
) -> None:
    other, taken_name = datasets
    before = _name_of(live_cli, scratch_project, other)

    envelope = _rename(live_cli, scratch_project, other, name=taken_name, unique=False)

    assert "error" in envelope, envelope
    assert _name_of(live_cli, scratch_project, other) == before
