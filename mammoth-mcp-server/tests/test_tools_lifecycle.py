"""Make a project, rename what the user named badly, and say what a deleted file leaves behind."""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, a_fake_api, as_caller, run

PROJECT, DATASET, VIEW, FILE = 3, 5, 9, 12
WORKSPACE_PATH = f"/workspaces/{WORKSPACE}"
PROJECT_PATH = f"{WORKSPACE_PATH}/projects/{PROJECT}"
DATASET_PATH = f"{PROJECT_PATH}/datasets/{DATASET}"
VIEW_PATH = f"{DATASET_PATH}/dataviews/{VIEW}"
FILE_PATH = f"{PROJECT_PATH}/files/{FILE}"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
# A file as Mammoth lists it once read (a dev server, 28 Oct 2026), cut to what is read.
READ_FILE = {
    "file": {
        "id": FILE,
        "name": "m12_scratch.csv",
        "status": "processed",
        "additional_info": {"parent_id": f"project_{PROJECT}", "final_ds_id": DATASET},
    }
}


def call(tool: str, **arguments: object) -> Any:
    """Call one tool as a client does. `call_tool` cannot pass an argument named `name`."""
    register_tools()
    result = run(mcp_server.call_tool(tool, dict(arguments)))
    assert result.structured_content is not None
    return dict(result.structured_content)


class TestCreatingAProject:
    def test_the_new_project_is_named_and_linked(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{WORKSPACE_PATH}/projects", {"id": 44, "name": "Q4 sales"})
            made = call("create_project", workspace_id=WORKSPACE, name="Q4 sales")

        (sent,) = api.sent("POST", f"{WORKSPACE_PATH}/projects")
        assert api.body(sent)["name"] == "Q4 sales"
        assert made["project_id"] == 44
        assert made["name"] == "Q4 sales"
        assert made["mammoth_url"].endswith(f"/#/workspaces/{WORKSPACE}/projects/44")

    def test_a_connection_limited_to_some_projects_could_not_reach_a_new_one(self) -> None:
        with (
            a_fake_api() as api,
            as_caller(project_id=PROJECT),
            pytest.raises(ToolError, match="limited to project 3"),
        ):
            call("create_project", workspace_id=WORKSPACE, name="Q4 sales")

        assert not api.sent("POST", f"{WORKSPACE_PATH}/projects")


class TestRenaming:
    def test_a_dataset(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("PATCH", DATASET_PATH, {"id": DATASET, "name": "Orders"})
            renamed = call("rename", what="dataset", dataset_id=DATASET, name="Orders", **IDS)

        (sent,) = api.sent("PATCH", DATASET_PATH)
        assert api.body(sent)["patch"] == {"op": "replace", "path": "name", "value": "Orders"}
        assert renamed == {
            "renamed": "dataset",
            "id": DATASET,
            "name": "Orders",
            "mammoth_url": renamed["mammoth_url"],
        }
        assert renamed["mammoth_url"].endswith(f"/datasets/{DATASET}")

    def test_a_view(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("PATCH", VIEW_PATH, [{"id": VIEW, "name": "Cleaned"}])
            renamed = call(
                "rename", what="view", dataset_id=DATASET, view_id=VIEW, name="Cleaned", **IDS
            )

        (sent,) = api.sent("PATCH", VIEW_PATH)
        assert api.body(sent)["patch"] == [{"op": "replace", "path": "name", "value": "Cleaned"}]
        assert renamed["renamed"] == "view"
        assert renamed["id"] == VIEW
        assert renamed["mammoth_url"].endswith(f"/views/{VIEW}")

    def test_a_project(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("PATCH", PROJECT_PATH, {"id": PROJECT, "name": "Sales"})
            renamed = call("rename", what="project", name="Sales", **IDS)

        (sent,) = api.sent("PATCH", PROJECT_PATH)
        assert api.body(sent)["patches"] == [{"op": "replace", "path": "name", "value": "Sales"}]
        assert renamed["renamed"] == "project"
        assert renamed["id"] == PROJECT

    @pytest.mark.parametrize(
        ("what", "given", "missing"),
        [("dataset", {}, "dataset_id"), ("view", {"dataset_id": DATASET}, "view_id")],
    )
    def test_what_is_renamed_needs_its_ids(
        self, what: str, given: dict[str, int], missing: str
    ) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match=missing):
            call("rename", what=what, name="Orders", **given, **IDS)

        assert not [r for r in api.requests if r.method == "PATCH"]


class TestDeletingAFile:
    def test_the_dataset_made_from_it_stays_and_is_named(self) -> None:
        # Seen live: the file went, its dataset stayed, and the tool said nothing.
        with a_fake_api() as api, as_caller():
            api.answer("GET", FILE_PATH, READ_FILE)
            api.answer("DELETE", FILE_PATH, {"job": {"id": 41}})
            api.answer("GET", "/jobs/41", {"job": {"id": 41, "status": "success", "response": {}}})
            answer = call("delete_file", file_id=FILE, **IDS)

        assert api.sent("DELETE", FILE_PATH)
        assert answer["deleted_file"] == FILE
        assert answer["dataset_kept"] == DATASET
        assert "whole_dataset" in answer["next_step"]
