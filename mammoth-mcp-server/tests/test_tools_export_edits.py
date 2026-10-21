"""Changing one export of a view, or running it, and what a model is told."""

from copy import deepcopy
from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

PROJECT, DATASET, VIEW = 3, 5, 9
VIEW_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"
EXPORTS = f"{VIEW_PATH}/pipeline/exports"
EXPORT_ID = 61
EXPORT = f"{EXPORTS}/{EXPORT_ID}"
RUNS = f"{EXPORT}/runs"
JOB = "/jobs/41"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "view_id": VIEW}

TO_SFTP: dict[str, Any] = {
    "id": EXPORT_ID,
    "dataview_id": VIEW,
    "sequence": 2,
    "handler_type": "sftp",
    "trigger_type": "pipeline",
    "end_of_pipeline": True,
    "status": "executed",
    "target_properties": {
        "host": "files.example.com",
        "username": "mammoth",
        "password": "******",
        "directory": "/in",
        "port": 22,
    },
    "additional_properties": {},
    "condition": {},
}
STARTED = {"job": {"id": 41}}
DONE = {"job": {"id": 41, "status": "success", "response": {}}}
SENT = {"id": 7, "status": "success", "rows_exported": 4, "triggered_by": "manual"}
OLDER = {"id": 6, "status": "success", "rows_exported": 3, "triggered_by": "pipeline"}
REFUSED_BY_SFTP = {
    "id": 8,
    "status": "failed",
    "error_message": "Authentication failed",
    "triggered_by": "manual",
}


def suspended(export: dict[str, Any]) -> dict[str, Any]:
    return {**deepcopy(export), "status": "suspended"}


def scheduled(export: dict[str, Any]) -> dict[str, Any]:
    weekly = {"frequency": "weekly", "by_week_day": ["MO"], "interval": 1}
    return {
        **deepcopy(export),
        "trigger_type": "schedule",
        "additional_properties": {"schedule": weekly},
    }


def a_view(
    api: FakeApi,
    *listings: list[dict[str, Any]],
    runs: tuple[dict[str, Any], ...] = (),
    job: dict[str, Any] = DONE,
    later_runs: tuple[dict[str, Any], ...] | None = None,
) -> None:
    """A view whose exports list as each listing in turn, the last from then on.

    Its runs list as `runs`, and as `later_runs` from the second read on.
    """
    for exports in listings:
        api.answer("GET", EXPORTS, {"limit": 10, "offset": 0, "next": "", "exports": exports})
    api.answer("GET", RUNS, {"export_id": EXPORT_ID, "runs": list(runs)})
    if later_runs is not None:
        api.answer("GET", RUNS, {"export_id": EXPORT_ID, "runs": list(later_runs)})
    api.answer("PATCH", EXPORT, STARTED)
    api.answer("GET", JOB, job)


def the_patch(api: FakeApi) -> dict[str, Any]:
    [sent] = api.sent("PATCH", EXPORT)
    [patch] = api.body(sent)["patches"]
    return patch


