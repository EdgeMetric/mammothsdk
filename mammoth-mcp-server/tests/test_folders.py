"""Folders: list them, make one, and upload into one.

A folder automation consolidates what lands in a folder, so a model that sets
one up needs a folder to point it at and a way to put files there.
"""

from typing import Any

from mammoth_mcp_server.consts import UploadFields
from mammoth_mcp_server.server import mcp_server, register_tools
from mammoth_mcp_server.upload_app import request_upload
from mammoth_mcp_server.upload_report import report_upload
from mammoth_mcp_server.upload_tickets import read_ticket

from .helpers import WORKSPACE, a_fake_api, a_fake_store, as_caller, call_tool, run

PROJECT = 3
PROJECT_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}"
FOLDERS = f"{PROJECT_PATH}/folders"
FILES = f"{PROJECT_PATH}/files"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
MONTHLY = {
    "id": 5,
    "name": "Monthly",
    "status": "active",
    "resource_id": 77,
    "parent_id": None,
    "created_by": "Api Tests",
}


def call(tool: str, **arguments: object) -> Any:
    """Call one tool as a client does. `call_tool` cannot pass an argument named `name`."""
    register_tools()
    result = run(mcp_server.call_tool(tool, dict(arguments)))
    assert result.structured_content is not None
    return dict(result.structured_content)


class TestFolders:
    def test_a_folder_is_made_and_named_by_the_id_uploads_and_automations_take(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", FOLDERS, {"folder": MONTHLY})
            made = call("create_folder", name="Monthly", **IDS)

        (sent,) = api.sent("POST", FOLDERS)
        assert api.body(sent) == {"name": "Monthly"}
        assert made == {"folder_id": 5, "folder_resource_id": 77, "name": "Monthly"}

    def test_a_folder_inside_another_names_its_parent(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", FOLDERS, {"folder": {**MONTHLY, "parent_id": 4}})
            call("create_folder", name="Monthly", parent_folder_resource_id=70, **IDS)

        (sent,) = api.sent("POST", FOLDERS)
        assert api.body(sent) == {"name": "Monthly", "parent_resource_id": "70"}

    def test_the_projects_folders_are_listed_with_its_files(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", FILES, {"files": [], "limit": 50, "offset": 0})
            api.answer("GET", FOLDERS, {"folders": [MONTHLY], "total": 1})
            listed = call_tool("list_files", **IDS)

        assert listed["folders"] == [
            {"folder_id": 5, "folder_resource_id": 77, "name": "Monthly", "parent_id": None}
        ]

    def test_text_is_uploaded_into_the_folder(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", FILES, {"job": {"id": 41}})
            api.answer("GET", "/jobs/41", {"job": {"id": 41, "status": "success", "response": {}}})
            api.answer("GET", f"{PROJECT_PATH}/resources", {"resources": []})
            answer = call_tool(
                "upload_file",
                file_name="sales.csv",
                content="a,b\n1,2\n",
                folder_resource_id=77,
                **IDS,
            )

        [upload] = api.sent("POST", FILES)
        assert upload.url.params["folder_resource_id"] == "77"
        [listed] = api.sent("GET", f"{PROJECT_PATH}/resources")
        assert listed.url.params["parent_id"] == "77"
        assert answer["status"] == "done"

    def test_what_landed_in_a_folder_is_looked_for_in_that_folder(self) -> None:
        # Seen live: Mammoth lists only the project's own items unless asked for a
        # folder's, so the upload was never found and the call ran out of time.
        ticket = {
            UploadFields.UPLOADED_AT: "2026-10-28T10:00:00+00:00",
            UploadFields.WORKSPACE_ID: WORKSPACE,
            UploadFields.PROJECT_ID: PROJECT,
            UploadFields.FOLDER_RESOURCE_ID: 77,
        }
        with a_fake_api() as api, as_caller():
            api.answer("GET", f"{PROJECT_PATH}/resources", {"resources": []})
            run(report_upload(ticket))

        [listed] = api.sent("GET", f"{PROJECT_PATH}/resources")
        assert listed.url.params["parent_type"] == "label"
        assert listed.url.params["parent_id"] == "77"

    def test_a_link_for_a_folder_remembers_the_folder(self) -> None:
        with a_fake_store(), as_caller():
            minted = run(request_upload(WORKSPACE, PROJECT, folder_resource_id=77))
            ticket = run(read_ticket(minted[UploadFields.UPLOAD_ID]))

        assert ticket is not None
        assert ticket[UploadFields.FOLDER_RESOURCE_ID] == 77
