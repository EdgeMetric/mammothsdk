"""Update method, workbook upload results and file settings against a real DEV instance.

No mocks: each test uploads real files, reads the stored state back through the API and
deletes what it created, even when an assertion fails.

Required env vars: MAMMOTH_BASE_URL, MAMMOTH_API_KEY, MAMMOTH_API_SECRET,
MAMMOTH_WORKSPACE_ID, MAMMOTH_PROJECT_ID.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Any

import pytest
from openpyxl import Workbook

from mammoth import MammothClient
from mammoth.models.datasets import DataAdditionMode

_REQUIRED_ENV = (
    "MAMMOTH_BASE_URL",
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_PROJECT_ID",
)
_missing = [v for v in _REQUIRED_ENV if not os.environ.get(v)]
pytestmark = [
    pytest.mark.skipif(bool(_missing), reason=f"Missing env vars: {', '.join(_missing)}"),
    pytest.mark.asyncio(loop_scope="session"),
]

#: What the backend stores for a dataset with no settings of its own
#: (mvc-service ``SchemaPropertiesDefaultValues``).
_RELEASE_DEFAULTS: dict[str, Any] = {
    "data_addition_mode": "combine",
    "delete_after_append": True,
    "strict_data_type_check": True,
    "convert_columns_to_text": False,
    "strict_column_length_check": False,
    "match_existing_target_schema": True,
    "convert_incompatible_data_to_null": False,
}
_SHEETS = ("Jan", "Feb", "Mar")


@pytest.fixture(scope="module")
def client() -> MammothClient:
    c = MammothClient(
        api_key=os.environ["MAMMOTH_API_KEY"],
        api_secret=os.environ["MAMMOTH_API_SECRET"],
        workspace_id=int(os.environ["MAMMOTH_WORKSPACE_ID"]),
        base_url=os.environ["MAMMOTH_BASE_URL"],
    )
    c.set_project_id(int(os.environ["MAMMOTH_PROJECT_ID"]))
    return c


async def _stored_schema_properties(client: MammothClient, dataset_id: int) -> dict[str, Any]:
    """The dataset's ``configurations.schema_properties``, read with a real GET."""
    response = await client.datasets.get(dataset_id, fields="id,configurations")
    dataset = response.get("dataset", response)
    return (dataset.get("configurations") or {}).get("schema_properties") or {}


def _settings_subset(stored: dict[str, Any]) -> dict[str, Any]:
    return {key: stored[key] for key in _RELEASE_DEFAULTS if key in stored}


async def test_set_update_method_changes_only_the_mode(
    client: MammothClient, tmp_path: Path
) -> None:
    """Replace keeps every other stored setting; an empty dataset gets the release defaults."""
    csv_path = tmp_path / "update_method.csv"
    csv_path.write_text("name,salary\nalice,100\nbob,90\n")
    dataset_id = await client.files.upload(str(csv_path))
    assert isinstance(dataset_id, int)
    try:
        read = await client.datasets.get_update_method(dataset_id)
        before = _settings_subset(await _stored_schema_properties(client, dataset_id))
        assert read == {
            k: v for k, v in read.items() if k in _RELEASE_DEFAULTS | {"schema_mapping"}
        }
        expected = {**_RELEASE_DEFAULTS, **before, "data_addition_mode": "replace"}

        result = await client.datasets.set_update_method(dataset_id, DataAdditionMode.REPLACE)

        assert result["data_addition_mode"] == "replace"
        assert result["dataset_id"] == dataset_id
        after = _settings_subset(await _stored_schema_properties(client, dataset_id))
        assert after == expected
        assert (await client.datasets.get_update_method(dataset_id))["data_addition_mode"] == (
            "replace"
        )

        restored = await client.datasets.set_update_method(dataset_id, DataAdditionMode.COMBINE)
        assert restored["data_addition_mode"] == "combine"
        assert _settings_subset(await _stored_schema_properties(client, dataset_id)) == {
            **expected,
            "data_addition_mode": "combine",
        }
    finally:
        with contextlib.suppress(Exception):
            await client.datasets.delete(dataset_id)


