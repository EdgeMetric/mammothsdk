"""W4 (PLAN-021): profile registration, scoped project check, write-state values."""

from __future__ import annotations

import json

import pytest

from mammoth_cli.commands.project import _scoped_dataset_id
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.commands.schema import find_schemas
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import state as state_mod
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import _write_parent
from mammoth_cli.runtime.verify import _known_dataset_id
from mammoth_cli.services.board_values import (
    attach_values,
    dashboard_link,
    figure_bindings,
    results_of,
)
from mammoth_cli.services.command_contract import resolve_command_contract


def _find(query: str) -> list[str]:
    return [match["command_id"] for match in find_schemas(query)["matches"]]


# -- view data profile is a registered, discoverable command ---------------------------------


def test_profile_is_registered_with_the_input_fields_it_reads() -> None:
    assert "view.data.profile" in HANDLERS
    assert command_by_id("view.data.profile")["mutation_class"] == "read"
    contract = resolve_command_contract("view.data.profile")
    assert contract is not None
    assert contract.accepted_field_names == {"target", "columns", "top", "limit"}


@pytest.mark.parametrize(
    "query",
    [
        "profile this data",
        "explore what is in this data",
        "churn drivers",
        "which columns drive churn",
        "understand the dataset",
        "check for blanks and duplicates",
    ],
)
def test_schema_find_surfaces_profile_for_explore_and_driver_phrasing(query: str) -> None:
    assert "view.data.profile" in _find(query)


# -- project check takes a dataset and then reads only it --------------------------------------


def test_project_check_dataset_positional_scopes_and_absent_means_whole_project() -> None:
    scoped = Invocation(command_id="project.check", extra_args=["12", "55"])
    whole = Invocation(command_id="project.check", extra_args=["12"])

    assert _scoped_dataset_id(scoped) == 55
    assert _scoped_dataset_id(whole) is None


def test_project_check_rejects_a_dataset_that_is_not_a_number() -> None:
    with pytest.raises(CliError):
        _scoped_dataset_id(Invocation(command_id="project.check", extra_args=["12", "abc"]))


# -- the post-write export check reuses the dataset the write already carried ----------------


def test_verify_takes_the_dataset_from_the_positional_or_the_input_field(tmp_path) -> None:  # type: ignore[no-untyped-def]
    positional = Invocation(
        command_id="view.transform.filter",
        positionals={"view_id": 9, "dataset_id": 4},
        extra_args=["9", "4"],
    )
    document = tmp_path / "in.json"
    document.write_text(json.dumps({"dataset_id": 7}), encoding="utf-8")
    from_input = Invocation(
        command_id="view.transform.filter",
        input_file=str(document),
        positionals={"view_id": 9},
        extra_args=["9"],
    )

    assert _known_dataset_id(positional) == 4
    assert _known_dataset_id(from_input) == 7
    assert _known_dataset_id(Invocation(command_id="view.transform.filter")) is None


def test_verify_and_readback_use_the_parent_the_write_resolved() -> None:
    # The write carried no dataset_id (the parent came from the local memory);
    # the handler records it once and neither verify nor the readback walks.
    write = Invocation(
        command_id="view.transform.filter", positionals={"view_id": 9}, extra_args=["9"]
    )
    assert _known_dataset_id(write) is None
    object.__setattr__(write, "known_dataset_id", 4)
    assert _known_dataset_id(write) == 4
    assert _write_parent(write, 9) == 4
    assert _write_parent(write, 10) is None


# -- a view edit returns the changed column's new values ------------------------------------


def test_changed_columns_are_read_from_the_edit_input() -> None:
    assert state_mod.changed_columns({"existing_column": "Status", "new_column": "Flag"}) == [
        "Flag",
        "Status",
    ]
    assert state_mod.changed_columns({"columns": ["A", "B"], "renames": {"old": "New"}}) == [
        "A",
        "B",
        "New",
    ]
    assert state_mod.changed_columns(None) == []


