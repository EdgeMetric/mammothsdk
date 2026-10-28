"""Taking a change back: restore what was trashed, or put a pipeline back as it was."""

from typing import Any
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

PROJECT, DATASET, VIEW = 3, 5, 9
PROJECT_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}"
VIEW_PATH = f"{PROJECT_PATH}/datasets/{DATASET}/dataviews/{VIEW}"
TRASH = f"{PROJECT_PATH}/trash"
RESTORE = f"{TRASH}/restore"
VERSIONS = f"{VIEW_PATH}/pipeline/versions"
JOB = "/jobs/41"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
VIEW_IDS = {**IDS, "dataset_id": DATASET, "view_id": VIEW}
DATASET_PATH = f"{PROJECT_PATH}/datasets/{DATASET}"
VIEWS = f"{DATASET_PATH}/dataviews"
NO_IMPACT = {"dashboards": [], "exports": [], "views": [], "automations": [], "dependencies": {}}
# What deleting a view takes with it, as Mammoth lists it (a dev server, 28 Oct 2026).
SENDS_TO_A_DATASET = {
    "id": 398,
    "name": "Monthly totals",
    "handler_type": "internal_dataset",
    "connector": "internal_dataset",
    "has_transform": False,
    "destination": "Monthly totals",
    "data_pass_through": True,
    "moves_to_end": False,
}

STARTED = {"job": {"id": 41}}
RUNNING = {"job": {"id": 41, "status": "processing", "response": None}}
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)


def done(response: dict[str, Any]) -> dict[str, Any]:
    return {"job": {"id": 41, "status": "success", "response": response}}


TRASHED_VIEW = {
    "id": VIEW,
    "type": "dataview",
    "name": "Cleaned",
    "project_id": PROJECT,
    "dataset_id": DATASET,
    "trashed_at": "2026-10-22T06:00:00",
    "trashed_by": {"id": 19, "name": "Api Tests"},
    "days_until_purge": 29,
    "cascade_trash_event_id": None,
    "folder_resource_id": None,
    "original_folder_path": [],
}
# Sent only so the web app can group a trashed view under its dataset.
LIVE_PARENT = {"id": DATASET, "type": "dataset", "name": "Customers", "is_active_parent": True}
TRASH_LIST = {
    "items": [TRASHED_VIEW, LIVE_PARENT],
    "total": 1,
    "retention_days": 30,
    "limit": 50,
    "offset": 0,
    "next": None,
}
VERSION_LIST = {
    "versions": [
        {
            "id": 202,
            "dataview_id": VIEW,
            "name": "Version 3",
            "modification_type": "DELETE_TASK",
            "created_at": "2026-10-22T06:10:00",
            "created_by": 19,
            "note": None,
            "change_summary": {"deleted": 1},
        },
        {
            "id": 201,
            "dataview_id": VIEW,
            "name": "Version 2",
            "modification_type": "ADD_TASK",
            "created_at": "2026-10-22T06:00:00",
            "created_by": 19,
            "note": None,
            "change_summary": {"added": 1},
        },
    ],
    "limit": 10,
    "offset": 10,
    "next": None,
}
PIPELINE_STATE = {"draft_mode": "off", "auto_run": True, "execution_state": "idle"}
TASKS = {"tasks": [{"id": 77, "sequence": 1, "status": "ready", "params": {}}]}


def a_view(
    api: FakeApi,
    job: dict[str, Any] | None = None,
    views: tuple[int, ...] = (VIEW, 10, 11),
    impact: dict[str, Any] = NO_IMPACT,
) -> None:
    api.answer("GET", VIEWS, {"dataviews": [{"id": view} for view in views]})
    for view in views:
        api.answer("GET", f"{VIEWS}/{view}/impact", impact if view == VIEW else NO_IMPACT)
    api.answer("POST", f"{VIEW_PATH}/trash", STARTED)
    api.answer("GET", TRASH, TRASH_LIST)
    api.answer("POST", RESTORE, STARTED)
    api.answer("GET", VERSIONS, VERSION_LIST)
    api.answer("POST", f"{VERSIONS}/201", STARTED)
    api.answer("GET", f"{VIEW_PATH}/pipeline", PIPELINE_STATE)
    api.answer("GET", f"{VIEW_PATH}/pipeline/tasks", TASKS)
    api.answer("GET", JOB, job or done({}))


