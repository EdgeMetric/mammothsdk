"""Workflows: find a template or describe one, draft, build, run and trigger it."""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.tools import workflows

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool

PROJECT = 3
BASE = f"/workspaces/{WORKSPACE}/projects/{PROJECT}"
TEMPLATES = f"{BASE}/workflow-templates"
DESCRIBE = f"{BASE}/workflows/describe"
WORKFLOW = f"{BASE}/workflows/41"
BANK = {
    "key": "bank-reconcile",
    "name": "Reconcile a bank statement",
    "sentence": "Match bank lines to the ledger.",
    "words": ["bank", "reconcile", "statement"],
}
SALES = {"key": "sales-by-month", "name": "Sales by month", "words": ["sales", "month"]}
INVOICES = {"key": "late-invoices", "name": "Chase late invoices", "words": ["invoice"]}


def _call(tool: str, /, **arguments: object) -> Any:
    return call_tool(tool, workspace_id=WORKSPACE, project_id=PROJECT, **arguments)


@pytest.fixture(autouse=True)
def _no_waiting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mammoth.api.workflows._SAVE_POLL_SECONDS", 0.0)
    monkeypatch.setattr(workflows, "ANSWER_SECONDS", 0.0)
    monkeypatch.setattr("mammoth.api.workflow_triggers._POLL_SECONDS", 0.0)
    monkeypatch.setattr("mammoth.api.workflow_describe._POLL_SECONDS", 0.0)


