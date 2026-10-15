"""Workflow duplicate, Save undo and Save step cancel: the wire each SDK call sends.

Runs against a real loopback HTTP server that records every request.
"""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

WF = "/workspaces/1/projects/25654/workflows"


async def test_duplicate_posts_the_name_and_datasets_and_waits_for_the_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {WF}/duplicate"] = (202, {"job_id": 44, "status_code": 202})
    server.answers["GET /jobs/44"] = {
        "id": 44,
        "status": "success",
        "response": {"workflow_id": 901},
    }
    job = await client.workflows.duplicate("Copy of Sales", [3, 4], source_workflow_id=12)
    assert server.requests[0] == {
        "method": "POST",
        "path": f"{WF}/duplicate",
        "query": {},
        "body": {"name": "Copy of Sales", "dataset_ids": [3, 4], "source_workflow_id": 12},
    }
    assert server.requests[1]["path"] == "/jobs/44"
    assert job["response"]["workflow_id"] == 901


async def test_duplicate_without_wait_returns_the_queued_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /workspaces/1/projects/9/workflows/duplicate"] = (202, {"job_id": 44})
    queued = await client.workflows.duplicate("Copy", [3], wait=False, project_id=9)
    assert queued == {"job_id": 44}
    assert len(server.requests) == 1
    assert server.requests[0]["path"] == "/workspaces/1/projects/9/workflows/duplicate"
    assert server.requests[0]["body"] == {"name": "Copy", "dataset_ids": [3]}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "", "dataset_ids": [3]},
        {"name": "x" * 256, "dataset_ids": [3]},
        {"name": "ok", "dataset_ids": []},
        {"name": "ok", "dataset_ids": [3, 0]},
        {"name": "ok", "dataset_ids": [True]},
        {"name": "ok", "dataset_ids": [3], "source_workflow_id": 0},
        {"name": "ok", "dataset_ids": [3], "project_id": -1},
    ],
)
async def test_duplicate_refuses_bad_input_before_any_request(
    server: RecordingServer, client: MammothClient, kwargs: dict[str, object]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.workflows.duplicate(**kwargs)  # type: ignore[arg-type]
    assert server.requests == []


async def test_undo_save_posts_to_the_undo_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {WF}/12/save/run-abc/undo"] = (202, {"id": 12, "name": "Sales"})
    workflow = await client.workflows.undo_save(12, "run-abc")
    assert server.requests[-1] == {
        "method": "POST",
        "path": f"{WF}/12/save/run-abc/undo",
        "query": {},
        "body": None,
    }
    assert workflow["id"] == 12


async def test_cancel_save_step_posts_to_the_step_cancel_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {WF}/12/save/run-abc/steps/2/cancel"] = {"id": 12, "name": "Sales"}
    workflow = await client.workflows.cancel_save_step(12, "run-abc", 2)
    assert server.requests[-1] == {
        "method": "POST",
        "path": f"{WF}/12/save/run-abc/steps/2/cancel",
        "query": {},
        "body": None,
    }
    assert workflow["name"] == "Sales"


async def test_cancel_save_step_accepts_step_zero_and_a_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workflows.cancel_save_step(12, "r1", 0, project_id=7)
    assert (
        server.requests[-1]["path"]
        == "/workspaces/1/projects/7/workflows/12/save/r1/steps/0/cancel"
    )


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("undo_save", (0, "run")),
        ("undo_save", (12, "")),
        ("undo_save", (12, "a/b")),
        ("cancel_save_step", (0, "run", 1)),
        ("cancel_save_step", (12, " ", 1)),
        ("cancel_save_step", (12, "run", -1)),
        ("cancel_save_step", (12, "run", True)),
    ],
)
async def test_save_calls_refuse_bad_input_before_any_request(
    server: RecordingServer,
    client: MammothClient,
    method: str,
    args: tuple[object, ...],  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await getattr(client.workflows, method)(*args)
    assert server.requests == []
