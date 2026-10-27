"""``View.math`` resolves ``{name}`` parameters by listing each scope once, fully paged."""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from mammoth.view import View

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

DV = "/workspaces/1/projects/25654/datasets/7/dataviews/9"
PARAMS = "/workspaces/1/parameters"
META = {
    "id": 9,
    "name": "v",
    "metadata": [{"display_name": "sales", "internal_name": "column_2", "type": "NUMERIC"}],
}


def _view(client: MammothClient) -> View:
    return View(client, META, 7)


def _listing(*names: str, total: int | None = None) -> dict[str, object]:
    items = [{"id": 100 + i, "name": name} for i, name in enumerate(names)]
    return {"items": items, "total_count": total or len(items), "limit": 100, "offset": 0}


def _script_task(server: RecordingServer) -> None:
    server.answers.update(
        {
            f"POST {DV}/pipeline/tasks": {"status": "processing", "task_id": 5},
            f"GET {DV}/pipeline": {"state": "ready", "draft_mode": "off", "auto_run": True},
            f"GET {DV}": META,
        }
    )


def _parameter_reads(server: RecordingServer) -> list[dict[str, object]]:
    return [r for r in server.requests if r["path"] == PARAMS]


async def test_an_unknown_parameter_raises_and_submits_no_task(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {PARAMS}"] = _listing("other")

    with pytest.raises(MammothValidationError, match="no parameter named 'rate'"):
        await _view(client).math("sales * {rate}", new_column="x")

    assert not [r for r in server.requests if r["method"] == "POST"]


async def test_each_scope_is_listed_once_without_a_name_search(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _script_task(server)
    server.answers[f"GET {PARAMS}"] = _listing("rate", "tax")

    await _view(client).math("sales * {rate} + {tax}", new_column="x")

    reads = _parameter_reads(server)
    assert [r["query"].get("project_id") for r in reads] == [None, "25654"]  # type: ignore[union-attr]
    assert all("search" not in r["query"] for r in reads)  # type: ignore[operator]


async def test_a_scope_longer_than_a_page_is_read_to_its_end(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _script_task(server)
    full_page = ["rate"] + [f"p{i}" for i in range(99)]
    server.answers[f"GET {PARAMS}"] = _listing(*full_page, total=150)

    await _view(client).math("sales * {rate}", new_column="x")

    offsets = [r["query"]["offset"] for r in _parameter_reads(server)]  # type: ignore[index]
    assert offsets[:2] == ["0", "100"]
