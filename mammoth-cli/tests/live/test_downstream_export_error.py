"""Live: a column change that breaks a saved export on the view says so in its own result.

ISS-225: converting ``customer_id`` to TEXT broke an export that replaces a NUMERIC
destination column (``Column mapping is not valid``, 7003) and the convert-type
answered ``verified: true`` with no warning. Run on the box with the test identity
(see ``conftest.py``)::

    pytest tests/live/test_downstream_export_error.py -m live -v
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


@pytest.fixture
def pipes(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> Pipes:
    """A source view and a destination dataset, both with a NUMERIC ``customer_id``."""
    folder: Path = tmp_path_factory.mktemp("downstream")
    stamp = int(time.time() * 1000)
    source, view = upload_csv(
        live_cli, scratch_project, folder / f"src_{stamp}.csv", "customer_id,amount\n1,5\n2,7\n"
    )
    target, _ = upload_csv(
        live_cli, scratch_project, folder / f"dst_{stamp}.csv", "customer_id,amount\n9,1\n"
    )
    body = {
        "dataset_name": "replace",
        "dataset_id": source,
        "target_ds_id": target,
        "save_as_mode": "REPLACE_IN_DS",
    }
    live_cli.ok(
        *("view", "export", "dataset", str(view), "--input", json.dumps(body)),
        "--yes",
        project=scratch_project,
    )
    return Pipes(scratch_project, source, view, target)


def _convert(live_cli: LiveCli, pipes: Pipes, column: str, to: str) -> dict[str, Any]:
    document = {"conversions": [{"column": column, "to": to}], "dataset_id": pipes.dataset}
    data, _ = live_cli.ok(
        *("view", "transform", "convert-type", str(pipes.view)),
        *("--input", json.dumps(document)),
        project=pipes.project,
    )
    assert isinstance(data, dict)
    return data


def test_a_convert_type_that_breaks_a_saved_export_is_not_reported_clean(
    live_cli: LiveCli, pipes: Pipes
) -> None:
    result = _convert(live_cli, pipes, "customer_id", "TEXT")

    verify = result["verify"]
    assert verify["verified"] is False, result
    assert "customer_id" in verify["reason"]
    assert verify["needs_user"]
    assert verify["outcome"] == "failed"


def test_a_convert_type_on_a_view_with_no_export_stays_verified(
    live_cli: LiveCli, pipes: Pipes, tmp_path: Path
) -> None:
    dataset, view = upload_csv(
        live_cli, pipes.project, tmp_path / f"plain_{int(time.time() * 1000)}.csv", "id,qty\n1,5\n"
    )

    result = _convert(live_cli, Pipes(pipes.project, dataset, view, pipes.target), "qty", "TEXT")

    assert result["verify"]["verified"] is True, result
    assert result["verify"]["outcome"] == "settled"
