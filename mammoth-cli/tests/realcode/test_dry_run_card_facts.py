"""``--dry-run`` states the facts an approval card shows, so the card renders and never decides.

Real-code: argv through the real handler, service and client, with only the HTTP
socket faked. Three facts: a dry run is a pending preview (nothing ran); an export
into a NEW dataset says it creates one, what it leaves out and that it stays on the
view; a draft submit lists every pending step and which of them another session staged.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]

PROJECT = 180
DATASET = 55
VIEW = 3062
_COLUMNS = [
    {"display_name": "Donor", "internal_name": "col_a", "type": "TEXT"},
    {"display_name": "Gift", "internal_name": "col_b", "type": "NUMERIC"},
    {"display_name": "Notes", "internal_name": "col_c", "type": "TEXT"},
]


def _dry_run(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    argv: list[str],
    routes: Callable[[Any], None],
) -> dict[str, Any]:
    service, api = real_service(project_id=PROJECT)
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=PROJECT)[0],
    )
    routes(api)
    result = make_runner().invoke(
        [*argv, "--project", str(PROJECT), "--dry-run", "--output", "json", "--no-input"]
    )
    envelope: dict[str, Any] = json.loads(result.output)
    assert "error" not in envelope, envelope
    data: dict[str, Any] = envelope["data"]
    return data


def _view_routes(display_properties: dict[str, Any]) -> Callable[[Any], None]:
    def routes(api: Any) -> None:
        api.on(
            "GET",
            rf"/datasets/{DATASET}/dataviews/{VIEW}$",
            body={
                "id": VIEW,
                "name": "Donations",
                "row_count": 3,
                "metadata": _COLUMNS,
                "display_properties": display_properties,
            },
        )

    return routes


def _export(name: str | None) -> list[str]:
    document: dict[str, Any] = {"dataset_id": DATASET}
    if name is not None:
        document["dataset_name"] = name
    return ["view", "export", "dataset", str(VIEW), "--input", json.dumps(document)]


def test_a_dry_run_says_it_is_pending_and_nothing_ran(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data = _dry_run(monkeypatch, real_service, _export("Snapshot"), _view_routes({}))

    assert data["ran"] is False
    assert data["pending"] is True
    assert "approve" in data["hint"] and "cancel" in data["hint"]


def test_an_export_into_a_new_dataset_says_what_it_creates_and_leaves_out(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data = _dry_run(
        monkeypatch,
        real_service,
        _export("Snapshot"),
        _view_routes({"HIDDEN_COLUMNS": ["col_c"]}),
    )

    assert data["creates_dataset"] is True
    assert data["new_dataset_name"] == "Snapshot"
    assert data["hidden_columns_left_out"] == ["Notes"]
    assert data["standing_export"] is True


def test_an_unnamed_new_dataset_export_names_the_product_default(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data = _dry_run(monkeypatch, real_service, _export(None), _view_routes({}))

    assert data["new_dataset_name"] == "Result Dataset"
    assert data["hidden_columns_left_out"] == []


def _draft_routes(
    tasks: list[dict[str, Any]], actions: list[dict[str, Any]]
) -> Callable[[Any], None]:
    def routes(api: Any) -> None:
        _view_routes({})(api)
        api.on(
            "GET",
            rf"/resources/dataview/{VIEW}$",
            body={"resource": {"object_id": VIEW, "dataset": {"id": DATASET, "name": "ds"}}},
        )
        api.on(
            "GET",
            r"/pipeline$",
            body={"state": "ready", "in_draft_mode": True, "draft": "dirty"},
        )
        api.on("GET", r"/tasks$", body={"tasks": tasks})
        api.on("GET", r"/agents/sessions/chat-1/actions$", body={"actions": actions})

    return routes


_SUBMIT = ["view", "draft", "submit", str(VIEW), "--input", json.dumps({"dataset_id": DATASET})]
_TASKS = [
    {
        "id": 1,
        "sequence": 1,
        "status": "added",
        "params": {"REPLACE": {}},
        "created_at": "2026-10-07T09:00:00",
        "updated_at": None,
    },
    {
        "id": 2,
        "sequence": 2,
        "status": "executed",
        "params": {"SELECT": {}},
        "created_at": "2026-10-07T09:30:00",
        "updated_at": None,
    },
    {
        "id": 3,
        "sequence": 3,
        "status": "edited",
        "params": {"SELECT": {}},
        "created_at": "2026-10-07T09:05:00",
        "updated_at": "2026-10-07T11:00:00",
    },
]


def test_a_draft_submit_lists_every_pending_step_and_who_staged_it(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    # This session first wrote to the view at 10:00: step 1 (09:00) is older, step 3 was
    # last touched at 11:00 by the session itself. Step 2 is already applied.
    wrote = [
        {"kind": "view", "object_id": VIEW, "created_at": "2026-10-07T10:00:00"},
        {"kind": "view", "object_id": 999, "created_at": "2026-10-07T08:00:00"},
    ]
    data = _dry_run(
        monkeypatch,
        real_service,
        _SUBMIT + ["--session", "chat-1"],
        _draft_routes(_TASKS, wrote),
    )

    steps = data["pending_draft_steps"]
    assert [(s["sequence"], s["name"], s["staged_by_other"]) for s in steps] == [
        (1, "Replace", True),
        (3, "Select", False),
    ]
    assert steps[0]["created_at"] == "2026-10-07T09:00:00"


def test_a_draft_submit_without_a_session_lists_steps_without_claiming_who_staged_them(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data = _dry_run(
        monkeypatch,
        real_service,
        _SUBMIT,
        _draft_routes(_TASKS, []),
    )

    steps = data["pending_draft_steps"]
    assert [s["sequence"] for s in steps] == [1, 3]
    assert all("staged_by_other" not in s for s in steps)
