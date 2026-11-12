"""Workflow automation clients: triggers, describe, editing calls and template fits.

The loopback server records each request; nothing here reaches a real server.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from mammoth.api import workflow_describe, workflow_triggers, workflows
from mammoth.client import SUB_CLIENTS, MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

_PROJ = "/workspaces/1/projects/25654"
_WF = f"{_PROJ}/workflows/41"
_DESCRIBE = f"{_PROJ}/workflows/describe"


def _routes(server: RecordingServer) -> list[tuple[Any, Any]]:
    return [(r["method"], r["path"]) for r in server.requests]


def test_triggers_and_describe_are_sub_clients() -> None:
    assert SUB_CLIENTS["workflow_triggers"][1] == "WorkflowTriggersAPI"
    assert SUB_CLIENTS["workflow_describe"][1] == "WorkflowDescribeAPI"


# --- triggers ---------------------------------------------------------------------------


async def test_run_posts_once_and_returns_the_run_without_waiting(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {_WF}/run"] = (202, {"run_id": "r-1", "already_running": False})
    assert await client.workflow_triggers.run(41) == {"run_id": "r-1", "already_running": False}
    assert _routes(server) == [("POST", f"{_WF}/run")]


async def test_run_with_wait_reads_recent_runs_until_the_run_ends(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {_WF}/run"] = (202, {"run_id": "r-1", "already_running": True})
    server.answers[f"GET {_WF}/runs"] = [
        {"id": "r-2", "result": "running"},
        {"id": "r-1", "result": "success", "rows_out": 12},
    ]
    done = await client.workflow_triggers.run(41, wait=True, timeout=5)
    assert done["result"] == "success"
    assert done["run"]["rows_out"] == 12
    assert done["already_running"] is True
    assert _routes(server) == [("POST", f"{_WF}/run"), ("GET", f"{_WF}/runs")]


async def test_a_wait_that_ends_first_says_running(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {_WF}/run"] = (202, {"run_id": "r-9", "already_running": False})
    server.answers[f"GET {_WF}/runs"] = []
    done = await client.workflow_triggers.run(41, wait=True, timeout=0)
    assert (done["run"], done["result"]) == (None, "running")


@pytest.mark.parametrize("timeout", [-1, True, "5"])
async def test_run_refuses_a_bad_wait_before_it_starts_a_run(
    server: RecordingServer, client: MammothClient, timeout: Any  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.workflow_triggers.run(41, wait=True, timeout=timeout)
    assert server.requests == []


async def test_triggers_and_workflows_refuse_a_bad_id_with_the_same_message(
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError) as from_triggers:
        await client.workflow_triggers.run(0)
    with pytest.raises(MammothValidationError) as from_workflows:
        await client.workflows.holds_check(0)
    assert str(from_triggers.value) == str(from_workflows.value)


async def test_wait_for_run_polls_until_the_row_is_no_longer_running(
    client: MammothClient, monkeypatch: pytest.MonkeyPatch  # noqa: F811
) -> None:
    pages = iter(
        [
            {"runs": []},
            {"runs": [{"id": "r-1", "result": "running"}]},
            {"runs": [{"id": "r-1", "result": "failure", "reason": "boom"}]},
        ]
    )

    async def runs(workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        return next(pages)

    monkeypatch.setattr(workflow_triggers, "_POLL_SECONDS", 0.0)
    monkeypatch.setattr(client.workflow_triggers, "runs", runs)
    row = await client.workflow_triggers.wait_for_run(41, "r-1", timeout=5)
    assert row == {"id": "r-1", "result": "failure", "reason": "boom"}


def _saving(status: str) -> dict[str, Any]:
    return {"id": 41, "canvas_state": {"save_run": {"status": status}}}


async def test_wait_for_save_reads_the_workflow_until_its_save_ends(
    client: MammothClient, monkeypatch: pytest.MonkeyPatch  # noqa: F811
) -> None:
    reads = iter([_saving("running"), _saving("partial")])

    async def get(workflow_id: int, project_id: int | None = None) -> dict[str, Any]:
        return next(reads)

    monkeypatch.setattr(workflows, "_SAVE_POLL_SECONDS", 0.0)
    monkeypatch.setattr(client.workflows, "get", get)
    done = await client.workflows.wait_for_save(41, workflow=_saving("running"), timeout=5)
    assert workflows.save_run(done) == {"status": "partial"}
    assert next(reads, None) is None


async def test_wait_for_save_returns_a_finished_record_without_a_read(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    done = await client.workflows.wait_for_save(41, workflow=_saving("done"), timeout=5)
    assert done == _saving("done")
    assert server.requests == []


async def test_wait_for_save_reads_first_when_given_no_record_and_says_running_at_timeout(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {_WF}"] = _saving("running")
    done = await client.workflows.wait_for_save(41, timeout=0)
    assert workflows.save_is_running(done)
    assert _routes(server) == [("GET", _WF)]


@pytest.mark.parametrize("timeout", [-1, True, "5"])
async def test_wait_for_save_refuses_a_bad_timeout(
    client: MammothClient, timeout: Any  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.workflows.wait_for_save(41, timeout=timeout)


def test_save_run_reads_only_a_mapping() -> None:
    assert workflows.save_run({"canvas_state": {"save_run": "x"}}) is None
    assert workflows.save_run(None) is None
    assert not workflows.save_is_running({"canvas_state": {}})


async def test_schedule_after_and_link_use_their_routes(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    api = client.workflow_triggers
    server.answers[f"GET {_WF}/runs"] = [{"id": "r-1"}]
    await api.schedule_set(41, "weekly", by_week_day=["mo", "th"], start_at="2026-11-10T07:00:00Z")
    await api.after_set(41, 40, only_when_ok=False)
    await api.after_loops(41)
    await api.link_create(41)
    await api.link_remove(41)
    assert await api.runs(41) == {"runs": [{"id": "r-1"}]}
    assert _routes(server) == [
        ("PUT", f"{_WF}/schedule"),
        ("PUT", f"{_WF}/after"),
        ("GET", f"{_WF}/after"),
        ("POST", f"{_WF}/link"),
        ("DELETE", f"{_WF}/link"),
        ("GET", f"{_WF}/runs"),
    ]
    schedule, after = server.requests[0]["body"], server.requests[1]["body"]
    assert schedule == {
        "frequency": "weekly",
        "interval": 1,
        "start_now": True,
        "by_week_day": ["mo", "th"],
        "start_at": "2026-11-10T07:00:00Z",
    }
    assert after == {"source_workflow_id": 40, "only_when_ok": False}


async def test_project_id_overrides_the_client_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workflow_triggers.link_create(41, project_id=7)
    assert server.requests[0]["path"] == "/workspaces/1/projects/7/workflows/41/link"


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.run(0),
        lambda api: api.run(True),
        lambda api: api.run(41, project_id=0),
        lambda api: api.wait_for_run(41, "r-1", timeout=-1),
        lambda api: api.schedule_set(41, "yearly"),
        lambda api: api.schedule_set(41, "daily", interval=0),
        lambda api: api.schedule_set(41, "daily", interval=367),
        lambda api: api.schedule_set(41, "weekly", by_week_day=["monday"]),
        lambda api: api.schedule_set(41, "monthly", by_month_day=[32]),
        lambda api: api.after_set(41, 0),
    ],
)
async def test_bad_trigger_input_is_refused_before_any_request(
    server: RecordingServer, client: MammothClient, call: Callable[[Any], Any]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await call(client.workflow_triggers)
    assert server.requests == []


# --- describe ---------------------------------------------------------------------------


async def test_describe_without_wait_starts_a_draft(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {_DESCRIBE}"] = (202, {"draft": "d-1", "state": "running"})
    started = await client.workflow_describe.describe(
        "  Match payouts to the bank feed ", dataset_ids=[812, 815], wait=False
    )
    assert started == {"draft": "d-1", "state": "running"}
    assert server.requests[0]["body"] == {
        "text": "Match payouts to the bank feed",
        "dataset_ids": [812, 815],
    }


async def test_describe_waits_for_the_read_back(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {_DESCRIBE}"] = (202, {"draft": "d/1", "state": "running"})
    server.answers[f"GET {_DESCRIBE}/d%2F1"] = {"draft": "d/1", "state": "done", "read_back": {}}
    state = await client.workflow_describe.describe("Match payouts", timeout=5)
    assert state["state"] == "done"
    assert _routes(server) == [("POST", _DESCRIBE), ("GET", f"{_DESCRIBE}/d%2F1")]


async def test_wait_polls_until_the_draft_is_not_running(
    client: MammothClient, monkeypatch: pytest.MonkeyPatch  # noqa: F811
) -> None:
    states = iter([{"state": "running"}, {"state": "failed", "reason": "timeout"}])

    async def draft(draft: str, project_id: int | None = None) -> dict[str, Any]:
        return next(states)

    monkeypatch.setattr(workflow_describe, "_POLL_SECONDS", 0.0)
    monkeypatch.setattr(client.workflow_describe, "draft", draft)
    assert await client.workflow_describe.wait("d-1", timeout=5) == {
        "state": "failed",
        "reason": "timeout",
    }


async def test_check_build_and_fed_by_use_their_routes(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    api = client.workflow_describe
    spec = {"sentence": "Match payouts", "status": "ready"}
    await api.check(spec, samples=["s-1"])
    await api.build(
        spec,
        " Payout matches ",
        destination_emails=["a@b.c"],
        schedule={"frequency": "daily"},
    )
    await api.fed_by(77)
    assert _routes(server) == [
        ("POST", f"{_DESCRIBE}/check"),
        ("POST", f"{_DESCRIBE}/build"),
        ("GET", f"{_DESCRIBE}/fed-by/77"),
    ]
    assert server.requests[0]["body"] == {"spec": spec, "samples": ["s-1"]}
    assert server.requests[1]["body"] == {
        "spec": spec,
        "destination": {"name": "Payout matches", "emails": ["a@b.c"]},
        "schedule": {"frequency": "daily", "interval": 1, "start_now": True},
    }


async def test_keep_sample_uploads_the_file(
    server: RecordingServer, client: MammothClient, tmp_path: Any  # noqa: F811
) -> None:
    receipt = tmp_path / "receipt.pdf"
    receipt.write_bytes(b"%PDF-1.4")
    await client.workflow_describe.keep_sample(receipt)
    assert _routes(server) == [("POST", f"{_DESCRIBE}/samples")]


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.start("hi"),
        lambda api: api.start("x" * 2001),
        lambda api: api.start("Match payouts", dataset_ids=list(range(1, 12))),
        lambda api: api.start("Match payouts", dataset_ids=[0]),
        lambda api: api.draft(" "),
        lambda api: api.wait("d-1", timeout=-1),
        lambda api: api.check({}),
        lambda api: api.build({"a": 1}, ""),
        lambda api: api.build({"a": 1}, "x" * 121),
        lambda api: api.build({"a": 1}, "Out", schedule={"frequency": "yearly"}),
        lambda api: api.keep_sample("/no/such/file.pdf"),
        lambda api: api.fed_by(0),
    ],
)
async def test_bad_describe_input_is_refused_before_any_request(
    server: RecordingServer, client: MammothClient, call: Callable[[Any], Any]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await call(client.workflow_describe)
    assert server.requests == []


# --- editing ----------------------------------------------------------------------------


async def test_editing_calls_use_their_routes_and_queries(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    api = client.workflows
    await api.step_lines(41, [3, 2], match_keys=True)
    await api.repeat_counts()
    await api.before_after(41, ["k1", "k2"])
    await api.view_values(41, 3, "Region", "West")
    await api.holds_check(41)
    await api.sentence_read(41, "Keep paid rows", answers=[{"question": "q", "answer": "a"}])
    await api.sentence_ask_dismiss(41)
    await api.swap_fit(41, 3, [9])
    await api.swap(41, 3, 9, picks={"Amount": "Total"})
    await api.swap_cancel(41)
    await api.swap_undo(41)
    assert _routes(server) == [
        ("GET", f"{_WF}/step-lines"),
        ("GET", f"{_PROJ}/workflows/repeat-counts"),
        ("GET", f"{_WF}/before-after"),
        ("GET", f"{_WF}/views/3/values"),
        ("POST", f"{_WF}/holds/check"),
        ("POST", f"{_WF}/sentence"),
        ("DELETE", f"{_WF}/sentence/ask"),
        ("POST", f"{_WF}/swap/fit"),
        ("POST", f"{_WF}/swap"),
        ("DELETE", f"{_WF}/swap"),
        ("POST", f"{_WF}/swap/undo"),
    ]
    queries = [r["query"] for r in server.requests[:4]]
    assert queries == [
        {"view_ids": "3,2", "match_keys": "true"},
        {},
        {"keys": "k1,k2"},
        {"column": "Region", "text": "West"},
    ]
    assert server.requests[5]["body"] == {
        "text": "Keep paid rows",
        "answers": [{"question": "q", "answer": "a"}],
    }
    assert server.requests[7]["body"] == {"view_id": 3, "dataset_ids": [9]}
    assert server.requests[8]["body"] == {
        "view_id": 3,
        "dataset_id": 9,
        "picks": {"Amount": "Total"},
    }


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.step_lines(41, []),
        lambda api: api.step_lines(0, [3]),
        lambda api: api.before_after(41, []),
        lambda api: api.view_values(41, 0, "Region", "West"),
        lambda api: api.view_values(41, 3, "", "West"),
        lambda api: api.sentence_read(41, " "),
        lambda api: api.swap_fit(41, 3, list(range(1, 202))),
        lambda api: api.swap(41, 3, 0),
        lambda api: api.repeat_counts(project_id=0),
    ],
)
async def test_bad_editing_input_is_refused_before_any_request(
    server: RecordingServer, client: MammothClient, call: Callable[[Any], Any]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await call(client.workflows)
    assert server.requests == []


# --- template fits and workflow pages ---------------------------------------------------


async def test_fits_wraps_the_bare_array_and_start_page_uses_the_pages_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    fit = {"key": "bank-reconciliation", "sure": True, "tables": {"main": 4}}
    server.answers[f"POST {_PROJ}/workflow-templates/fits"] = [fit]
    api = client.workflow_templates
    assert await api.fits([4, 5], focus=4) == {"fits": [fit]}
    await api.fits()
    await api.start_page("stripe-payouts")
    assert _routes(server) == [
        ("POST", f"{_PROJ}/workflow-templates/fits"),
        ("POST", f"{_PROJ}/workflow-templates/fits"),
        ("POST", f"{_PROJ}/workflow-pages/stripe-payouts/start"),
    ]
    assert server.requests[0]["body"] == {"dataset_ids": [4, 5], "focus": 4}
    assert server.requests[1]["body"] == {}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.fits([0]),
        lambda api: api.fits(list(range(1, 202))),
        lambda api: api.fits(focus=0),
        lambda api: api.start_page(" "),
    ],
)
async def test_bad_fits_input_is_refused_before_any_request(
    server: RecordingServer, client: MammothClient, call: Callable[[Any], Any]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await call(client.workflow_templates)
    assert server.requests == []