def test_changed_column_values_show_new_values_and_name_a_missing_column() -> None:
    rows = [{"Status": "open", "Id": 1}, {"Status": "closed", "Id": 2}]

    values = state_mod.changed_column_values(["Status", "Gone"], rows, ["Status", "Id"])

    assert values["Status"] == ["open", "closed"]
    assert "not a column" in values["Gone"]


def test_a_blank_column_is_still_a_column_of_the_view() -> None:
    values = state_mod.changed_column_values(["Notes"], [], ["Notes"])
    assert values == {"Notes": []}


def test_size_cap_keeps_changed_values_after_the_sample_rows_are_dropped() -> None:
    state = {
        "kind": "data",
        "columns": [{"name": "Status", "type": "TEXT"}],
        "row_count": 50,
        "sample": [{"Status": "x" * 70, "Other": "y" * 70} for _ in range(5)],
        "changed_columns": {"Status": ["open", "closed", "open"]},
    }

    capped = state_mod._enforce_cap(state)

    assert capped["changed_columns"] == {"Status": ["open", "closed", "open"]}
    assert len(json.dumps(capped)) <= state_mod.STATE_SIZE_CAP_BYTES


# -- a built or edited board returns its evaluated numbers -----------------------------------

CANVAS_DOC = {
    "canvas": {
        "focus": {"kpis": [{"label": "Churn rate"}, {"label": "Customers"}]},
        "added": [{"id": "hbar-1", "title": "Churn by plan"}],
    },
    "meta": {
        "figures": {
            "p1:kpi:0": {"descriptors": {"value": "d-rate"}},
            "p1:kpi:1": {"descriptors": {"value": "d-count"}},
            "p1:add:hbar-1": {"descriptors": {"Churn": "d-plan"}},
            "p1:detail": {"descriptors": {"rows": "d-detail"}},
        }
    },
}


def test_bindings_cover_kpi_cards_and_tiles_with_their_labels_and_skip_tables() -> None:
    bindings = figure_bindings(CANVAS_DOC)

    assert [(b["figure"], b["kind"], b["label"]) for b in bindings] == [
        ("p1:kpi:0", "kpi", "Churn rate"),
        ("p1:kpi:1", "kpi", "Customers"),
        ("p1:add:hbar-1", "tile", "Churn by plan"),
    ]


def test_evaluated_numbers_are_attached_to_each_card_and_tile() -> None:
    results = {
        "d-rate": {"status": "success", "value": 0.0734},
        "d-count": {"status": "success", "value": 50000},
        "d-plan": {"status": "success", "data": [{"plan": "basic", "rate": 0.12}] * 14},
    }

    values = attach_values(figure_bindings(CANVAS_DOC), results)

    assert values[0] == {
        "figure": "p1:kpi:0",
        "kind": "kpi",
        "label": "Churn rate",
        "value": 0.0734,
    }
    tile = values[2]["series"]["Churn"]
    assert tile["row_count"] == 14 and len(tile["rows"]) == 10


def test_a_descriptor_that_failed_is_reported_not_dropped() -> None:
    bindings = figure_bindings(CANVAS_DOC)[:1]
    values = attach_values(
        bindings, {"d-rate": {"status": "error", "error": "unknown descriptor id"}}
    )
    assert values[0]["error"] == "unknown descriptor id"


def test_descriptor_data_results_are_found_at_top_level_or_under_response() -> None:
    assert results_of({"results": {"a": 1}}) == {"a": 1}
    assert results_of({"response": {"results": {"a": 1}}}) == {"a": 1}
    assert results_of({"job": {}}) is None


def test_dashboard_link_is_the_web_address_of_the_board() -> None:
    assert (
        dashboard_link("https://app.mammoth.io/api/v2", 4, 140)
        == "https://app.mammoth.io/workspaces/4/publish/140"
    )