class TestDeletingViews:
    def test_a_view_goes_to_the_trash_not_away_for_good(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            answer = call_tool("delete_views", dataset_id=DATASET, view_ids=[VIEW], **IDS)

        assert api.sent("POST", f"{VIEW_PATH}/trash")
        assert not api.sent("DELETE", VIEW_PATH)
        assert answer["deleted"] == [VIEW]
        assert "undo" in answer["next_step"]

    def test_a_view_the_trash_refuses_is_reported_and_the_rest_go_on(self) -> None:
        other = f"{PROJECT_PATH}/datasets/{DATASET}/dataviews/10/trash"
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer("POST", other, {"message": "Other views depend on this one"}, status=400)
            answer = call_tool("delete_views", dataset_id=DATASET, view_ids=[10, VIEW], **IDS)

        assert answer["deleted"] == [VIEW]
        [failed] = answer["failed"]
        assert failed["view_id"] == 10
        assert "depend" in failed["error"]

    def test_a_datasets_last_view_is_refused_since_the_dataset_would_go_with_it(self) -> None:
        # Seen live: Mammoth moves a dataset to the trash with its last view.
        with a_fake_api() as api, as_caller():
            a_view(api, views=(VIEW,))
            with pytest.raises(ToolError, match="whole_dataset"):
                call_tool("delete_views", dataset_id=DATASET, view_ids=[VIEW], **IDS)

        assert not api.sent("POST", f"{VIEW_PATH}/trash")

    def test_what_goes_with_a_view_is_listed_and_nothing_is_deleted_yet(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, impact={**NO_IMPACT, "exports": [SENDS_TO_A_DATASET]})
            answer = call_tool("delete_views", dataset_id=DATASET, view_ids=[VIEW], **IDS)

        assert not api.sent("POST", f"{VIEW_PATH}/trash")
        assert api.sent("GET", f"{VIEW_PATH}/impact")[0].url.params["scope"] == "view"
        assert answer["deleted"] == []
        assert answer["goes_with_them"] == {
            "exports": [
                {
                    "view_id": VIEW,
                    "id": 398,
                    "name": "Monthly totals",
                    "handler_type": "internal_dataset",
                    "destination": "Monthly totals",
                }
            ]
        }
        assert "confirmed=true" in answer["next_step"]

    def test_once_the_user_agrees_the_view_and_what_goes_with_it_are_deleted(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, impact={**NO_IMPACT, "exports": [SENDS_TO_A_DATASET]})
            answer = call_tool(
                "delete_views", dataset_id=DATASET, view_ids=[VIEW], confirmed=True, **IDS
            )

        assert api.sent("POST", f"{VIEW_PATH}/trash")
        assert answer["deleted"] == [VIEW]

    def test_a_whole_dataset_is_listed_with_its_views_before_it_goes(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, views=(VIEW,))
            api.answer("POST", f"{DATASET_PATH}/trash", STARTED)
            answer = call_tool("delete_views", dataset_id=DATASET, whole_dataset=True, **IDS)

        assert not api.sent("POST", f"{DATASET_PATH}/trash")
        assert answer["goes_with_them"] == {"dataset": DATASET, "views": [VIEW]}

    def test_a_whole_dataset_goes_to_the_trash_once_the_user_agrees(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, views=(VIEW,))
            api.answer("POST", f"{DATASET_PATH}/trash", STARTED)
            answer = call_tool(
                "delete_views", dataset_id=DATASET, whole_dataset=True, confirmed=True, **IDS
            )

        assert api.sent("POST", f"{DATASET_PATH}/trash")
        assert not api.sent("POST", f"{VIEW_PATH}/trash")
        assert answer["trashed_dataset"] == DATASET
        assert "undo" in answer["next_step"]

    def test_no_views_and_no_whole_dataset_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            with pytest.raises(ToolError, match="view_ids"):
                call_tool("delete_views", dataset_id=DATASET, **IDS)


class TestListingTheTrash:
    def test_what_can_be_restored_is_listed(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            trash = call_tool("list_trash", **IDS)

        assert trash["items"] == [
            {
                "id": VIEW,
                "type": "dataview",
                "name": "Cleaned",
                "dataset_id": DATASET,
                "trashed_at": "2026-10-22T06:00:00",
                "days_until_purge": 29,
            }
        ]
        assert trash["retention_days"] == 30
        assert "next_offset" not in trash

    def test_a_trash_with_more_than_a_page_says_where_the_next_starts(self) -> None:
        # Seen live: 55 views in the trash, 50 to a page.
        with a_fake_api() as api, as_caller():
            api.answer("GET", TRASH, {**TRASH_LIST, "total": 55, "offset": 50})
            a_view(api)
            trash = call_tool("list_trash", offset=50, **IDS)

        [sent] = api.sent("GET", TRASH)
        assert sent.url.params["offset"] == "50"
        # 50 + 50 covers all 55: this is the last page.
        assert "next_offset" not in trash

    def test_the_first_page_of_a_long_trash_names_the_next(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", TRASH, {**TRASH_LIST, "total": 55})
            a_view(api)
            trash = call_tool("list_trash", **IDS)

        assert trash["next_offset"] == 50

    def test_a_trash_that_fills_one_page_exactly_has_no_next(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", TRASH, {**TRASH_LIST, "total": 50})
            a_view(api)
            trash = call_tool("list_trash", **IDS)

        assert "next_offset" not in trash

    def test_one_kind_is_listed_when_asked_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            call_tool("list_trash", kind="dashboard", **IDS)

        [sent] = api.sent("GET", TRASH)
        assert sent.url.params["type"] == "dashboard"


class TestRestoringFromTheTrash:
    def test_the_items_named_are_restored_and_waited_for(self) -> None:
        restored = done({"succeeded": [{"type": "dataview", "id": VIEW}], "failed": []})
        with a_fake_api() as api, as_caller():
            a_view(api, job=restored)
            answer = call_tool(
                "undo", what="trash", items=[{"type": "dataview", "id": VIEW}], **IDS
            )

        [sent] = api.sent("POST", RESTORE)
        assert api.body(sent) == {"items": [{"type": "dataview", "id": VIEW}]}
        assert answer["succeeded"] == [{"type": "dataview", "id": VIEW}]
        assert answer["failed"] == []

    def test_a_restore_still_going_says_so(self) -> None:
        # A dataset's views are restored with it, which can outlast the call.
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_view(api, job=RUNNING)
            answer = call_tool(
                "undo", what="trash", items=[{"type": "dataset", "id": DATASET}], **IDS
            )

        assert answer["status"] == "processing"
        assert answer["job_id"] == 41
        assert "do not call undo again" in answer["note"]

    @pytest.mark.parametrize("items", [None, []])
    def test_restoring_names_what_to_restore(self, items: list[Any] | None) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            with pytest.raises(ToolError, match="list_trash"):
                call_tool("undo", what="trash", items=items, **IDS)

        assert not api.requests


class TestPuttingAPipelineBack:
    def test_the_version_named_is_applied_and_the_pipeline_read_after(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            answer = call_tool(
                "undo", what="pipeline", dataset_id=DATASET, view_id=VIEW, version_id=201, **IDS
            )

        assert api.sent("POST", f"{VERSIONS}/201")
        assert answer["steps"] == TASKS["tasks"]
        # The version from just before the undo is listed, so this is undone the same way.
        assert "include_versions" in answer["next_step"]
        assert "running" not in answer["next_step"]

    def test_a_view_still_running_after_the_undo_says_so(self) -> None:
        # Seen live: the apply's job ends before the view's run does.
        with a_fake_api() as api, as_caller():
            api.answer(
                "GET", f"{VIEW_PATH}/pipeline", {**PIPELINE_STATE, "execution_state": "submitted"}
            )
            a_view(api)
            answer = call_tool(
                "undo", what="pipeline", dataset_id=DATASET, view_id=VIEW, version_id=201, **IDS
            )

        assert "running again" in answer["next_step"]

    def test_a_view_whose_run_failed_after_the_undo_says_so(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer(
                "GET",
                f"{VIEW_PATH}/pipeline",
                {**PIPELINE_STATE, "execution_state": "runtime_error"},
            )
            a_view(api)
            answer = call_tool(
                "undo", what="pipeline", dataset_id=DATASET, view_id=VIEW, version_id=201, **IDS
            )

        assert "running again" not in answer["next_step"]
        assert "failed" in answer["next_step"]

    def test_a_pipeline_still_going_back_says_so(self) -> None:
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            a_view(api, job=RUNNING)
            answer = call_tool(
                "undo", what="pipeline", dataset_id=DATASET, view_id=VIEW, version_id=201, **IDS
            )

        assert answer["status"] == "processing"
        assert "do not call undo again" in answer["note"]

    def test_a_pipeline_undo_names_the_view_and_the_version(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            with pytest.raises(ToolError, match="version_id"):
                call_tool("undo", what="pipeline", dataset_id=DATASET, view_id=VIEW, **IDS)

        assert not api.requests


class TestThePipelinesVersions:
    def test_the_latest_versions_come_with_the_pipeline_when_asked_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            answer = call_tool("get_pipeline", include_versions=True, **VIEW_IDS)

        [sent] = api.sent("GET", VERSIONS)
        assert sent.url.params["sort"] == "(id:desc)"
        assert [version["id"] for version in answer["versions"]] == [202, 201]
        assert answer["versions"][0]["change_summary"] == {"deleted": 1}

    def test_a_plain_read_does_not_list_them(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            answer = call_tool("get_pipeline", **VIEW_IDS)

        assert "versions" not in answer
        assert not api.sent("GET", VERSIONS)
