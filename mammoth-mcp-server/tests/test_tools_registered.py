"""Which tools a client is offered."""

from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool, run

TOOLS = {
    "add_export",
    "add_transformations",
    "check_upload",
    "create_automation",
    "create_dashboard",
    "create_view",
    "delete_automation",
    "delete_dashboard",
    "delete_export",
    "delete_file",
    "delete_transformation_step",
    "delete_views",
    "extract_sheets",
    "generate_dashboard",
    "get_automation",
    "get_automation_schema",
    "get_dashboard",
    "get_data",
    "get_dataset",
    "get_export",
    "get_export_schema",
    "get_file",
    "get_help",
    "get_pipeline",
    "get_transformation_schema",
    "get_view",
    "interpret_file",
    "list_automations",
    "list_dashboard_tags",
    "list_dashboards",
    "list_datasets",
    "list_exports",
    "list_files",
    "list_projects",
    "list_views",
    "list_workspaces",
    "manage_draft",
    "preview_transformation",
    "publish_dashboard",
    "request_upload",
    "review_unreadable_rows",
    "run_pipeline",
    "set_dashboard_tags",
    "set_date_format",
    "unlock_file",
    "update_automation",
    "upload_file",
}


def test_the_server_offers_exactly_these_tools() -> None:
    # A tool dropped by a bad import would otherwise go unnoticed: the server
    # still starts, with one tool fewer.
    register_tools()

    assert {tool.name for tool in run(mcp_server.list_tools())} == TOOLS


def test_a_tool_reaches_the_api_as_the_caller_before_a_workspace_is_known() -> None:
    with a_fake_api() as api, as_caller():
        api.answer("GET", "/workspaces", {"workspaces": [{"id": WORKSPACE, "name": "Home"}]})
        listed = call_tool("list_workspaces")

    [request] = api.sent("GET", "/workspaces")
    assert listed["workspaces"] == [{"id": WORKSPACE, "name": "Home"}]
    assert request.headers["authorization"].startswith("Bearer mm_")
