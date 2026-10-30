"""Adding an export to a view, and what a model is told of its first run.

Seen live (a dev server, 28 Oct 2026): `add_export` answered with every export
of the view while the new one still read "added"; its run came after the call,
and when the run failed Mammoth removed the export, so nobody was told.
"""

from typing import Any
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

PROJECT, DATASET, VIEW = 3, 5, 9
PROJECT_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}"
DATASETS = f"{PROJECT_PATH}/datasets"
EXPORTS = f"{DATASETS}/{DATASET}/dataviews/{VIEW}/pipeline/exports"
NEW_ID, OLD_ID = 62, 61
RUNS = f"{EXPORTS}/{NEW_ID}/runs"
JOB = "/jobs/41"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "view_id": VIEW}
# The job the add route answers with, as the SDK reads it.
STARTED = {
    "job": {
        "id": 41,
        "status": "processing",
        "response": {},
        "path": EXPORTS,
        "operation": "add_action",
        "created_at": "2026-10-28T11:00:07",
        "last_updated_at": "2026-10-28T11:00:07",
    }
}
# The add job ends before the export runs (a dev server, 28 Oct 2026).
ADDED = {"job": {"id": 41, "status": "success", "response": {}}}
SENT = {"id": 7, "status": "success", "rows_exported": 4, "triggered_by": "pipeline"}
REFUSED = {"id": 7, "status": "failed", "error_message": "Login failed", "triggered_by": "pipeline"}
QUICK_POLL = patch("mammoth_mcp_server.export_runs.EXPORT_POLL_SECONDS", 0.01)
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)
SFTP = {"host": "files.example.com", "username": "mammoth", "password": "secret"}


def an_export(export_id: int, status: str, handler: str = "sftp") -> dict[str, Any]:
    return {
        "id": export_id,
        "dataview_id": VIEW,
        "handler_type": handler,
        "trigger_type": "pipeline",
        "status": status,
        "target_properties": {},
    }


OLD = an_export(OLD_ID, "executed")


def a_view(api: FakeApi, *listings: list[dict[str, Any]], runs: tuple[Any, ...] = ()) -> None:
    """A view whose exports list as each listing in turn, the last from then on."""
    for exports in listings:
        api.answer("GET", EXPORTS, {"limit": 50, "offset": 0, "next": "", "exports": exports})
    api.answer("POST", EXPORTS, STARTED)
    api.answer("GET", JOB, ADDED)
    api.answer("GET", RUNS, {"export_id": NEW_ID, "runs": list(runs)})


def datasets_named(*named: tuple[int, str]) -> dict[str, Any]:
    return {"datasets": [{"id": i, "name": name} for i, name in named], "next": ""}


def what_was_sent(api: FakeApi) -> dict[str, Any]:
    [sent] = api.sent("POST", EXPORTS)
    body: dict[str, Any] = api.body(sent)
    return body


class TestTheFirstRun:
    def test_the_new_export_is_reported_with_its_run_and_no_other_export(self) -> None:
        new = an_export(NEW_ID, "executed")
        with a_fake_api() as api, as_caller(), QUICK_POLL:
            a_view(api, [OLD], [OLD, an_export(NEW_ID, "added")], [OLD, new], runs=(SENT,))
            answer = call_tool("add_export", destination="sftp", settings=SFTP, **IDS)

        assert answer["outcome"] == "ran"
        assert answer["export"]["id"] == NEW_ID
        assert answer["last_run"]["rows_exported"] == 4
        assert "exports" not in answer
        assert answer["mammoth_url"].endswith(f"/views/{VIEW}")

    def test_a_run_that_fails_says_why(self) -> None:
        new = an_export(NEW_ID, "executed")
        with a_fake_api() as api, as_caller(), QUICK_POLL:
            a_view(api, [OLD], [OLD, new], runs=(REFUSED,))
            answer = call_tool("add_export", destination="sftp", settings=SFTP, **IDS)

        assert answer["outcome"] == "run_failed"
        assert answer["last_run"]["error_message"] == "Login failed"

    def test_an_export_mammoth_removed_after_its_first_run_failed_is_reported(self) -> None:
        with a_fake_api() as api, as_caller(), QUICK_POLL:
            a_view(api, [OLD], [OLD, an_export(NEW_ID, "added")], [OLD])
            answer = call_tool("add_export", destination="sftp", settings=SFTP, **IDS)

        assert answer["outcome"] == "run_failed"
        assert answer["export"] is None
        assert "removed" in answer["next_step"]

    def test_a_run_still_going_when_the_call_ends_is_not_reported_as_done(self) -> None:
        with a_fake_api() as api, as_caller(), QUICK_POLL, SHORT_CALL:
            a_view(api, [OLD], [OLD, an_export(NEW_ID, "executing")])
            answer = call_tool("add_export", destination="sftp", settings=SFTP, **IDS)

        assert answer["outcome"] == "run_pending"
        assert answer["export"]["id"] == NEW_ID
        assert "get_export" in answer["next_step"]

    def test_an_export_not_run_now_is_reported_added_and_not_waited_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [OLD], [OLD, an_export(NEW_ID, "added")])
            answer = call_tool(
                "add_export", destination="sftp", settings=SFTP, run_now=False, **IDS
            )

        assert answer["outcome"] == "added"
        assert answer["export"]["id"] == NEW_ID
        assert not api.sent("GET", RUNS)
        assert len(api.sent("GET", EXPORTS)) == 2

    def test_no_new_export_listed_after_the_add_is_said_plainly_not_called_removed(self) -> None:
        # Either its first run failed and Mammoth removed it, or it was never added:
        # the tool cannot tell which, so it says so.
        with a_fake_api() as api, as_caller(), QUICK_POLL:
            a_view(api, [OLD], [OLD])
            answer = call_tool("add_export", destination="sftp", settings=SFTP, **IDS)

        assert answer["outcome"] == "not_listed"
        assert answer["export"] is None
        assert "list_exports" in answer["next_step"]
        assert not api.sent("GET", RUNS)


