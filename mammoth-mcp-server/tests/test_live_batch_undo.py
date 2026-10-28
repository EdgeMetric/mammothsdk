"""The record-then-undo round trip of append batches, against a real Mammoth and a real Redis.

No doubles: each test makes real datasets through the SDK, appends through the server's own
`append_file`, removes through its own `remove_batches`, and deletes what it made, even when an
assertion fails. Run it with `pytest -m live`; it skips itself when the environment is not set.

Required env vars: MCP_LIVE_API_TOKEN (an `mm_` bearer), MCP_LIVE_API_URL,
MCP_LIVE_WORKSPACE_ID, MCP_LIVE_PROJECT_ID, MCP_LIVE_REDIS_URL. `MCP_ENCRYPTION_KEY` is not
needed: a batch's mode is stored in the clear, only credentials are sealed.
"""

import asyncio
import contextlib
import os
import time
from collections.abc import AsyncIterator, Sequence
from pathlib import Path

import pytest
import redis.asyncio as aioredis
from mammoth import MammothClient
from mammoth.appends import NO_RECORD, NOT_ADDED, SETTLED_STATUSES, WOULD_EMPTY, status_of
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server import store
from mammoth_mcp_server.appends import append_file, forget_batch_modes, recall_batch_modes
from mammoth_mcp_server.jobs import job_id_of
from mammoth_mcp_server.sdk import JsonValue, set_api_url
from mammoth_mcp_server.tools.undo import remove_batches

from .helpers import API_URL, as_caller

_REQUIRED_ENV = (
    "MCP_LIVE_API_TOKEN",
    "MCP_LIVE_API_URL",
    "MCP_LIVE_WORKSPACE_ID",
    "MCP_LIVE_PROJECT_ID",
    "MCP_LIVE_REDIS_URL",
)
_missing = [name for name in _REQUIRED_ENV if not os.environ.get(name)]
if _missing:
    pytest.skip(f"Missing env vars: {', '.join(_missing)}", allow_module_level=True)

pytestmark = pytest.mark.live

_SETTLE_SECONDS = 180
_POLL_SECONDS = 2


def _csv(rows: int, prefix: str) -> bytes:
    """A `name,salary` CSV of `rows` rows."""
    body = "".join(f"{prefix}{i},{100 + i}\n" for i in range(rows))
    return f"name,salary\n{body}".encode()


class Env:
    """The live pieces one test works with, and what it made, for cleanup."""

    def __init__(self, client: MammothClient, workspace_id: int, project_id: int, tmp: Path):
        self.client = client
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.tmp = tmp
        self.datasets: list[int] = []
        self.batches: list[tuple[int, int]] = []

    async def make_dataset(self, name: str, rows: int) -> int:
        """Upload a small CSV as a new dataset, wait for it to settle, and return its id."""
        path = self.tmp / name
        path.write_bytes(_csv(rows, "base"))
        outcome = await self.client.files.upload_result(str(path))
        assert outcome["dataset_ids"], outcome
        dataset_id = int(outcome["dataset_ids"][0])
        self.datasets.append(dataset_id)
        await self.settle(dataset_id)
        return dataset_id

    async def settle(self, dataset_id: int) -> None:
        """Wait until the dataset's status says it holds its rows."""
        deadline = time.monotonic() + _SETTLE_SECONDS
        status = None
        while time.monotonic() < deadline:
            status = status_of(await self.client.datasets.get(dataset_id, fields="__standard"))
            if status in SETTLED_STATUSES:
                return
            await asyncio.sleep(_POLL_SECONDS)
        raise AssertionError(f"dataset {dataset_id} did not settle, last status {status!r}")

    async def batch_ids(self, dataset_id: int) -> list[int]:
        """The ids of the dataset's batches, as they are listed now."""
        return [int(row["id"]) for row in await self.client.appends.list_batches(dataset_id)]

    async def append(self, dataset_id: int, mode: str, rows: int) -> list[int]:
        """Append `rows` rows through the server's `append_file` and return the batch ids."""
        report = await append_file(
            self.workspace_id,
            self.project_id,
            dataset_id,
            f"more_{mode}.csv",
            _csv(rows, "extra"),
            "add" if mode == "add" else "replace",
        )
        ids = report["batch_ids"]
        assert isinstance(ids, list) and ids, report
        batches = [batch for batch in ids if isinstance(batch, int)]
        assert len(batches) == len(ids), report
        self.batches.extend((dataset_id, batch) for batch in batches)
        return batches

    async def remove(self, dataset_id: int, batch_ids: Sequence[int]) -> dict[str, JsonValue]:
        """Run the server's `remove_batches` as the live caller."""
        return await remove_batches(self.workspace_id, self.project_id, dataset_id, list(batch_ids))


