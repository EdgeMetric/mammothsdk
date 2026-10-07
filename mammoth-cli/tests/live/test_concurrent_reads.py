"""Live checks: the independent reads behind one listing or data read go out together.

``view list`` read each dataset's views one after another, ``dataset find`` listed
each project in turn, and ``view data get`` named the view, then the dataset, then
read the data: against a real server each round trip was added to the last. The
tests run the real CLI against a real tenant and watch the real requests (the
observer below calls the true ``send`` and only records when each request started
and finished), then assert the independent ones overlapped in time.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_concurrent_reads.py -m live -v
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live

_DATASETS = 4


@contextmanager
def observed_requests() -> Iterator[list[tuple[str, float, float]]]:
    """Record ``(method + path, start, end)`` of every request the SDK sends, unchanged."""
    seen: list[tuple[str, float, float]] = []
    real_send = httpx.AsyncClient.send

    async def send(self: httpx.AsyncClient, request: httpx.Request, **kwargs: Any) -> Any:
        started = time.monotonic()
        try:
            return await real_send(self, request, **kwargs)
        finally:
            seen.append((f"{request.method} {request.url.path}", started, time.monotonic()))

    httpx.AsyncClient.send = send  # type: ignore[method-assign]
    try:
        yield seen
    finally:
        httpx.AsyncClient.send = real_send  # type: ignore[method-assign]


def most_at_once(seen: list[tuple[str, float, float]], wanted: Callable[[str], bool]) -> int:
    """The largest number of matching requests that were in flight at the same moment."""
    spans = [(start, end) for label, start, end in seen if wanted(label)]
    return max(
        (sum(1 for s, e in spans if s <= start < e) for start, _end in spans),
        default=0,
    )


def _upload_datasets(live_cli: LiveCli, project: int, directory: Path, stem: str) -> list[int]:
    ids = []
    for n in range(_DATASETS):
        source = directory / f"{stem}_{n}.csv"
        source.write_text("Region,Units\nNorth,1\nSouth,2\n", encoding="utf-8")
        uploaded, _ = live_cli.ok("file", "upload", str(source), "--yes", project=project)
        ids.append(int(uploaded["dataset_id"]))
    return ids


@pytest.fixture(scope="module")
def stem() -> str:
    return f"w10conc{int(time.time())}"


@pytest.fixture(scope="module")
def uploaded(
    live_cli: LiveCli, scratch_project: int, stem: str, tmp_path_factory: pytest.TempPathFactory
) -> list[int]:
    return _upload_datasets(live_cli, scratch_project, tmp_path_factory.mktemp("conc"), stem)


@pytest.fixture(scope="module")
def second_project(
    live_cli: LiveCli, stem: str, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[int]:
    data, _ = live_cli.ok("project", "create", f"{stem}-second", "--yes")
    project = int(data["id"])
    try:
        _upload_datasets(live_cli, project, tmp_path_factory.mktemp("conc2"), stem)
        yield project
    finally:
        removed = live_cli.run(
            *("project", "delete", str(project), "--yes", "--confirm", str(project)),
            project=None,
        )
        assert "error" not in removed, f"project {project} not deleted: {removed}"


def test_view_list_reads_the_datasets_views_together(
    live_cli: LiveCli, scratch_project: int, uploaded: list[int]
) -> None:
    with observed_requests() as seen:
        data, _ = live_cli.ok("view", "list", project=scratch_project)

    assert data["datasets_visited"] == _DATASETS
    assert {row["dataset_id"] for row in data["dataviews"]} == set(uploaded)
    views_of_a_dataset = re.compile(r"GET .*/datasets/\d+/dataviews$")
    assert most_at_once(seen, lambda label: bool(views_of_a_dataset.match(label))) >= 2


def test_dataset_find_lists_the_projects_together(
    live_cli: LiveCli, scratch_project: int, second_project: int, uploaded: list[int], stem: str
) -> None:
    with observed_requests() as seen:
        data, _ = live_cli.ok("dataset", "find", stem)

    assert {row["project_id"] for row in data["matches"]} == {scratch_project, second_project}
    datasets_of_a_project = re.compile(r"GET .*/projects/\d+/datasets$")
    assert most_at_once(seen, lambda label: bool(datasets_of_a_project.match(label))) >= 2


def test_view_data_get_reads_names_and_data_together(
    live_cli: LiveCli, scratch_project: int, uploaded: list[int]
) -> None:
    listed, _ = live_cli.ok("view", "list", str(uploaded[0]), project=scratch_project)
    view = int(listed["dataviews"][0]["id"])

    with observed_requests() as seen:
        data, meta = live_cli.ok(
            "view", "data", "get", str(view), str(uploaded[0]), project=scratch_project
        )

    assert meta["dataset"]["id"] == uploaded[0]
    assert meta["view"]["id"] == view
    assert [row["Region"] for row in data["data"]] == ["North", "South"]
    names = re.compile(rf"GET .*/datasets/{uploaded[0]}(/dataviews/{view})?$")
    assert most_at_once(seen, lambda label: bool(names.match(label))) >= 2
