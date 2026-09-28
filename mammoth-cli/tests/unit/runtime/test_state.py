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
