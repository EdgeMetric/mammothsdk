"""`create_view` answers with the new view, not the run that built it."""

from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, a_fake_api, as_caller, run

PROJECT, DATASET, VIEW = 3, 5, 8644
VIEWS = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews"
# What Mammoth answered for a copy of a view with one step (a dev server, 28 Oct 2026).
COPIED = {
    "taskwise_execution_result": {
        "2797": {"status": "DONE", "task_id": 2797, "error_details": None, "params": {}}
    },
    "has_error": False,
    "tables_to_be_dropped": [],
    "dataview_id": VIEW,
    "context": {
        "context_type": "run_pending_updates",
        "ram_size": 15.25,
        "cpu_count": 2,
        "instance_type": "r6a.large",
    },
}


def create(answer: dict) -> dict:
    # `name` is the tool's own argument, so it cannot go through call_tool.
    register_tools()
    arguments = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET}
    with a_fake_api() as api, as_caller():
        api.answer("POST", VIEWS, answer)
        result = run(
            mcp_server.call_tool("create_view", {**arguments, "name": "Scratch"})
        ).structured_content
    return dict(result)


def test_a_copy_answers_with_the_new_view_alone() -> None:
    created = create(COPIED)

    assert set(created) == {"dataview_id", "mammoth_url"}
    assert created["dataview_id"] == VIEW


def test_a_copy_whose_steps_failed_says_so() -> None:
    created = create({**COPIED, "has_error": True})

    assert created["dataview_id"] == VIEW
    assert "get_pipeline" in created["next_step"]
