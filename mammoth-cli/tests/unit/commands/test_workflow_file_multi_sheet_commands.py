"""The workflow save, archive, attach, held-resolve and multi-sheet file commands: argv to request.

Each dry run goes through the real CLI parser and handler and stops before the request leaves.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.testing import login_default_profile, make_runner

_IDS = [
    "workflow.save",
    "workflow.archive",
    "workflow.attach-dataset",
    "workflow.resolve-held",
    "file.multi-sheet-preview",
    "file.multi-sheet-extract",
]


@pytest.mark.parametrize("command_id", _IDS)
def test_the_command_is_registered_and_reachable_from_the_cli(command_id: str) -> None:
    assert command_id in HANDLERS
    record = command_by_id(command_id)
    assert record is not None
    result = make_runner().invoke([*record["command_path"].split(), "--help"])
    assert result.exit_code == 0


def _dry_run(argv: list[str]) -> dict[str, object]:
    result = make_runner().invoke([*argv, "--project", "25654", "--dry-run", "--output", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["dry_run"] is True and data["ran"] is False
    return data["would_call"]


def test_attach_dataset_sends_the_dataset_id_given_as_the_second_positional(
    isolated_cli_config: Path,
) -> None:
    login_default_profile()
    call = _dry_run(["workflow", "attach-dataset", "12", "415"])
    assert call["sdk_symbol"] == "mammoth.api.workflows.WorkflowsAPI.attach_dataset"
    assert call["arguments"] == {"workflow_id": 12, "datasource_id": 415, "project_id": 25654}


def test_resolve_held_takes_the_change_key_as_a_positional_and_built_from_input(
    isolated_cli_config: Path,
) -> None:
    login_default_profile()
    call = _dry_run(
        ["workflow", "resolve-held", "12", "change-1", "--input", json.dumps({"built": True})]
    )
    assert call["arguments"] == {
        "workflow_id": 12,
        "key": "change-1",
        "built": True,
        "project_id": 25654,
    }


def test_archive_sends_the_flag_and_the_dataset_ids_from_input(isolated_cli_config: Path) -> None:
    login_default_profile()
    document = {"archived": True, "dataset_ids": [3, 4]}
    call = _dry_run(["workflow", "archive", "12", "--input", json.dumps(document)])
    assert call["sdk_symbol"] == "mammoth.api.workflows.WorkflowsAPI.set_archived"
    assert call["arguments"] == {
        "workflow_id": 12,
        "archived": True,
        "dataset_ids": [3, 4],
        "project_id": 25654,
    }


def test_multi_sheet_extract_forwards_the_tables_and_leaves_delete_to_the_default(
    isolated_cli_config: Path,
) -> None:
    login_default_profile()
    table = {"sheet_name": "Sales 2", "dataset_name": "Sales 2", "structure_map": {}}
    call = _dry_run(
        ["file", "multi-sheet-extract", "9", "--input", json.dumps({"tables": [table]})]
    )
    assert call["sdk_symbol"] == "mammoth.api.files.FilesAPI.create_datasets_from_multi_sheet"
    assert call["arguments"] == {"file_id": 9, "tables": [table]}
