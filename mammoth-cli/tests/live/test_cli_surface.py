"""Live: commands whose routing, confirmation and read-back the old fake socket scripted.

Replaces the fake-socket realcode tests ``test_end_to_end_cli`` (all but the data-app and
dashboard-generation cases that need a data app or a paid board), ``test_explore_panel_open_cards``,
``test_explore_panel_set_readback``, ``test_job_wait_outcome`` and ``test_token_revoke_own_grant``
(the failed-call case). Everything is created in the module's scratch project and removed again.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


# -- project ---------------------------------------------------------------


def test_project_list_reaches_the_api_and_names_the_scratch_project(
    live_cli: LiveCli, scratch_project: int
) -> None:
    data, _ = live_cli.ok("project", "list")

    assert scratch_project in [p["id"] for p in data["projects"]]


def test_a_leaf_with_a_positional_keeps_parsing_the_options_after_it(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    """``project resource-dependencies 3 --input ...``: ``3`` is an id, not a subcommand."""
    data, _ = live_cli.ok(
        "project",
        "resource-dependencies",
        str(sales_data.project),
        *_input({"resource_ids": [sales_data.dataset]}),
    )

    assert isinstance(data, dict)


# -- delete confirmation and parent ----------------------------------------


@pytest.fixture
def spare_view(live_cli: LiveCli, sales_data: SalesData) -> Iterator[int]:
    created, _ = live_cli.ok(
        "view", "create", str(sales_data.dataset), "--yes", project=sales_data.project
    )
    view = int(created["id"])
    yield view
    live_cli.run(
        *("view", "delete", str(view), "--yes", "--confirm", str(view)),
        *_input({"dataset_id": sales_data.dataset}),
        project=sales_data.project,
    )


def _view_ids(live_cli: LiveCli, sales_data: SalesData) -> list[int]:
    listed, _ = live_cli.ok("view", "list", str(sales_data.dataset), project=sales_data.project)
    return [int(v["id"]) for v in listed["dataviews"]]


def test_view_delete_names_its_parent_and_a_wrong_parent_deletes_nothing(
    live_cli: LiveCli, sales_data: SalesData, spare_view: int
) -> None:
    wrong = live_cli.run(
        *("view", "delete", str(spare_view), str(sales_data.dataset + 1), "--yes"),
        *("--confirm", str(spare_view)),
        project=sales_data.project,
    )
    assert "error" in wrong, wrong
    assert spare_view in _view_ids(live_cli, sales_data)

    live_cli.ok(
        *("view", "delete", str(spare_view), str(sales_data.dataset), "--yes"),
        *("--confirm", str(spare_view)),
        project=sales_data.project,
    )
    assert spare_view not in _view_ids(live_cli, sales_data)


# -- folders ---------------------------------------------------------------


@pytest.fixture
def folder(live_cli: LiveCli, scratch_project: int) -> Iterator[int]:
    created, _ = live_cli.ok("folder", "create", "live folder", "--yes", project=scratch_project)
    folder_id = int(created.get("id") or created["folder"]["id"])
    yield folder_id
    live_cli.run("folder", "delete", str(folder_id), "--yes", project=scratch_project)


def _folder_ids(live_cli: LiveCli, project: int) -> list[int]:
    listed, _ = live_cli.ok("folder", "list", project=project)
    return [int(f["id"]) for f in listed.get("folders", listed if isinstance(listed, list) else [])]


def test_folder_delete_takes_the_id_as_a_positional(
    live_cli: LiveCli, scratch_project: int, folder: int
) -> None:
    assert folder in _folder_ids(live_cli, scratch_project)

    live_cli.ok("folder", "delete", str(folder), "--yes", project=scratch_project)

    assert folder not in _folder_ids(live_cli, scratch_project)


# -- automation ------------------------------------------------------------


def test_automation_create_keeps_the_task_spec_it_was_given(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    scratch_project = sales_data.project
    task = {
        "task_type": "send_an_alert",
        "details": {
            "alert_type": "email",
            "recipients": ["ops@example.com"],
            "subject": "Nightly run finished",
            "attachments": {"dataview_ids": [sales_data.view]},
        },
    }
    body = {"description": "d", "tasks": [task], "condition_mode": "and"}
    created, _ = live_cli.ok(
        "automation", "create", "Nightly", *_input(body), "--yes", project=scratch_project
    )
    automation = int(created.get("id") or created["automation"]["id"])
    try:
        got, _ = live_cli.ok("automation", "get", str(automation), project=scratch_project)
        read = got.get("automation", got)
    finally:
        live_cli.run("automation", "delete", str(automation), "--yes", project=scratch_project)

    assert read["name"] == "Nightly"
    assert read["tasks"][0]["task_type"] == "send_an_alert"
    assert read["tasks"][0]["details"]["recipients"] == ["ops@example.com"]


# -- dashboard contexts ----------------------------------------------------


def _context_ids(live_cli: LiveCli) -> list[str]:
    listed, _ = live_cli.ok("dashboard", "context", "list")
    return [str(c["id"]) for c in listed["contexts"]]


def test_a_context_is_created_and_deleting_it_needs_confirmation(live_cli: LiveCli) -> None:
    body = {"body": {"params": {"name": f"uqa-live-context-{int(time.time())}", "type": "analyst"}}}
    created, _ = live_cli.ok("dashboard", "context", "create", *_input(body))
    context = str(created.get("id") or created["context"]["id"])
    try:
        assert context in _context_ids(live_cli)
        refused = live_cli.run("dashboard", "context", "delete", context)
        assert "error" in refused and context in _context_ids(live_cli)
    finally:
        live_cli.run("dashboard", "context", "delete", context, "--yes")

    assert context not in _context_ids(live_cli)


# -- data-app --------------------------------------------------------------


def test_data_app_user_remove_rejects_the_email_as_an_input_field(live_cli: LiveCli) -> None:
    error = live_cli.err("data-app", "user", "remove", "123", "--yes", *_input({"email": "a@b.co"}))

    assert error["code"] == "missing_argument"


# -- explore panel ---------------------------------------------------------

_PANEL = {
    "height": 248,
    "cards": [{"colId": "column_1", "renderType": "chart"}, {"colId": "column_2"}],
}


def _panel_of(live_cli: LiveCli, sales_data: SalesData) -> dict[str, Any]:
    """The panel saved on the view (empty when none is saved)."""
    got, _ = live_cli.ok(
        "view", "explore-panel", "get", str(sales_data.view), project=sales_data.project
    )
    return dict(got)


def test_columns_all_opens_a_card_per_column_in_the_shape_the_web_app_reads(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    view, _ = live_cli.ok("view", "get", str(sales_data.view), project=sales_data.project)
    columns = view["metadata"]

    data, _ = live_cli.ok(
        "view",
        "explore-panel",
        "set",
        str(sales_data.view),
        *_input({"panel": {"columns": "all"}}),
        project=sales_data.project,
    )

    cards = data["panel"]["cards"]
    assert [card["colId"] for card in cards] == [c["internal_name"] for c in columns]
    first_text = next(c for c in columns if c["type"] == "TEXT")
    first_number = next(c for c in columns if c["type"] == "NUMERIC")
    by_id = {card["colId"]: card["renderType"] for card in cards}
    assert by_id[first_text["internal_name"]] == "list"
    assert by_id[first_number["internal_name"]] == "chart"
    assert _panel_of(live_cli, sales_data)["cards"] == cards


def test_the_old_open_items_panel_is_refused_and_nothing_is_written(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    before = _panel_of(live_cli, sales_data)

    error = live_cli.err(
        "view",
        "explore-panel",
        "set",
        str(sales_data.view),
        *_input({"panel": {"open": True, "items": [{"column": "column_1"}]}}),
        project=sales_data.project,
    )

    assert "No cards yet" in error["message"]
    assert _panel_of(live_cli, sales_data) == before


def test_set_result_carries_the_panel_read_back_after_the_write(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    view, _ = live_cli.ok("view", "get", str(sales_data.view), project=sales_data.project)
    ids = [c["internal_name"] for c in view["metadata"]][:2]
    panel = {
        "height": 248,
        "cards": [{"colId": ids[0], "renderType": "chart"}, {"colId": ids[1]}],
    }

    data, _ = live_cli.ok(
        "view",
        "explore-panel",
        "set",
        str(sales_data.view),
        *_input({"panel": panel}),
        project=sales_data.project,
    )

    assert data["panel"]["height"] == 248
    assert [c["colId"] for c in data["panel"]["cards"]] == ids
    assert _panel_of(live_cli, sales_data) == data["panel"]


# -- token revoke ----------------------------------------------------------


def test_a_failed_client_app_call_does_not_repeat_the_client_key(live_cli: LiveCli) -> None:
    envelope = live_cli.run("token", "revoke", "KEYSECRET123", "--yes")

    assert "error" in envelope
    assert "KEYSECRET123" not in json.dumps(envelope).replace('"client_key":', "")
