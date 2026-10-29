"""From URL against a real server: preview a link, then follow it, copy it and list it.

Needs the ``MM_REL_*`` credentials of ``conftest.py`` and a server that has mvc-service's From
URL routes (#7166, #7169). ``MAMMOTH_LINK_CSV_URL`` names a public CSV the server can reach.

    pytest tests/integration/test_from_url.py -v
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from mammoth import MammothClient

pytestmark = pytest.mark.asyncio(loop_scope="session")

CSV_URL = os.environ.get(
    "MAMMOTH_LINK_CSV_URL",
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
)


async def _linked_ids(client: MammothClient) -> list[int]:
    listed = await client.datasets.links()
    return [row["id"] for row in listed["datasets"] if row["url"] == CSV_URL]


async def test_link_preview_reads_the_file_without_keeping_it(client: MammothClient) -> None:
    """The preview names the file's columns and first rows, and no dataset appears."""
    before = await client.datasets.list_all()
    preview = await client.connector_drafts.link_preview(CSV_URL)
    after = await client.datasets.list_all()

    table = preview["tables"][0]
    assert len(table["columns"]) > 1
    assert table["sample_rows"] and table["row_count"] >= len(table["sample_rows"])
    assert [d["id"] for d in after["datasets"]] == [d["id"] for d in before["datasets"]]


@pytest_asyncio.fixture(loop_scope="session")
async def linked_dataset_id(client: MammothClient) -> AsyncIterator[int]:
    """A dataset made from ``CSV_URL``, deleted afterwards."""
    created = await client.datasets.create({"url": CSV_URL}, "weburl")
    await client.jobs.wait_for_job(created["job_id"])
    ids = await _linked_ids(client)
    assert ids, "the new dataset is not listed among the project's links"
    yield ids[-1]
    with contextlib.suppress(Exception):
        await client.datasets.delete(ids[-1])


async def test_a_copy_leaves_the_links_list_and_following_again_returns_it(
    client: MammothClient, linked_dataset_id: int
) -> None:
    """follow_link(False) drops the dataset from ``links``; follow_link(True) puts it back."""
    assert linked_dataset_id in await _linked_ids(client)

    assert await client.datasets.follow_link(linked_dataset_id, False) == {"follow_link": False}
    assert linked_dataset_id not in await _linked_ids(client)

    assert await client.datasets.follow_link(linked_dataset_id, True) == {"follow_link": True}
    assert linked_dataset_id in await _linked_ids(client)