@pytest.fixture
async def live(tmp_path: Path) -> AsyncIterator[Env]:
    """A real SDK client, the server pointed at the live API and Redis, and cleanup."""
    workspace_id = int(os.environ["MCP_LIVE_WORKSPACE_ID"])
    project_id = int(os.environ["MCP_LIVE_PROJECT_ID"])
    client = MammothClient(
        api_token=os.environ["MCP_LIVE_API_TOKEN"], base_url=os.environ["MCP_LIVE_API_URL"]
    )
    client.set_workspace_id(workspace_id)
    client.set_project_id(project_id)
    redis_client = aioredis.from_url(os.environ["MCP_LIVE_REDIS_URL"], decode_responses=True)
    store.use(redis_client)
    set_api_url(os.environ["MCP_LIVE_API_URL"])
    env = Env(client, workspace_id, project_id, tmp_path)
    try:
        with as_caller(
            token=os.environ["MCP_LIVE_API_TOKEN"],
            workspace_id=workspace_id,
            project_id=project_id,
        ):
            yield env
    finally:
        for dataset_id, batch_id in env.batches:
            with contextlib.suppress(Exception):
                await forget_batch_modes(workspace_id, dataset_id, [batch_id])
        for dataset_id in env.datasets:
            with contextlib.suppress(Exception):
                await client.datasets.delete(dataset_id)
        store.use(None)
        set_api_url(API_URL)
        with contextlib.suppress(Exception):
            await redis_client.aclose()
        with contextlib.suppress(Exception):
            await client.close()


async def test_an_add_batch_is_recorded_and_removable(live: Env) -> None:
    """An add batch is recorded as "add"; undo removes it, drops 3 rows and its records."""
    dataset_id = await live.make_dataset("undo_add_base.csv", rows=2)

    batches = await live.append(dataset_id, "add", rows=3)

    recorded = await recall_batch_modes(live.workspace_id, dataset_id, batches)
    assert recorded == {batch: "add" for batch in batches}
    result = await live.remove(dataset_id, batches)
    assert result["removed"] == batches
    rows_before = result["rows_before"]
    assert isinstance(rows_before, int)
    assert result["rows_after"] == rows_before - 3
    after = await recall_batch_modes(live.workspace_id, dataset_id, batches)
    assert after == {batch: None for batch in batches}


async def test_a_replace_batch_is_refused(live: Env) -> None:
    """A batch made under "replace" is recorded as such and undo will not remove it."""
    dataset_id = await live.make_dataset("undo_replace_base.csv", rows=2)

    batches = await live.append(dataset_id, "replace", rows=1)

    recorded = await recall_batch_modes(live.workspace_id, dataset_id, batches)
    assert recorded == {batch: "replace" for batch in batches}
    with pytest.raises(ToolError) as refused:
        await live.remove(dataset_id, batches[:1])
    assert str(refused.value) == NOT_ADDED.format(batches[0], "replace")


async def test_the_only_batch_is_refused(live: Env) -> None:
    """Removing the add batch once the original is gone would empty the dataset."""
    dataset_id = await live.make_dataset("undo_only_base.csv", rows=2)
    original = await live.batch_ids(dataset_id)
    assert len(original) == 1
    batches = await live.append(dataset_id, "add", rows=2)

    started = await live.client.batches.bulk_delete(dataset_id, original)
    job_id = job_id_of(started)
    if job_id is not None:
        await live.client.jobs.wait_for_job(job_id)
    assert set(await live.batch_ids(dataset_id)) == set(batches)

    with pytest.raises(ToolError) as refused:
        await live.remove(dataset_id, batches)
    assert str(refused.value) == WOULD_EMPTY.format(sorted(set(batches)))


async def test_an_unrecorded_batch_is_refused(live: Env) -> None:
    """A batch this server never recorded is left alone."""
    dataset_id = await live.make_dataset("undo_unrecorded_base.csv", rows=2)
    original = await live.batch_ids(dataset_id)
    assert len(original) == 1

    with pytest.raises(ToolError) as refused:
        await live.remove(dataset_id, original)
    assert str(refused.value) == NO_RECORD.format(original[0])
