"""Unit tests for the automatic write read-back ``state`` block (D-077)."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands import registry
from mammoth_cli.runtime import state as state_mod
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import STATE_SIZE_CAP_BYTES, with_state


def _invocation(command_id: str = "view.transform.filter", **overrides: Any) -> Invocation:
    kwargs: dict[str, Any] = {
        "command_id": command_id,
        "output": "json",
        "profile": "default",
        "project": 10,
        "positionals": {"view_id": 3310},
        "extra_args": ["3310"],
    }
    kwargs.update(overrides)
    return Invocation(**kwargs)


def _patch_record(monkeypatch: pytest.MonkeyPatch, record: dict[str, Any]) -> None:
    monkeypatch.setattr(state_mod, "command_by_id", lambda command_id: record)


def _patch_handlers(monkeypatch: pytest.MonkeyPatch, handlers: dict[str, Any]) -> None:
    monkeypatch.setattr(registry, "HANDLERS", handlers)


def test_non_dict_data_passes_through_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(monkeypatch, {"readback": {"command": "view.get", "ids": {}, "kind": "object"}})
    assert with_state(_invocation(), ["a", "b"]) == ["a", "b"]
    assert with_state(_invocation(), None) is None


def test_no_declaration_yet_returns_data_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(monkeypatch, {})
    data = {"status": "done"}
    assert with_state(_invocation(), data) == data


def test_no_readback_returns_data_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(monkeypatch, {"no_readback": "the object was deleted; nothing left to read"})
    data = {"status": "done"}
    assert with_state(_invocation(), data) == data


def test_kind_object_reads_and_keeps_only_scalar_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {"readback": {"command": "view.get", "ids": {"view_id": "positional.0"}, "kind": "object"}},
    )

    def fake_view_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        assert invocation.extra_args == ["3310"]
        return (
            {
                "id": 3310,
                "name": "Sales",
                "row_count": 42,
                "metadata": [{"internal_name": "c1", "display_name": "Sales", "type": "NUMERIC"}],
            },
            {},
        )

    _patch_handlers(monkeypatch, {"view.get": fake_view_get})
    result = with_state(_invocation(), {"status": "done"})
    assert result["state"] == {
        "kind": "object",
        "read_by": "view.get 3310",
        "object": {"id": 3310, "name": "Sales", "row_count": 42},
    }


def test_kind_delivery_reads_job_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "job.get",
                "ids": {"job_id": "result.job_id"},
                "kind": "delivery",
            }
        },
    )

    def fake_job_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        assert invocation.extra_args == ["7660"]
        return {"status": "done", "message": "delivered"}, {}

    _patch_handlers(monkeypatch, {"job.get": fake_job_get})
    result = with_state(_invocation(), {"job_id": 7660})
    assert result["state"] == {
        "kind": "delivery",
        "read_by": "job.get 7660",
        "status": "done",
        "detail": "delivered",
    }


def test_kind_data_combines_view_get_and_view_data_get(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "view.data.get",
                "ids": {"view_id": "positional.0"},
                "kind": "data",
            }
        },
    )

    def fake_view_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        return (
            {
                "id": 3310,
                "row_count": 113,
                "metadata": [
                    {"internal_name": "c1", "display_name": "petal_width", "type": "NUMERIC"}
                ],
            },
            {},
        )

    def fake_view_data_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        return {"data": [{"petal_width": 1.4}, {"petal_width": 1.5}]}, {}

    _patch_handlers(monkeypatch, {"view.get": fake_view_get, "view.data.get": fake_view_data_get})
    result = with_state(_invocation(), {"status": "done"})
    assert result["state"] == {
        "kind": "data",
        "read_by": "view.data.get 3310",
        "columns": [{"name": "petal_width", "type": "NUMERIC"}],
        "row_count": 113,
        "sample": [{"petal_width": 1.4}, {"petal_width": 1.5}],
    }


def test_kind_data_discovers_view_from_dataset_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "view.data.get",
                "ids": {"dataset_id": "result.dataset_id"},
                "kind": "data",
            }
        },
    )

    def fake_view_list(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        assert invocation.extra_args == ["501"]
        return {"dataviews": [{"id": 91, "name": "Sheet1"}]}, {}

    def fake_view_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        assert invocation.positionals.get("view_id") == 91
        return {"id": 91, "row_count": 5, "metadata": []}, {}

    def fake_view_data_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        return {"data": []}, {}

    _patch_handlers(
        monkeypatch,
        {
            "view.list": fake_view_list,
            "view.get": fake_view_get,
            "view.data.get": fake_view_data_get,
        },
    )
    result = with_state(_invocation(), {"dataset_id": 501})
    assert result["state"]["kind"] == "data"
    assert result["state"]["read_by"] == "view.data.get 91"
    assert result["state"]["row_count"] == 5


def test_unreadable_on_read_failure_never_omits_the_block(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {"readback": {"command": "view.get", "ids": {"view_id": "positional.0"}, "kind": "object"}},
    )

    def fake_view_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        raise RuntimeError("boom: view not found")

    _patch_handlers(monkeypatch, {"view.get": fake_view_get})
    result = with_state(_invocation(), {"status": "done"})
    assert result["state"]["kind"] == "unreadable"
    assert result["state"]["read_by"] == "view.get 3310"
    assert "boom: view not found" in result["state"]["reason"]


def test_unreadable_when_an_id_cannot_be_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "view.get",
                "ids": {"view_id": "result.view_id"},
                "kind": "object",
            }
        },
    )
    result = with_state(_invocation(), {"status": "done"})
    assert result["state"]["kind"] == "unreadable"
    assert "view_id" in result["state"]["reason"]


def test_size_cap_trims_sample_rows_but_keeps_columns_and_row_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "view.data.get",
                "ids": {"view_id": "positional.0"},
                "kind": "data",
            }
        },
    )
    big_row = {f"col_{i}": "x" * 80 for i in range(20)}

    def fake_view_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        return {"id": 3310, "row_count": 999, "metadata": []}, {}

    def fake_view_data_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        return {"data": [dict(big_row) for _ in range(5)]}, {}

    _patch_handlers(monkeypatch, {"view.get": fake_view_get, "view.data.get": fake_view_data_get})
    result = with_state(_invocation(), {"status": "done"})
    state = result["state"]
    assert state["row_count"] == 999
    assert len(state["sample"]) < 5
    assert len(state["sample"]) >= 0
    import json

    assert len(json.dumps(state)) <= STATE_SIZE_CAP_BYTES


def test_write_still_processing_reports_delivery_not_stale_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "view.data.get",
                "ids": {"view_id": "positional.0"},
                "kind": "data",
            }
        },
    )

    def must_not_read(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        raise AssertionError("an unfinished write must not be read back as its new state")

    _patch_handlers(monkeypatch, {"view.get": must_not_read, "view.data.get": must_not_read})
    data = {
        "status": "processing",
        "verify": {"verified": False, "state": "processing", "reason": "accepted, not finished"},
    }
    assert with_state(_invocation(), data)["state"] == {
        "kind": "delivery",
        "read_by": "verify",
        "status": "processing",
        "detail": "accepted, not finished",
    }


def test_truncated_listing_says_how_many_items_it_held(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "view.list",
                "ids": {"dataset_id": "input.dataset_id"},
                "kind": "object",
            }
        },
    )
    views = [{"id": n, "name": "v" * 60} for n in range(80)]
    _patch_handlers(monkeypatch, {"view.list": lambda invocation: ({"dataviews": views}, {})})
    invocation = _invocation(positionals={}, extra_args=[])
    object.__setattr__(invocation, "_prepared_input", {"dataset_id": 7})
    state = with_state(invocation, {"status": "done"})["state"]
    assert len(state["object"]) < 80
    assert state["object_total"] == 80


def test_id_source_alternatives_take_the_first_that_resolves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_record(
        monkeypatch,
        {
            "readback": {
                "command": "job.get",
                "ids": {"job_id": "result.future_id|result.job.id"},
                "kind": "delivery",
            }
        },
    )

    def fake_job_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        assert invocation.extra_args == ["7660"]
        return {"id": 7660, "status": "success"}, {}

    _patch_handlers(monkeypatch, {"job.get": fake_job_get})
    state = with_state(_invocation(), {"job": {"id": 7660, "status": "processing"}})["state"]
    assert state["read_by"] == "job.get 7660"
    assert state["status"] == "success"


_DATA_READBACK = {
    "readback": {"command": "view.data.get", "ids": {"view_id": "positional.0"}, "kind": "data"}
}
_NOT_RUN_YET = (
    "The Mammoth job failed: Failed to retrieve the latest data item from dataview - "
    "Additional Info: no data for pipeline step 1 of dataview 3310 yet; the step is 'added'"
)


def _view_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "id": 3310,
            "row_count": 20,
            "metadata": [{"internal_name": "c1", "display_name": "status", "type": "TEXT"}],
        },
        {},
    )


def test_a_staged_draft_step_reports_the_staged_steps_not_unreadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # FB-20: a step staged in a draft never ran, so reading its data fails;
    # the agent got "unreadable" and polled four read commands to learn what
    # was staged.
    _patch_record(monkeypatch, _DATA_READBACK)

    def fake_task_list(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        assert invocation.extra_args == ["3310"]
        return (
            {
                "tasks": [
                    {"id": 1, "params": {"TASK_KEY": "SELECT"}, "status": "executed"},
                    {"id": 2, "params": {"TASK_KEY": "MATH"}, "status": "added"},
                ]
            },
            {},
        )

    def no_data_read(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        raise AssertionError("a staged step has no data to read")

    _patch_handlers(
        monkeypatch,
        {"view.get": _view_get, "view.task.list": fake_task_list, "view.data.get": no_data_read},
    )

    result = with_state(_invocation(), {"status": "staged", "message": "staged, not run"})

    assert result["state"] == {
        "kind": "staged",
        "read_by": "view.task.list 3310",
        "detail": "Staged in the draft, not run: the live view is unchanged until "
        "'view draft submit'.",
        "live_row_count": 20,
        "steps": [
            {"id": 1, "task": "SELECT", "status": "executed"},
            {"id": 2, "task": "MATH", "status": "added"},
        ],
    }


def test_a_live_read_back_waits_for_the_new_step_to_have_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # FB-18/FB-22: read right after the write, the new step had no data yet,
    # the read-back said "unreadable", and the agent re-read the view itself.
    _patch_record(monkeypatch, _DATA_READBACK)
    monkeypatch.setattr(state_mod.time, "sleep", lambda seconds: None)
    reads = {"n": 0}

    def fake_view_data_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        reads["n"] += 1
        if reads["n"] < 3:
            raise state_mod.CliError(code="job_failed", message=_NOT_RUN_YET)
        return {"data": [{"status": "Shipped"}]}, {}

    _patch_handlers(monkeypatch, {"view.get": _view_get, "view.data.get": fake_view_data_get})

    result = with_state(_invocation(), {"status": "done"})

    assert result["state"]["kind"] == "data"
    assert result["state"]["sample"] == [{"status": "Shipped"}]
    assert reads["n"] == 3


def test_a_read_back_that_never_gets_data_is_still_unreadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_record(monkeypatch, _DATA_READBACK)
    monkeypatch.setattr(state_mod.time, "sleep", lambda seconds: None)

    def fake_view_data_get(invocation: Invocation) -> tuple[dict[str, Any], dict[str, Any]]:
        raise state_mod.CliError(code="job_failed", message=_NOT_RUN_YET)

    _patch_handlers(monkeypatch, {"view.get": _view_get, "view.data.get": fake_view_data_get})

    result = with_state(_invocation(), {"status": "done"})

    assert result["state"]["kind"] == "unreadable"
    assert "no data for pipeline step" in result["state"]["reason"]
