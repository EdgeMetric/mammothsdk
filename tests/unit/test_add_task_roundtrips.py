"""``View._add_task`` reads the pipeline once after the submit, for draft state and the wait.

That one read answers whether the view is in draft (the step is staged) and whether the
pipeline has settled; it is also the first poll of the wait, so a transform that settles at
once costs the submit, one pipeline read and the metadata refresh. A pipeline in
``ref_error`` with auto-run on is a failed step, never a staged draft, even when the server
has marked the draft dirty.
"""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothTransformError
from mammoth.view import View

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

DV = "/workspaces/1/projects/25654/datasets/7/dataviews/9"
META = {
    "id": 9,
    "name": "v",
    "metadata": [{"display_name": "sales", "internal_name": "column_2", "type": "NUMERIC"}],
}


def _view(client: MammothClient) -> View:
    return View(client, META, 7)


def _calls(server: RecordingServer) -> list[str]:
    return [f"{r['method']} {r['path']}" for r in server.requests]


def _script(server: RecordingServer, pipeline: dict[str, object]) -> None:
    server.answers.update(
        {
            f"POST {DV}/pipeline/tasks": {"status": "processing", "task_id": 5},
            f"GET {DV}/pipeline": pipeline,
            f"GET {DV}": META,
        }
    )


async def test_a_settled_pipeline_costs_one_read_after_the_submit(
    server: RecordingServer, client: MammothClient
) -> None:
    _script(server, {"state": "ready", "draft_mode": "off", "auto_run": True})

    result = await _view(client).math("sales * 2", new_column="double")

    assert _calls(server) == [f"POST {DV}/pipeline/tasks", f"GET {DV}/pipeline", f"GET {DV}"]
    assert result["status"] == "done"
    assert result["pipeline_state"] == "ready"


async def test_a_draft_stages_the_step_without_a_wait_or_refresh(
    server: RecordingServer, client: MammothClient
) -> None:
    _script(server, {"state": "ready", "draft_mode": "clean", "auto_run": False})

    result = await _view(client).math("sales * 2", new_column="double")

    assert _calls(server) == [f"POST {DV}/pipeline/tasks", f"GET {DV}/pipeline"]
    assert result["status"] == "staged"
    assert "view draft submit 9" in result["message"]


async def test_a_draft_holding_a_broken_step_still_stages(
    server: RecordingServer, client: MammothClient
) -> None:
    # Auto-run is off, so the user's own draft is what holds the error: nothing ran.
    _script(server, {"state": "ref_error", "draft_mode": "dirty", "auto_run": False})

    result = await _view(client).math("sales * 2", new_column="double")

    assert result["status"] == "staged"


@pytest.mark.parametrize("auto_run", [{"auto_run": True}, {}], ids=["auto-run-on", "no-auto-run"])
async def test_a_reference_error_with_auto_run_on_is_never_reported_as_staged(
    server: RecordingServer, client: MammothClient, auto_run: dict[str, object]
) -> None:
    # The 0.7.12 shape: the server marks the draft dirty when the new step breaks. A
    # pipeline that does not say auto-run is off is read the same way.
    _script(server, {"state": "ref_error", "draft_mode": "dirty", **auto_run})

    with pytest.raises(MammothAPIError) as caught:
        await _view(client).math("sales * 2", new_column="double")

    assert caught.value.phase == "post_submit_readback"
    assert isinstance(caught.value.__cause__, MammothTransformError)
    assert caught.value.details["post_submitted"] is True


async def test_an_unsettled_pipeline_is_waited_on(
    server: RecordingServer, client: MammothClient
) -> None:
    # The wait polls the same route; the stand-in answers ``ready`` from the second read on.
    _script(server, {"state": "running", "draft_mode": "off", "auto_run": True})
    view = _view(client)
    first_read = view._pipeline_status

    async def then_ready() -> dict[str, object] | None:
        status = await first_read()
        server.answers[f"GET {DV}/pipeline"] = {"state": "ready", "auto_run": True}
        return status

    view._pipeline_status = then_ready  # type: ignore[method-assign]

    result = await view.math("sales * 2", new_column="double")

    assert _calls(server) == [
        f"POST {DV}/pipeline/tasks",
        f"GET {DV}/pipeline",
        f"GET {DV}/pipeline",
        f"GET {DV}",
    ]
    assert result["status"] == "done"