class TestFindWorkflowTemplate:
    def test_the_users_words_pick_the_template_and_a_fit_names_its_tables(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", TEMPLATES, [SALES, BANK, INVOICES])
            api.answer(
                "POST",
                f"{TEMPLATES}/fits",
                [{"key": "bank-reconcile", "sure": True, "tables": {"bank": 9}}],
            )
            found = _call("find_workflow_template", words="reconcile my bank statement")

        assert [card["key"] for card in found["templates"]] == ["bank-reconcile"]
        assert found["templates"][0]["fits"] == {"tables": {"bank": 9}, "sure": True}

    def test_with_no_words_it_lists_what_the_tables_already_fit(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", TEMPLATES, [SALES, BANK, INVOICES])
            api.answer(
                "POST",
                f"{TEMPLATES}/fits",
                [{"key": "sales-by-month", "sure": False, "tables": {}}],
            )
            found = _call("find_workflow_template", dataset_ids=[9, 10])

        [request] = api.sent("POST", f"{TEMPLATES}/fits")
        assert api.body(request) == {"dataset_ids": [9, 10]}
        assert [card["key"] for card in found["templates"]] == ["sales-by-month"]


class TestDraftWorkflow:
    def test_a_template_draft_proposes_matches_previews_them_and_asks_what_it_is_unsure_of(
        self,
    ) -> None:
        roles = [
            {"role": "amount", "status": "matched", "mapping": {"column": "Amount"}},
            {
                "role": "date",
                "status": "check",
                "mapping": {"column": "Posted"},
                "question": "Posted?",
            },
            {"role": "memo", "status": "missing", "mapping": None},
        ]
        with a_fake_api() as api, as_caller():
            api.answer(
                "POST",
                f"{TEMPLATES}/bank-reconcile/fit",
                {"inputs": [{"key": "bank", "roles": roles}]},
            )
            api.answer("POST", f"{TEMPLATES}/bank-reconcile/preview", {"rows": [], "checks": []})
            drafted = _call("draft_workflow", template_key="bank-reconcile", inputs={"bank": 9})

        matches = {"bank": {"amount": {"column": "Amount"}, "date": {"column": "Posted"}}}
        assert drafted["matches"] == matches
        assert [q["role"] for q in drafted["questions"]] == ["date", "memo"]
        [preview] = api.sent("POST", f"{TEMPLATES}/bank-reconcile/preview")
        assert api.body(preview)["matches"] == matches
        assert api.body(preview)["inputs"] == {"bank": 9}

    def test_matches_the_user_changed_are_previewed_without_fitting_again(self) -> None:
        matches = {"bank": {"amount": {"column": "Net"}}}
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{TEMPLATES}/bank-reconcile/preview", {"rows": []})
            _call(
                "draft_workflow", template_key="bank-reconcile", inputs={"bank": 9}, matches=matches
            )

        assert api.sent("POST", f"{TEMPLATES}/bank-reconcile/fit") == []
        [preview] = api.sent("POST", f"{TEMPLATES}/bank-reconcile/preview")
        assert api.body(preview)["matches"] == matches

    def test_a_description_is_read_back_and_waited_for(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", DESCRIBE, {"draft": "d-1", "state": "running"})
            api.answer("GET", f"{DESCRIBE}/d-1", {"draft": "d-1", "state": "running"})
            api.answer(
                "GET",
                f"{DESCRIBE}/d-1",
                {"draft": "d-1", "state": "done", "read_back": {"spec": {"status": "ready"}}},
            )
            drafted = _call(
                "draft_workflow", description="Total sales by region every Monday", dataset_ids=[9]
            )

        [start] = api.sent("POST", DESCRIBE)
        assert api.body(start)["dataset_ids"] == [9]
        assert drafted["state"] == "done"
        assert drafted["read_back"] == {"spec": {"status": "ready"}}

    def test_a_running_draft_is_read_again_by_its_id(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer(
                "GET", f"{DESCRIBE}/d-1", {"draft": "d-1", "state": "failed", "reason": "no"}
            )
            drafted = _call("draft_workflow", draft="d-1")

        assert api.sent("POST", DESCRIBE) == []
        assert drafted["reason"] == "no"

    @pytest.mark.parametrize(
        "arguments",
        [
            {},
            {"template_key": "bank-reconcile"},
            {"template_key": "bank-reconcile", "inputs": {"bank": 9}, "description": "x y z"},
        ],
    )
    def test_one_way_to_draft_is_asked_for(self, arguments: dict[str, object]) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="either"):
            _call("draft_workflow", **arguments)

        assert api.requests == []


def _workflow(status: str) -> dict[str, object]:
    return {"id": 41, "name": "Bank", "canvas_state": {"save_run": {"status": status}}}


class TestBuildWorkflow:
    def test_a_template_build_waits_for_its_save(self) -> None:
        matches = {"bank": {"amount": {"column": "Amount"}}}
        with a_fake_api() as api, as_caller():
            api.answer(
                "POST", f"{TEMPLATES}/bank-reconcile/build", {"workflow": _workflow("running")}
            )
            api.answer("GET", WORKFLOW, _workflow("running"))
            api.answer("GET", WORKFLOW, _workflow("done"))
            built = _call(
                "build_workflow",
                template_key="bank-reconcile",
                inputs={"bank": 9},
                matches=matches,
                destination_name="Reconciled",
                destination_emails=["ops@example.com"],
            )

        [build] = api.sent("POST", f"{TEMPLATES}/bank-reconcile/build")
        assert api.body(build)["destination"] == {
            "name": "Reconciled",
            "emails": ["ops@example.com"],
        }
        assert built["saved"] == "done"
        assert len(api.sent("GET", WORKFLOW)) == 2

    def test_a_described_build_carries_its_spec_and_clock(self) -> None:
        spec = {"status": "ready", "steps": []}
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{DESCRIBE}/build", {"workflow": _workflow("done")})
            built = _call(
                "build_workflow",
                spec=spec,
                destination_name="Weekly sales",
                schedule={"frequency": "weekly", "by_week_day": ["mo"]},
            )

        [build] = api.sent("POST", f"{DESCRIBE}/build")
        assert api.body(build)["spec"] == spec
        assert api.body(build)["schedule"]["frequency"] == "weekly"
        assert built["saved"] == "done"
        assert api.sent("GET", WORKFLOW) == []

    def test_a_save_that_outlasts_the_call_says_it_is_still_running(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(workflows, "_wait_seconds", lambda: 0.0)
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{DESCRIBE}/build", {"workflow": _workflow("running")})
            built = _call("build_workflow", spec={"status": "ready"}, destination_name="Out")

        assert built["saved"] == "running"

    def test_a_template_build_with_a_clock_is_refused(self) -> None:
        with (
            a_fake_api() as api,
            as_caller(),
            pytest.raises(ToolError, match="set_workflow_trigger"),
        ):
            _call(
                "build_workflow",
                template_key="bank-reconcile",
                inputs={"bank": 9},
                matches={"bank": {}},
                destination_name="Out",
                schedule={"frequency": "daily"},
            )

        assert api.requests == []


class TestRunWorkflow:
    def test_a_run_is_started_and_followed_to_its_end(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{WORKFLOW}/run", {"run_id": "r-1", "already_running": False}, 202)
            api.answer("GET", f"{WORKFLOW}/runs", [{"id": "r-1", "result": "running"}])
            api.answer("GET", f"{WORKFLOW}/runs", [{"id": "r-1", "result": "success"}])
            ran = _call("run_workflow", workflow_id=41)

        assert ran["result"] == "success"
        assert ran["run"] == {"id": "r-1", "result": "success"}

    def test_a_run_that_has_not_shown_yet_is_still_running(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(workflows, "_wait_seconds", lambda: 0.0)
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{WORKFLOW}/run", {"run_id": "r-1", "already_running": True}, 202)
            api.answer("GET", f"{WORKFLOW}/runs", [])
            ran = _call("run_workflow", workflow_id=41)

        assert (ran["result"], ran["run"], ran["already_running"]) == ("running", None, True)


class TestSetWorkflowTrigger:
    def test_a_clock_is_set_and_does_not_run_now_unless_asked(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("PUT", f"{WORKFLOW}/schedule", {"automation_id": 5})
            set_ = _call(
                "set_workflow_trigger",
                workflow_id=41,
                kind="schedule",
                frequency="weekly",
                by_week_day=["mo", "fr"],
            )

        [request] = api.sent("PUT", f"{WORKFLOW}/schedule")
        assert api.body(request) == {
            "frequency": "weekly",
            "interval": 1,
            "start_now": False,
            "by_week_day": ["mo", "fr"],
        }
        assert set_ == {"automation_id": 5}

    def test_after_names_the_source_workflow(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("PUT", f"{WORKFLOW}/after", {"automation_id": 6})
            _call("set_workflow_trigger", workflow_id=41, kind="after", source_workflow_id=40)

        [request] = api.sent("PUT", f"{WORKFLOW}/after")
        assert api.body(request) == {"source_workflow_id": 40, "only_when_ok": True}

    def test_a_link_is_made_and_turned_off(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{WORKFLOW}/link", {"automation_id": 7, "secret": "s"})
            api.answer("DELETE", f"{WORKFLOW}/link", {}, 200)
            made = _call("set_workflow_trigger", workflow_id=41, kind="link")
            gone = _call("set_workflow_trigger", workflow_id=41, kind="unlink")

        assert made["secret"] == "s"
        assert gone == {"unlinked": True}

    @pytest.mark.parametrize(
        ("kind", "field"), [("schedule", "frequency"), ("after", "source_workflow_id")]
    )
    def test_a_trigger_without_what_it_needs_is_refused(self, kind: str, field: str) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match=field):
            _call("set_workflow_trigger", workflow_id=41, kind=kind)

        assert api.requests == []


def test_get_workflow_shows_its_save_and_latest_runs() -> None:
    runs = [{"id": f"r-{n}", "result": "success"} for n in range(15)]
    with a_fake_api() as api, as_caller():
        api.answer("GET", WORKFLOW, _workflow("failed"))
        api.answer("GET", f"{WORKFLOW}/runs", runs)
        got = _call("get_workflow", workflow_id=41)

    assert got["saved"] == "failed"
    assert got["runs"] == runs[:10]


def test_list_workflows_wraps_the_list() -> None:
    with a_fake_api() as api, as_caller():
        api.answer("GET", f"{BASE}/workflows", [{"id": 41, "name": "Bank"}])
        listed = _call("list_workflows")

    assert listed == {"workflows": [{"id": 41, "name": "Bank"}]}


class TestCreateWorkflow:
    def test_a_new_workflow_starts_from_a_table(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{BASE}/workflows", {"id": 42, "name": "Ledger"}, 201)
            made = _call("create_workflow", name="Ledger", seed_dataset_id=9)

        [request] = api.sent("POST", f"{BASE}/workflows")
        assert api.body(request) == {"name": "Ledger", "shape": "blank", "seed_datasource_id": 9}
        assert made == {"workflow": {"id": 42, "name": "Ledger"}}

    def test_a_copy_waits_for_its_job_and_names_the_new_workflow(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{BASE}/workflows/duplicate", {"job_id": 77}, 202)
            api.answer(
                "GET", "/jobs/77", {"id": 77, "status": "success", "response": {"workflow_id": 43}}
            )
            copied = _call("create_workflow", name="Copy", copy_of_workflow_id=41, dataset_ids=[9])

        [request] = api.sent("POST", f"{BASE}/workflows/duplicate")
        assert api.body(request) == {"name": "Copy", "dataset_ids": [9], "source_workflow_id": 41}
        assert copied == {"job_id": 77, "status": "done", "workflow_id": 43}

    @pytest.mark.parametrize(
        ("arguments", "said"),
        [({"copy_of_workflow_id": 41}, "dataset_ids"), ({"dataset_ids": [9]}, "copy_of")],
    )
    def test_a_copy_needs_its_tables_and_only_a_copy_takes_them(
        self, arguments: dict[str, object], said: str
    ) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match=said):
            _call("create_workflow", name="X", **arguments)

        assert api.requests == []


def test_delete_workflow_deletes_it() -> None:
    with a_fake_api() as api, as_caller():
        api.answer("DELETE", WORKFLOW, {})
        gone = _call("delete_workflow", workflow_id=41)

    assert len(api.sent("DELETE", WORKFLOW)) == 1
    assert gone == {"deleted": 41}


class TestProposeWorkflowChanges:
    def test_changes_are_sent_as_proposals_and_the_unsaved_changes_come_back(self) -> None:
        change = {"op": "remove_step", "view_id": 5, "task_id": 6}
        pending = [{"key": "k1", "kind": "remove_step"}]
        with a_fake_api() as api, as_caller():
            api.answer(
                "PATCH",
                f"{WORKFLOW}/canvas",
                {"id": 41, "canvas_state": {"pending_changes": pending, "version": 3}},
            )
            proposed = _call("propose_workflow_changes", workflow_id=41, changes=[change])

        [request] = api.sent("PATCH", f"{WORKFLOW}/canvas")
        assert api.body(request) == {"canvas_state": {"proposed_changes": [change]}}
        assert proposed == {"unsaved": pending, "version": 3}

    def test_no_changes_is_refused(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="change"):
            _call("propose_workflow_changes", workflow_id=41, changes=[])

        assert api.requests == []


def _saving(status: str, run_id: str = "s-1") -> dict[str, object]:
    steps = [{"label": "Filter", "status": status}]
    return {
        "id": 41,
        "canvas_state": {"save_run": {"id": run_id, "status": status, "steps": steps}},
    }


class TestSaveWorkflow:
    def test_a_save_builds_the_chosen_changes_and_waits_for_them(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{WORKFLOW}/save", _saving("running"))
            api.answer("GET", WORKFLOW, _saving("done"))
            saved = _call("save_workflow", workflow_id=41, keys=["k1"])

        [request] = api.sent("POST", f"{WORKFLOW}/save")
        assert api.body(request) == {"keys": ["k1"]}
        assert saved["saved"] == "done"
        assert saved["steps"] == [{"label": "Filter", "status": "done"}]

    def test_undo_takes_back_the_latest_save_when_no_run_is_named(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", WORKFLOW, _saving("done", run_id="s-9"))
            api.answer("POST", f"{WORKFLOW}/save/s-9/undo", _saving("done", run_id="u-1"))
            undone = _call("save_workflow", workflow_id=41, action="undo")

        assert len(api.sent("POST", f"{WORKFLOW}/save/s-9/undo")) == 1
        assert undone["saved"] == "done"

    def test_cancel_step_cancels_that_step_of_the_named_run(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{WORKFLOW}/save/s-1/steps/2/cancel", _saving("cancelled"))
            _call("save_workflow", workflow_id=41, action="cancel_step", run_id="s-1", step=2)

        assert len(api.sent("POST", f"{WORKFLOW}/save/s-1/steps/2/cancel")) == 1

    def test_cancel_step_needs_the_step(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="step"):
            _call("save_workflow", workflow_id=41, action="cancel_step", run_id="s-1")

        assert api.requests == []

    def test_undo_without_any_save_says_so(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="no Save"):
            api.answer("GET", WORKFLOW, {"id": 41, "canvas_state": {}})
            _call("save_workflow", workflow_id=41, action="undo")
