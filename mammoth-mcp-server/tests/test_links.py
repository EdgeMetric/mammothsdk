"""`mammoth_url`: the page in Mammoth where the user opens what a tool read or changed.

A user told about a cleaned view needs a way to open it, and to check a number
against Mammoth rather than take the model's word for it.
"""

from mammoth_mcp_server.consts import MCP_INSTRUCTIONS
from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool, run

PROJECT, DATASET, VIEW = 3, 5, 9
DATASETS = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets"
VIEWS = f"{DATASETS}/{DATASET}/dataviews"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET}
VIEW_PAGE = f"/#/workspaces/{WORKSPACE}/projects/{PROJECT}/views/{VIEW}"
DATASET_PAGE = f"/#/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}"


class TestViews:
    def test_a_view_read_links_to_its_page(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", f"{VIEWS}/{VIEW}", {"id": VIEW, "name": "View 1", "metadata": []})
            view = call_tool("get_view", view_id=VIEW, **IDS)

        assert view["mammoth_url"].endswith(VIEW_PAGE)

    def test_each_view_listed_links_to_its_page(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEWS, {"dataviews": [{"id": VIEW, "name": "View 1"}]})
            listed = call_tool("list_views", **IDS)

        assert listed["dataviews"][0]["mammoth_url"].endswith(VIEW_PAGE)

    def test_a_new_view_links_to_its_page(self) -> None:
        # `name` is the tool's own argument, so it cannot go through call_tool.
        register_tools()
        arguments = {**IDS, "name": "Scratch"}
        with a_fake_api() as api, as_caller():
            api.answer("POST", VIEWS, {"dataview_id": VIEW})
            created = run(mcp_server.call_tool("create_view", arguments)).structured_content

        assert created["mammoth_url"].endswith(VIEW_PAGE)

    def test_the_pipeline_links_to_its_view(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", f"{VIEWS}/{VIEW}/pipeline", {"draft_mode": "none"})
            api.answer("GET", f"{VIEWS}/{VIEW}/pipeline/tasks", {"tasks": []})
            pipeline = call_tool("get_pipeline", view_id=VIEW, **IDS)

        assert pipeline["mammoth_url"].endswith(VIEW_PAGE)


class TestDatasets:
    def test_a_dataset_read_links_to_its_page(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", f"{DATASETS}/{DATASET}", {"dataset": {"id": DATASET, "name": "q1"}})
            read = call_tool("get_dataset", **IDS)

        assert read["dataset"]["mammoth_url"].endswith(DATASET_PAGE)

    def test_each_dataset_listed_links_to_its_page(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", DATASETS, {"datasets": [{"id": DATASET, "name": "q1"}]})
            listed = call_tool("list_datasets", workspace_id=WORKSPACE, project_id=PROJECT)

        assert listed["datasets"][0]["mammoth_url"].endswith(DATASET_PAGE)


def test_the_server_tells_the_client_to_pass_the_links_on() -> None:
    assert "mammoth_url" in MCP_INSTRUCTIONS
    assert "aggregate_data" in MCP_INSTRUCTIONS
