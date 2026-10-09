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


def test_a_tool_that_builds_a_client_without_a_workspace_still_acts_as_the_caller() -> None:
    # `list_workspaces` is the one tool that builds its client with no workspace,
    # because its route is absolute. The caller's token still has to ride on it.
    with a_fake_api() as api, as_caller():
        api.answer("GET", f"/workspaces/{WORKSPACE}", {"id": WORKSPACE, "name": "Home"})
        listed = call_tool("list_workspaces")

    [request] = api.sent("GET", f"/workspaces/{WORKSPACE}")
    assert listed["workspaces"] == [{"id": WORKSPACE, "name": "Home"}]
    assert request.headers["authorization"].startswith("Bearer mm_")


READ_ONLY = {
    "check_upload",
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
    "list_automations",
    "list_dashboard_tags",
    "list_dashboards",
    "list_datasets",
    "list_exports",
    "list_files",
    "list_projects",
    "list_views",
    "list_workspaces",
    "preview_transformation",
}
# Deletes, sends rows out, publishes, sets something to run, or throws data away.
DESTRUCTIVE = {
    "add_export",
    "create_automation",
    "delete_automation",
    "delete_dashboard",
    "delete_export",
    "delete_file",
    "delete_transformation_step",
    "delete_views",
    "manage_draft",
    "publish_dashboard",
    "review_unreadable_rows",
    "run_pipeline",
    "update_automation",
}


def offered() -> dict[str, object]:
    register_tools()
    return {tool.name: tool for tool in run(mcp_server.list_tools())}


def test_every_tool_says_whether_it_changes_anything() -> None:
    # A client treats a tool with no annotations as one that may do anything.
    for name, tool in offered().items():
        annotations = tool.annotations  # type: ignore[attr-defined]
        assert annotations is not None, name
        read_only = annotations.read_only_hint is True
        assert read_only == (name in READ_ONLY), name
        if not read_only:
            assert annotations.destructive_hint == (name in DESTRUCTIVE), name


def test_tools_that_send_data_out_or_publish_say_to_ask_the_user_first() -> None:
    tools = offered()
    for name in ("add_export", "publish_dashboard", "create_automation"):
        assert "Ask the user first" in tools[name].description, name  # type: ignore[attr-defined]
