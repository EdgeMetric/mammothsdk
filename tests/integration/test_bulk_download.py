"""Bulk download against a real server: plan a download of a dataset, then download it.

Needs the ``MM_REL_*`` credentials of ``conftest.py`` and a server that has mvc-service's
downloads routes (#7203).

    pytest tests/integration/test_bulk_download.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth import MammothClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _resource_id(client: MammothClient, dataset_id: int) -> int:
    """The dataset's resource id, which the downloads routes take (not its dataset id)."""
    got = await client.datasets.get(dataset_id, fields="id,name")
    name = got.get("dataset", got)["name"]
    page = await client.browse.resources_list(search=name, limit=100)
    return next(
        row["resource_id"]
        for row in page["resources"]
        if row["id"] == dataset_id and row["name"] == name
    )


async def test_plan_counts_the_selected_dataset(
    client: MammothClient, uploaded_dataset_id: int
) -> None:
    """One dataset plans as one dataset in one file, with nothing skipped."""
    resource = await _resource_id(client, uploaded_dataset_id)

    plan = await client.exports.bulk_download_plan([resource])

    assert plan == {"datasets": 1, "stacked_files": 1, "skipped": 0}


async def test_download_writes_the_datasets_rows_to_a_csv_file(
    client: MammothClient, uploaded_dataset_id: int, tmp_path: Path
) -> None:
    """The file holds the uploaded dataset: a header and more than one line."""
    resource = await _resource_id(client, uploaded_dataset_id)
    target = tmp_path / "employees.csv"

    written = await client.exports.bulk_download([resource], "employees", output_path=target)

    assert written == target
    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 1 and "," in lines[0]
