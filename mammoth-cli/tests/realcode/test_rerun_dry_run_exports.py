"""``view pipeline rerun`` names the exports it fires, and its dry run the columns they blank.

Real-code: argv through the real handler, service and SDK client, with only the HTTP
socket faked. A rerun re-sends every end-of-pipeline export to its destination, so
the dry run (the confirmation gate's input) must say which exports those are, and for
an append into an existing dataset which destination columns the write leaves NULL.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]
DATASET, VIEW, TARGET = 55, 3062, 77
_SOURCE = {
    "id": VIEW,
    "name": "Fundraising",
    "row_count": 50,
    "metadata": [
        {"display_name": "Donor", "internal_name": "col_a", "type": "TEXT"},
        {"display_name": "Gift", "internal_name": "col_b", "type": "NUMERIC"},
    ],
}


def _internal_export(export_id: int, mode: str, **properties: Any) -> dict[str, Any]:
    return {
        "id": export_id,
        "handler_type": "internal_dataset",
        "end_of_pipeline": True,
        "target_properties": {"TARGET_DS_ID": TARGET, "SAVE_AS_DS_MODE": mode, **properties},
    }


def _target_schema(*names: str) -> dict[str, Any]:
    columns = [{"c_id": f"column_{i}", "c_name": n, "c_type": "text"} for i, n in enumerate(names)]
    return {"dataset": {"data_schema": columns}}


def _rerun(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    exports: list[dict[str, Any]],
    *,
    dry_run: bool,
    target_columns: tuple[str, ...] = ("Donor", "Gift"),
) -> tuple[Any, Any]:
    service, api = real_service(project_id=180)
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", body=_SOURCE)
    api.on(
        "GET",
        r"/pipeline/exports$",
        body={"limit": 50, "offset": 0, "next": "", "exports": exports},
    )
    api.on("GET", rf"/datasets/{TARGET}$", body=_target_schema(*target_columns))
    api.on("GET", r"/pipeline$", body={"state": "ready", "execution_state": "ready"})
    api.on("POST", r"/pipeline/rerun$", body={"status": "processing", "future_id": 9})
    api.on("GET", r"/jobs/9$", body={"id": 9, "status": "success", "response": {}})
    argv = ["view", "pipeline", "rerun", str(VIEW), "--project", "180"]
    argv += ["--input", json.dumps({"dataset_id": DATASET}), "--output", "json", "--no-input"]
    argv += ["--dry-run"] if dry_run else ["--yes"]
    return make_runner().invoke(argv), api


def _fired(result: Any) -> list[dict[str, Any]]:
    payload = json.loads(result.output)
    assert "error" not in payload, result.output
    record = payload["data"]
    return record["exports_fired"]


def test_dry_run_names_the_destination_columns_an_append_leaves_blank(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    exports = [_internal_export(11, "APPEND_TO_DS")]
    result, api = _rerun(
        monkeypatch, real_service, exports, dry_run=True, target_columns=("Donor", "Gift", "Notes")
    )

    (fired,) = _fired(result)
    assert fired["export_id"] == 11
    assert fired["handler_type"] == "internal_dataset"
    assert fired["blank_columns"] == ["Notes"]
    assert fired["target"] == {"TARGET_DS_ID": TARGET, "SAVE_AS_DS_MODE": "APPEND_TO_DS"}
    assert not [r for r in api.requests if r.method == "POST" and r.path.endswith("/rerun")]


def test_a_mapped_destination_column_is_not_reported_blank(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    exports = [_internal_export(11, "REPLACE_IN_DS", COLUMN_MAPPING={"Gift": "Amount"})]
    result, _ = _rerun(
        monkeypatch,
        real_service,
        exports,
        dry_run=True,
        target_columns=("Donor", "Amount", "Notes", "Region"),
    )

    assert _fired(result)[0]["blank_columns"] == ["Notes", "Region"]


def test_an_append_that_fills_every_destination_column_reports_none_blank(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, _ = _rerun(
        monkeypatch, real_service, [_internal_export(11, "APPEND_TO_DS")], dry_run=True
    )

    assert _fired(result)[0]["blank_columns"] == []


def test_an_export_that_creates_a_new_dataset_or_leaves_the_workspace_has_no_blank_columns(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    exports = [
        _internal_export(11, "CREATE_NEW_DS"),
        {
            "id": 12,
            "handler_type": "postgres",
            "target_properties": {"host": "db.example", "table": "gifts", "password": "hunter2"},
        },
    ]
    result, api = _rerun(monkeypatch, real_service, exports, dry_run=True)

    new_dataset, database = _fired(result)
    assert "blank_columns" not in new_dataset and "blank_columns" not in database
    assert database["target"] == {"host": "db.example", "table": "gifts"}
    assert not [r for r in api.requests if r.path.endswith(f"/datasets/{TARGET}")]


def test_a_dry_run_leaves_out_a_deleted_export(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    exports = [
        {**_internal_export(11, "APPEND_TO_DS"), "status": "deleted"},
        _internal_export(12, "APPEND_TO_DS"),
    ]
    result, _ = _rerun(monkeypatch, real_service, exports, dry_run=True)

    assert [e["export_id"] for e in _fired(result)] == [12]