class TestReplacingSettings:
    def test_only_the_settings_named_change(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            answer = call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        patch = the_patch(api)
        assert (patch["op"], patch["path"]) == ("replace", "params")
        settings = patch["value"]["target_properties"]
        assert settings["directory"] == "/out"
        assert settings["host"] == "files.example.com"
        # Mammoth puts the stored password back in place of the mask.
        assert settings["password"] == "******"
        assert answer["outcome"] == "changed"
        assert "nothing was sent" in answer["next_step"]

    def test_the_export_is_saved_in_place_and_sends_nothing(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        value = the_patch(api)["value"]
        assert value["TRIGGER_ID"] == EXPORT_ID
        assert value["DATAVIEW_ID"] == VIEW
        assert value["run_immediately"] is False
        assert value["trigger_type"] == "pipeline"

    def test_an_export_at_the_end_stays_at_the_end(self) -> None:
        # A save that names a sequence pins the export there, so a step added
        # later would run after it. Seen on a dev server.
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        value = the_patch(api)["value"]
        assert value["end_of_pipeline"] is True
        assert value.get("sequence") is None

    def test_an_export_inside_the_pipeline_keeps_its_place(self) -> None:
        inside = {**deepcopy(TO_SFTP), "end_of_pipeline": False}
        with a_fake_api() as api, as_caller():
            a_view(api, [inside])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        value = the_patch(api)["value"]
        assert (value["end_of_pipeline"], value["sequence"]) == (False, 2)

    def test_a_stored_setting_that_is_null_is_kept(self) -> None:
        stored = deepcopy(TO_SFTP)
        stored["target_properties"]["private_key"] = None
        with a_fake_api() as api, as_caller():
            a_view(api, [stored])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        settings = the_patch(api)["value"]["target_properties"]
        assert "private_key" in settings
        assert settings["private_key"] is None

    def test_a_setting_given_null_is_dropped(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": None},
                **IDS,
            )

        assert "directory" not in the_patch(api)["value"]["target_properties"]

    def test_a_scheduled_export_keeps_its_schedule(self) -> None:
        # Mammoth refuses a scheduled export saved without its schedule.
        with a_fake_api() as api, as_caller():
            a_view(api, [scheduled(TO_SFTP)])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        value = the_patch(api)["value"]
        assert value["trigger_type"] == "schedule"
        assert value["schedule"]["frequency"] == "weekly"

    def test_an_export_on_the_pipeline_sends_no_schedule(self) -> None:
        # Mammoth refuses a schedule on an export that runs with the pipeline,
        # even one left over in what the export stores.
        stale = {**scheduled(TO_SFTP), "trigger_type": "pipeline"}
        with a_fake_api() as api, as_caller():
            a_view(api, [stale])
            call_tool(
                "edit_export",
                export_id=EXPORT_ID,
                change="replace",
                settings={"directory": "/out"},
                **IDS,
            )

        assert "schedule" not in the_patch(api)["value"]

    def test_a_setting_the_destination_does_not_take_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            with pytest.raises(ToolError, match="bucket"):
                call_tool(
                    "edit_export",
                    export_id=EXPORT_ID,
                    change="replace",
                    settings={"bucket": "b"},
                    **IDS,
                )

        assert api.sent("PATCH", EXPORT) == []

    def test_without_settings_it_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            with pytest.raises(ToolError, match="needs `settings`"):
                call_tool("edit_export", export_id=EXPORT_ID, change="replace", **IDS)

    def test_a_refused_save_says_why(self) -> None:
        refused = {"job": {"id": 41, "status": "failure", "response": {"message": "in error"}}}
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], job=refused)
            with pytest.raises(ToolError, match="in error"):
                call_tool(
                    "edit_export",
                    export_id=EXPORT_ID,
                    change="replace",
                    settings={"directory": "/out"},
                    **IDS,
                )


class TestWhichExport:
    def test_an_export_of_another_view_is_refused_before_anything_is_sent(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            with pytest.raises(ToolError, match=r"no export 99\. Its exports: \[61\]"):
                call_tool("edit_export", export_id=99, change="suspend", **IDS)

        assert [r for r in api.requests if r.method == "PATCH"] == []


class TestSuspendingAndRestoring:
    def test_suspending_sends_the_command_alone(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], [suspended(TO_SFTP)])
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="suspend", **IDS)

        assert the_patch(api) == {"op": "command", "path": "suspend", "value": None}
        assert answer["outcome"] == "changed"
        assert answer["export"]["status"] == "suspended"

    def test_restoring_a_suspended_export_sends_restore(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [suspended(TO_SFTP)], [TO_SFTP])
            call_tool("edit_export", export_id=EXPORT_ID, change="restore", **IDS)

        assert the_patch(api)["path"] == "restore"

    @pytest.mark.parametrize(
        ("export", "change", "reason"),
        [
            (suspended(TO_SFTP), "suspend", "suspended already"),
            (TO_SFTP, "restore", "not suspended"),
            (suspended(TO_SFTP), "run", "cannot run"),
        ],
        ids=["suspend-twice", "restore-a-running-export", "run-a-suspended-export"],
    )
    def test_a_command_that_cannot_do_anything_is_refused(
        self, export: dict[str, Any], change: str, reason: str
    ) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [export])
            with pytest.raises(ToolError, match=reason):
                call_tool("edit_export", export_id=EXPORT_ID, change=change, **IDS)

        assert api.sent("PATCH", EXPORT) == []

    def test_settings_with_a_command_are_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP])
            with pytest.raises(ToolError, match='only with "replace"'):
                call_tool(
                    "edit_export",
                    export_id=EXPORT_ID,
                    change="suspend",
                    settings={"directory": "/out"},
                    **IDS,
                )


