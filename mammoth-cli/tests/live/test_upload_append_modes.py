"""Live: ``file upload`` into an existing dataset, its update method, its batches and its undo.

Every case runs the real CLI against a real backend in a scratch project the module
owns; the datasets are deleted after each case and the project at the end.

    MAMMOTH_EVAL_TOKEN_FILE=$HOME/evalrun/.apitests_token MAMMOTH_SERVER_PREFIX=koyal \\
        pytest tests/live/test_upload_append_modes.py -m live -v
"""

from __future__ import annotations

import json
import shlex
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from live_harness import LiveCli, upload_csv

pytestmark = pytest.mark.live

_SET_SYMBOL = "mammoth.api.datasets.DatasetsAPI.set_update_method"
_HEADER = "id,name\n"


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def _mode_of(cli: LiveCli, project: int, dataset: int) -> str:
    data, _ = cli.ok("dataset", "update-method", "get", str(dataset), project=project)
    return str(data["mode"])


def _set_mode(cli: LiveCli, project: int, dataset: int, mode: str) -> None:
    cli.ok(
        *("dataset", "update-method", "set", str(dataset)),
        *_input({"mode": mode}),
        "--yes",
        project=project,
    )


def _batch_ids(cli: LiveCli, project: int, dataset: int) -> list[int]:
    data, _ = cli.ok("batch", "list", str(dataset), project=project)
    return [int(row["id"]) for row in data["batches"]]


def _newest_upload_entry(cli: LiveCli) -> dict[str, Any]:
    """The journal's newest ``file upload`` entry (the listing is newest first)."""
    data, _ = cli.ok("history", "list", *_input({"limit": 50}))
    return next(e for e in data["entries"] if e["command"] == "file upload")


def _csv(tmp_path: Path, name: str, rows: int = 3) -> Path:
    path = tmp_path / name
    path.write_text(_HEADER + "".join(f"{n},row{n}\n" for n in range(rows)), encoding="utf-8")
    return path


@pytest.fixture
def dataset(live_cli: LiveCli, scratch_project: int, tmp_path: Path) -> Iterator[int]:
    """A dataset made from a small CSV; deleted after the test."""
    made, _view = upload_csv(
        live_cli, scratch_project, tmp_path / f"base_{time.time_ns()}.csv", _HEADER + "0,a\n1,b\n"
    )
    try:
        yield made
    finally:
        removed = live_cli.run(
            *("dataset", "delete", str(made), "--yes", "--confirm", str(made)),
            project=scratch_project,
        )
        assert "error" not in removed, f"dataset {made} not deleted: {removed}"


def test_an_append_with_no_mode_into_a_replace_dataset_has_no_undo(
    live_cli: LiveCli, scratch_project: int, dataset: int, tmp_path: Path
) -> None:
    _set_mode(live_cli, scratch_project, dataset, "replace")
    source = _csv(tmp_path, f"plain_{time.time_ns()}.csv")
    data, _ = live_cli.ok(
        *("file", "upload", str(source), "--yes"),
        *_input({"append_to_ds_id": dataset}),
        project=scratch_project,
    )
    assert data["update_method"]["mode"] == "replace"
    entry = _newest_upload_entry(live_cli)
    assert entry["undo"] == []
    assert not entry["undoable"]


def test_an_add_mode_append_reports_its_batch_and_the_undo_deletes_only_it(
    live_cli: LiveCli, scratch_project: int, dataset: int, tmp_path: Path
) -> None:
    _set_mode(live_cli, scratch_project, dataset, "add")
    before = _batch_ids(live_cli, scratch_project, dataset)
    source = _csv(tmp_path, f"added_{time.time_ns()}.csv")
    data, _ = live_cli.ok(
        *("file", "upload", str(source), "--yes"),
        *_input({"append_to_ds_id": dataset}),
        project=scratch_project,
    )
    assert data["update_method"]["mode"] == "add"
    after = _batch_ids(live_cli, scratch_project, dataset)
    added = sorted(set(after) - set(before))
    assert added, "the append added no batch"
    assert sorted(data["batch_ids"]) == added
    assert "unmatched_batch_ids" not in data
    undo = _newest_upload_entry(live_cli)["undo"]
    assert [(line["cmd"], line["args"]) for line in undo] == [
        ("batch delete", [dataset, batch]) for batch in sorted(added, reverse=True)
    ]


def test_mode_replace_sets_the_dataset_mode(
    live_cli: LiveCli, scratch_project: int, dataset: int, tmp_path: Path
) -> None:
    assert _mode_of(live_cli, scratch_project, dataset) == "add"
    source = _csv(tmp_path, f"replacing_{time.time_ns()}.csv")
    data, _ = live_cli.ok(
        *("file", "upload", str(source), "--yes"),
        *_input({"append_to_ds_id": dataset, "mode": "replace"}),
        project=scratch_project,
    )
    assert data["update_method"]["mode"] == "replace"
    assert data["update_method"]["previous_mode"] == "add"
    assert _mode_of(live_cli, scratch_project, dataset) == "replace"


def test_a_dry_run_with_a_mode_reports_both_calls_and_changes_nothing(
    live_cli: LiveCli, scratch_project: int, dataset: int, tmp_path: Path
) -> None:
    source = _csv(tmp_path, f"dry_{time.time_ns()}.csv")
    data, _ = live_cli.ok(
        *("file", "upload", str(source), "--yes", "--dry-run"),
        *_input({"append_to_ds_id": dataset, "mode": "replace"}),
        project=scratch_project,
    )
    assert data["dry_run"] is True
    assert [call["sdk_symbol"] for call in data["earlier_calls"]] == [_SET_SYMBOL]
    assert data["would_call"]["sdk_symbol"].endswith("upload_result")
    assert _mode_of(live_cli, scratch_project, dataset) == "add"


def test_a_three_sheet_workbook_needs_a_choice_and_the_next_command_makes_a_dataset(
    live_cli: LiveCli, scratch_project: int, tmp_path: Path
) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.Workbook()
    book.active.title = "Q1"
    for title in ("Q2", "Q3"):
        book.create_sheet(title)
    for sheet in book.worksheets:
        sheet.append(["id", "name"])
        sheet.append([1, f"{sheet.title}-row"])
    workbook = tmp_path / f"quarters_{time.time_ns()}.xlsx"
    book.save(workbook)

    def dataset_ids() -> set[int]:
        listed, _ = live_cli.ok("dataset", "list", project=scratch_project)
        return {int(row["id"]) for row in listed["datasets"]}

    existing = dataset_ids()
    data, _ = live_cli.ok("file", "upload", str(workbook), "--yes", project=scratch_project)
    assert data["status"] == "needs_sheet_choice"
    assert data["files"][0]["sheets_info"] == ["Q1", "Q2", "Q3"]

    argv = shlex.split(data["next_command"])
    assert argv[:3] == ["mammoth", "file", "extract-sheets"]
    live_cli.ok(*argv[1:], "--yes", project=scratch_project)

    made: set[int] = set()
    for _ in range(24):
        made = dataset_ids() - existing
        if made:
            break
        time.sleep(5)
    assert made, "extracting the chosen sheet made no dataset"
    for dataset_id in made:  # cleanup
        removed = live_cli.run(
            *("dataset", "delete", str(dataset_id), "--yes", "--confirm", str(dataset_id)),
            project=scratch_project,
        )
        assert "error" not in removed, f"dataset {dataset_id} not deleted: {removed}"