class TestSendingToADataset:
    def test_its_settings_are_listed(self) -> None:
        with as_caller():
            schema = call_tool("get_schema", kind="export", of="internal_dataset")

        assert schema["checked"] is True
        assert schema["required"] == []
        assert set(schema["one_of"]) == {"dataset_name", "target_dataset_name", "target_ds_id"}
        assert {"save_as_mode", "column_mapping"} <= set(schema["optional"])

    def test_a_new_dataset_gets_the_name_given(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [], [an_export(NEW_ID, "added", "internal_dataset")])
            call_tool(
                "add_export",
                destination="internal_dataset",
                settings={"dataset_name": "Orders"},
                run_now=False,
                **IDS,
            )

        sent = what_was_sent(api)["target_properties"]
        assert sent["DS_NAME"] == "Orders"
        assert sent["TARGET_DS_ID"] is None

    def test_rows_are_appended_to_the_dataset_named(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", DATASETS, datasets_named((DATASET, "Sales"), (44, "Orders")))
            a_view(api, [], [an_export(NEW_ID, "added", "internal_dataset")])
            call_tool(
                "add_export",
                destination="internal_dataset",
                settings={"target_dataset_name": "orders", "save_as_mode": "append"},
                run_now=False,
                **IDS,
            )

        sent = what_was_sent(api)["target_properties"]
        assert sent["TARGET_DS_ID"] == 44
        assert sent["SAVE_AS_DS_MODE"] == "APPEND_TO_DS"
        # Seen live: without the name, the run said it wrote to "Result Dataset".
        assert sent["DS_NAME"] == "Orders"

    def test_a_dataset_named_by_id_is_sent_with_its_own_name(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", DATASETS, datasets_named((DATASET, "Sales"), (44, "Orders")))
            a_view(api, [], [an_export(NEW_ID, "added", "internal_dataset")])
            call_tool(
                "add_export",
                destination="internal_dataset",
                settings={"target_ds_id": 44},
                run_now=False,
                **IDS,
            )

        sent = what_was_sent(api)["target_properties"]
        assert (sent["TARGET_DS_ID"], sent["DS_NAME"]) == (44, "Orders")

    def test_a_dataset_id_not_in_the_project_is_refused(self) -> None:
        with (
            a_fake_api() as api,
            as_caller(),
            pytest.raises(ToolError, match="No dataset 44"),
        ):
            api.answer("GET", DATASETS, datasets_named((DATASET, "Sales")))
            call_tool(
                "add_export", destination="internal_dataset", settings={"target_ds_id": 44}, **IDS
            )

        assert not api.sent("POST", EXPORTS)

    def test_two_datasets_of_that_name_are_named_and_nothing_is_added(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", DATASETS, datasets_named((44, "Orders"), (45, "Orders")))
            a_view(api, [])
            answer = call_tool(
                "add_export",
                destination="internal_dataset",
                settings={"target_dataset_name": "Orders"},
                **IDS,
            )

        assert not api.sent("POST", EXPORTS)
        assert answer["outcome"] == "which_dataset"
        assert [d["id"] for d in answer["datasets"]] == [44, 45]
        assert answer["datasets"][0]["mammoth_url"].endswith("/datasets/44")
        assert "target_ds_id" in answer["next_step"]

    def test_no_dataset_of_that_name_is_refused(self) -> None:
        with (
            a_fake_api() as api,
            as_caller(),
            pytest.raises(ToolError, match="No dataset named 'Orders'"),
        ):
            api.answer("GET", DATASETS, datasets_named((DATASET, "Sales")))
            call_tool(
                "add_export",
                destination="internal_dataset",
                settings={"target_dataset_name": "Orders"},
                **IDS,
            )

        assert not api.sent("POST", EXPORTS)

    @pytest.mark.parametrize(
        ("settings", "why"),
        [
            ({}, "dataset_name"),
            ({"dataset_name": "Orders", "target_ds_id": 44}, "only one"),
            ({"target_ds_id": 44, "save_as_mode": "merge"}, "append"),
            ({"DS_NAME": "Orders"}, "DS_NAME"),
        ],
    )
    def test_settings_that_cannot_work_are_refused(
        self, settings: dict[str, Any], why: str
    ) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match=why):
            call_tool("add_export", destination="internal_dataset", settings=settings, **IDS)

        assert not api.sent("POST", EXPORTS)


class TestACsvFile:
    def test_it_is_refused_and_a_destination_that_works_is_named(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="s3"):
            call_tool("add_export", destination="csv_file", settings={}, **IDS)

        assert not api.sent("POST", EXPORTS)

    def test_it_is_not_offered(self) -> None:
        from mammoth_mcp_server.tools.exports import DESTINATIONS

        assert "csv_file" not in DESTINATIONS