class TestRunningNow:
    def test_a_run_reports_the_rows_it_sent(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(OLDER,), later_runs=(SENT, OLDER))
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert the_patch(api) == {"op": "command", "path": "run", "value": None}
        assert answer["outcome"] == "ran"
        assert answer["last_run"]["rows_exported"] == 4

    def test_a_run_mammoth_has_not_recorded_yet_is_not_reported_as_this_one(self) -> None:
        # Yesterday's run is still the newest one after this run's job ends.
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(SENT,))
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert answer["outcome"] == "run_pending"
        assert "get_export" in answer["next_step"]
        assert answer["last_run"] is None

    def test_a_route_that_answers_with_a_job_id_alone_is_waited_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(OLDER,), later_runs=(SENT, OLDER))
            api.answers[("PATCH", EXPORT)] = [(200, {"job_id": 41})]
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert len(api.sent("GET", JOB)) == 1
        assert answer["outcome"] == "ran"

    def test_a_failed_run_says_why_and_how_to_fix_it(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(), later_runs=(REFUSED_BY_SFTP,))
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert answer["outcome"] == "run_failed"
        assert answer["last_run"]["error_message"] == "Authentication failed"
        assert 'edit_export "replace"' in answer["next_step"]
        assert answer["mammoth_url"].endswith(f"/views/{VIEW}")

    def test_a_run_whose_job_fails_is_a_failed_run_with_mammoths_reason(self) -> None:
        failed = {"job": {"id": 41, "status": "failure", "response": {"message": "no route"}}}
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], job=failed)
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert answer["outcome"] == "run_failed"
        assert "no route" in answer["next_step"]
        # Mammoth recorded no run for it, so no older run stands in for it.
        assert answer["last_run"] is None

    def test_a_run_whose_job_fails_reports_the_run_mammoth_recorded(self) -> None:
        failed = {"job": {"id": 41, "status": "failure", "response": {"message": "no route"}}}
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(OLDER,), later_runs=(REFUSED_BY_SFTP, OLDER), job=failed)
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert answer["outcome"] == "run_failed"
        assert answer["last_run"]["id"] == REFUSED_BY_SFTP["id"]

    def test_a_run_whose_job_fails_does_not_report_an_older_run(self) -> None:
        failed = {"job": {"id": 41, "status": "failure", "response": {"message": "no route"}}}
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(OLDER,), job=failed)
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert answer["outcome"] == "run_failed"
        assert answer["last_run"] is None

    def test_a_route_that_answers_with_the_job_itself_is_waited_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, [TO_SFTP], runs=(OLDER,), later_runs=(SENT, OLDER))
            api.answers[("PATCH", EXPORT)] = [(200, {"id": 41, "status": "processing"})]
            answer = call_tool("edit_export", export_id=EXPORT_ID, change="run", **IDS)

        assert len(api.sent("GET", JOB)) == 1
        assert answer["outcome"] == "ran"


class TestReadingAnExport:
    def test_get_export_shows_its_recent_runs(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", EXPORT, deepcopy(TO_SFTP))
            api.answer("GET", RUNS, {"export_id": EXPORT_ID, "runs": [REFUSED_BY_SFTP, SENT]})
            answer = call_tool("get_export", export_id=EXPORT_ID, **IDS)

        [asked] = api.sent("GET", RUNS)
        assert asked.url.params["limit"] == "5"
        assert [run["status"] for run in answer["recent_runs"]] == ["failed", "success"]
        assert answer["recent_runs"][0]["error_message"] == "Authentication failed"
