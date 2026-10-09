"""The one project a connection may act in.

A user who picks a project on the consent screen fences their token to it:
Mammoth refuses the token everywhere else. Nothing here asked Mammoth what
that project was, so a tool asked the user again and a write died on an
authorization error. These tests hold the three places that now read the pin.
"""

from collections.abc import Generator

import pytest
from mammoth.exceptions import MammothAPIError, MammothError
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import BrowseFields, ListFields, UploadFields
from mammoth_mcp_server.sdk import check_project, own_project
from mammoth_mcp_server.tools.discovery import list_projects
from mammoth_mcp_server.upload_app import request_upload
from mammoth_mcp_server.upload_routes import RELAYED_STATUS, refused_status

from .helpers import WORKSPACE, FakeRedis, a_fake_api, a_fake_store, as_caller, run

PINNED, OTHER = 31, 32
PROJECTS_PATH = f"/workspaces/{WORKSPACE}/projects"
BROWSE_PATH = f"/workspaces/{WORKSPACE}/browse"


def a_project(project_id: int) -> dict[str, object]:
    return {ListFields.ID: project_id, "name": f"project {project_id}"}


class TestTheCallersOwnProject:
    def test_a_pinned_caller_knows_their_project(self) -> None:
        with as_caller(project_id=PINNED):
            assert own_project() == PINNED

    def test_an_all_projects_caller_has_none(self) -> None:
        with as_caller():
            assert own_project() is None

    def test_another_project_is_refused_before_mammoth_is_asked(self) -> None:
        with as_caller(project_id=PINNED), pytest.raises(ToolError) as refused:
            check_project(OTHER)
        assert str(PINNED) in str(refused.value)

    def test_the_pinned_project_itself_is_allowed(self) -> None:
        with as_caller(project_id=PINNED):
            check_project(PINNED)

    def test_an_all_projects_caller_may_name_any_project(self) -> None:
        with as_caller():
            check_project(OTHER)


def a_browsed_project(project_id: int) -> dict[str, object]:
    """One row as the browse route answers it: a project among other types."""
    return {
        ListFields.ID: project_id,
        ListFields.NAME: f"project {project_id}",
        BrowseFields.TYPE: BrowseFields.PROJECT,
        "url": f"/workspaces/{WORKSPACE}/projects/{project_id}",
    }


class TestListingProjects:
    def test_a_pinned_caller_is_shown_their_project_alone(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", BROWSE_PATH, {BrowseFields.RESOURCES: [a_browsed_project(PINNED)]})
            with as_caller(project_id=PINNED):
                found = run(list_projects(workspace_id=WORKSPACE))
        assert found[ListFields.PROJECTS] == [a_project(PINNED)]

    def test_the_pinned_project_is_found_when_it_is_on_no_page_that_was_asked_for(self) -> None:
        """The defect this guards: a workspace with more projects than one page
        holds answered an empty list to a connection that has exactly one."""
        with a_fake_api() as api:
            api.answer("GET", PROJECTS_PATH, {ListFields.PROJECTS: [a_project(OTHER)]})
            api.answer("GET", BROWSE_PATH, {BrowseFields.RESOURCES: [a_browsed_project(PINNED)]})
            with as_caller(project_id=PINNED):
                found = run(list_projects(workspace_id=WORKSPACE))
        assert found[ListFields.PROJECTS] == [a_project(PINNED)]

    def test_a_pinned_caller_asks_for_their_project_by_id(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", BROWSE_PATH, {BrowseFields.RESOURCES: [a_browsed_project(PINNED)]})
            with as_caller(project_id=PINNED):
                run(list_projects(workspace_id=WORKSPACE))
            asked = api.sent("GET", BROWSE_PATH)[0].url.params
        assert asked[BrowseFields.IDS] == str(PINNED)
        assert asked[BrowseFields.TYPE] == BrowseFields.PROJECT

    def test_a_pinned_caller_never_pages_the_projects_route(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", PROJECTS_PATH, {ListFields.PROJECTS: [a_project(OTHER)]})
            api.answer("GET", BROWSE_PATH, {BrowseFields.RESOURCES: [a_browsed_project(PINNED)]})
            with as_caller(project_id=PINNED):
                run(list_projects(workspace_id=WORKSPACE))
        assert api.sent("GET", PROJECTS_PATH) == []

    def test_a_pinned_project_that_is_gone_lists_nothing(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", BROWSE_PATH, {BrowseFields.RESOURCES: []})
            with as_caller(project_id=PINNED):
                found = run(list_projects(workspace_id=WORKSPACE))
        assert found[ListFields.PROJECTS] == []

    def test_an_all_projects_caller_is_shown_them_all(self) -> None:
        rows = [a_project(PINNED), a_project(OTHER)]
        with a_fake_api() as api:
            api.answer("GET", PROJECTS_PATH, {ListFields.PROJECTS: list(rows)})
            with as_caller():
                found = run(list_projects(workspace_id=WORKSPACE))
        assert found[ListFields.PROJECTS] == rows

    def test_an_all_projects_caller_never_browses(self) -> None:
        with a_fake_api() as api:
            api.answer("GET", PROJECTS_PATH, {ListFields.PROJECTS: [a_project(PINNED)]})
            with as_caller():
                run(list_projects(workspace_id=WORKSPACE))
        assert api.sent("GET", BROWSE_PATH) == []


class TestAskingForAnUpload:
    @pytest.fixture(autouse=True)
    def store(self) -> Generator[FakeRedis]:
        with a_fake_store() as fake:
            yield fake

    def test_a_pinned_caller_need_not_name_a_project(self) -> None:
        with as_caller(project_id=PINNED):
            minted = run(request_upload(workspace_id=WORKSPACE))
        assert minted[UploadFields.UPLOAD_ID]

    def test_another_project_is_refused(self) -> None:
        with as_caller(project_id=PINNED), pytest.raises(ToolError) as refused:
            run(request_upload(workspace_id=WORKSPACE, project_id=OTHER))
        assert str(PINNED) in str(refused.value)

    def test_an_all_projects_caller_must_still_name_one(self) -> None:
        with as_caller(), pytest.raises(ToolError) as refused:
            run(request_upload(workspace_id=WORKSPACE))
        assert "project" in str(refused.value).lower()


class TestRelayingWhatMammothSaid:
    def test_the_apis_own_status_is_relayed(self) -> None:
        refused = MammothAPIError("You are not authorized", status_code=403)
        assert refused_status(refused) == 403

    @pytest.mark.parametrize("status", [None, 0, 200, 600, "403"])
    def test_a_status_that_is_not_a_refusal_becomes_a_relay_failure(self, status: object) -> None:
        refused = MammothAPIError("No", status_code=status)  # type: ignore[arg-type]
        assert refused_status(refused) == RELAYED_STATUS

    def test_an_error_with_no_status_at_all_becomes_a_relay_failure(self) -> None:
        assert refused_status(MammothError("the connection died")) == RELAYED_STATUS