async def test_upload_result_reports_a_workbook_waiting_for_its_sheets(
    client: MammothClient, tmp_path: Path
) -> None:
    """A 3-sheet workbook makes no dataset: it waits for the sheet choice."""
    workbook = Workbook()
    workbook.active.title = _SHEETS[0]
    for title in _SHEETS[1:]:
        workbook.create_sheet(title)
    for sheet in workbook.worksheets:
        sheet.append(["name", "salary"])
        sheet.append(["alice", 100])
    path = tmp_path / "three_sheets_update_method.xlsx"
    workbook.save(path)

    outcome: dict[str, Any] = {}
    try:
        outcome = await client.files.upload_result(str(path))
        assert outcome["dataset_ids"] == []
        assert "files_error" not in outcome
        assert len(outcome["files"]) == 1
        entry = outcome["files"][0]
        assert entry["name"] == path.name
        assert entry["action_needed"] == "sheet_selection_required"
        names = [sheet.get("sheet_name") or sheet.get("name") for sheet in entry["sheets_info"]]
        assert sorted(names) == sorted(_SHEETS)
    finally:
        for entry in outcome.get("files", []):
            with contextlib.suppress(Exception):
                await client.files.delete(entry["file_id"])
        for dataset_id in outcome.get("dataset_ids", []):
            with contextlib.suppress(Exception):
                await client.datasets.delete(dataset_id)


async def test_upload_result_gives_each_same_named_upload_its_own_file_id(
    client: MammothClient, tmp_path: Path
) -> None:
    """The same workbook name uploaded twice within a minute: each reports its own file id."""
    workbook = Workbook()
    workbook.active.title = _SHEETS[0]
    for title in _SHEETS[1:]:
        workbook.create_sheet(title)
    for sheet in workbook.worksheets:
        sheet.append(["name", "salary"])
        sheet.append(["alice", 100])
    path = tmp_path / "same_name_twice_update_method.xlsx"
    workbook.save(path)

    outcomes: list[dict[str, Any]] = []
    try:
        for _ in range(2):
            outcomes.append(await client.files.upload_result(str(path)))
        file_ids = []
        for outcome in outcomes:
            assert "files_error" not in outcome
            assert len(outcome["files"]) == 1
            entry = outcome["files"][0]
            assert entry["name"] == path.name
            assert entry["action_needed"] == "sheet_selection_required"
            # The id the upload job itself named for this upload's file.
            assert [entry["file_id"]] == [
                info["file_object_id"] for info in outcome["nested_job_ids"]
            ]
            file_ids.append(entry["file_id"])
        assert len(set(file_ids)) == 2
    finally:
        for outcome in outcomes:
            for entry in outcome.get("files", []):
                with contextlib.suppress(Exception):
                    await client.files.delete(entry["file_id"])


async def test_file_settings_update_with_one_setting_keeps_the_others(
    client: MammothClient, tmp_path: Path
) -> None:
    """Changing only ``initial_skip_count`` leaves delimiter, header and quote as they were."""
    csv_path = tmp_path / "two_title_lines_update_method.csv"
    csv_path.write_text("Quarterly report\nprepared by finance\nname,salary\nalice,100\nbob,90\n")
    dataset_id = await client.files.upload(str(csv_path))
    assert isinstance(dataset_id, int)
    try:
        before = (await client.datasets.get_file_settings(dataset_id))["info"]
        kept = ("delimiter", "has_header", "quotechar")

        response = await client.datasets.file_settings_update(dataset_id, initial_skip_count=2)
        job_id = response.get("job_id") if isinstance(response, dict) else None
        if job_id:
            await client.jobs.wait_for_job(job_id)

        after = (await client.datasets.get_file_settings(dataset_id))["info"]
        assert after["initial_skip_count"] == 2
        for key in kept:
            assert after[key] == before[key], key
    finally:
        with contextlib.suppress(Exception):
            await client.datasets.delete(dataset_id)
