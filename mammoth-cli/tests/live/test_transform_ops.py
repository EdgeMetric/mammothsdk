"""Live: one-call transform ops, display-name resolution and the write read-back.

Replaces the fake-socket realcode tests ``test_one_call_transform_ops``,
``test_m3_resource_resolution``, ``test_transform_payload``, ``test_c1_controls`` (exact-parent
math), ``test_parent_memory_from_reads`` and the convert-type read-back of
``test_settle_after_write``. Each test works on its own new view of a scratch dataset it
uploaded, and the project is deleted at the end of the module.

``items`` has four rows: Cost 10, 20, 30, 40 (sum 100), Qty 1, 2, 3, 4, and four names.
"""

from __future__ import annotations

import csv
import io
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from live_harness import LiveCli, open_live_service, upload_csv

pytestmark = pytest.mark.live


def _csv(rows: list[list[str]]) -> str:
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)
    return out.getvalue()


_ITEMS = _csv(
    [
        ["Item", "Cost", "Name", "Qty"],
        ["widget", "10", "Ada Lovelace", "1"],
        ["gizmo", "20", "Bo Peep", "2"],
        ["gadget", "30", "Cy Young", "3"],
        ["doohickey", "40", "Dee Snider", "4"],
    ]
)
_LOCAL = _csv(
    [
        ["Prix “brut”", "Qty / 値", "Source 名", "revision_rank", "Customer ID"],
        ["10", "1", "k1", "1", "c1"],
        ["20", "2", "k2", "2", "c2"],
        ["30", "3", "k3", "1", "c3"],
    ]
)
_FOREIGN = _csv(
    [
        ["SKU 名", "SELECT", 'Name "quoted"', "Customer ID"],
        ["k1", "alpha", "n1", "c1"],
        ["k2", "beta", "n2", "c2"],
        ["k3", "gamma", "n3", "c9"],
    ]
)


@dataclass(frozen=True)
class Table:
    cli: LiveCli
    project: int
    dataset: int
    view: int

    def op(
        self, command: str, *flags: str, with_dataset: bool = True, **doc: Any
    ) -> dict[str, Any]:
        """Run ``view transform COMMAND`` on this view; return the whole envelope."""
        body = {"dataset_id": self.dataset, **doc} if with_dataset else doc
        return self.cli.run(
            *("view", "transform", command, str(self.view)),
            *("--input", json.dumps(body), "--yes", *flags),
            project=self.project,
        )

    def ok(self, command: str, **doc: Any) -> dict[str, Any]:
        envelope = self.op(command, **doc)
        assert "error" not in envelope, envelope
        data: dict[str, Any] = envelope["data"]
        return data

    def err(self, command: str, **doc: Any) -> dict[str, Any]:
        envelope = self.op(command, **doc)
        assert "error" in envelope, envelope
        error: dict[str, Any] = envelope["error"]
        return error

    def total(self, column: str) -> float:
        """The SUM of ``column`` as the server computes it now."""
        document = {"aggregations": [{"column": column, "function": "SUM", "as_name": "total"}]}
        data, _ = self.cli.ok(
            *("view", "data", "aggregate", str(self.view), str(self.dataset)),
            *("--input", json.dumps(document)),
            project=self.project,
        )
        return float(data["data"][0]["total"])

    def values(self, column: str) -> list[Any]:
        document = {"group_by": [column], "aggregations": [{"function": "COUNT", "as_name": "n"}]}
        data, _ = self.cli.ok(
            *("view", "data", "aggregate", str(self.view), str(self.dataset)),
            *("--input", json.dumps(document), "--output", "json"),
            project=self.project,
        )
        rows = [row[column] for row in data["data"] for _ in range(int(row["n"]))]
        return sorted(rows, key=lambda value: (value is None, str(value)))

    def steps(self) -> int:
        analysed, _ = self.cli.ok(
            *("view", "analyze", str(self.view), str(self.dataset)), project=self.project
        )
        return int(analysed["steps"])

    def columns(self) -> dict[str, str]:
        view, _ = self.cli.ok("view", "get", str(self.view), project=self.project)
        return {c["display_name"]: c["internal_name"] for c in view["metadata"]}

    def draft_enter(self) -> None:
        self.cli.ok(
            *("view", "draft", "enter", str(self.view)),
            *("--input", json.dumps({"dataset_id": self.dataset}), "--yes"),
            project=self.project,
        )

    def draft_status(self) -> dict[str, Any]:
        status, _ = self.cli.ok("view", "draft", "status", str(self.view), project=self.project)
        return dict(status)


@dataclass(frozen=True)
class Source:
    cli: LiveCli
    project: int
    items: int
    local: int
    foreign: int


@pytest.fixture(scope="module")
def source(
    live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory
) -> Source:
    folder = tmp_path_factory.mktemp("ops")
    items, _ = upload_csv(live_cli, scratch_project, folder / "items.csv", _ITEMS)
    local, _ = upload_csv(live_cli, scratch_project, folder / "local.csv", _LOCAL)
    foreign, _ = upload_csv(live_cli, scratch_project, folder / "foreign.csv", _FOREIGN)
    return Source(live_cli, scratch_project, items, local, foreign)


def _fresh(source: Source, dataset: int) -> Iterator[Table]:
    cli, project = source.cli, source.project
    created, _ = cli.ok("view", "create", str(dataset), "--yes", project=project)
    table = Table(cli, project, dataset, int(created["id"]))
    try:
        yield table
    finally:
        parent = ("--input", json.dumps({"dataset_id": dataset}))
        cli.run("view", "draft", "discard", str(table.view), *parent, "--yes", project=project)
        removed = cli.run(
            *("view", "delete", str(table.view), "--yes", "--confirm", str(table.view)),
            *parent,
            project=project,
        )
        assert "error" not in removed, f"view {table.view} not deleted: {removed}"


@pytest.fixture
def items(source: Source) -> Iterator[Table]:
    yield from _fresh(source, source.items)


@pytest.fixture
def local(source: Source) -> Iterator[Table]:
    yield from _fresh(source, source.local)


@pytest.fixture
def foreign_view(source: Source) -> Iterator[Table]:
    yield from _fresh(source, source.foreign)


_UPDATE_COST = {"column": "Cost", "expression": "Cost + 5"}


# -- update-column and first-name ------------------------------------------


def test_update_column_in_draft_mode_submits_and_waits_for_its_own_task(items: Table) -> None:
    items.draft_enter()

    data = items.ok("update-column", **_UPDATE_COST)

    assert data["status"] == "done" and data["draft_applied"] is True
    assert data["run"]["transform_status"] == "DONE" and isinstance(data["run"]["task_id"], int)
    assert "pipeline_error" not in data
    assert items.total("Cost") == 120


def test_update_column_leaves_a_draft_that_held_other_steps_staged(items: Table) -> None:
    """Submitting would run steps the caller never named."""
    items.draft_enter()
    items.ok("limit-rows", n=2)

    data = items.ok("update-column", **_UPDATE_COST)

    assert data["status"] == "staged"
    assert "run" not in data
    assert items.draft_status()["is_draft"] is True
    items.cli.ok(
        *("view", "draft", "discard", str(items.view), "--yes"),
        *("--input", json.dumps({"dataset_id": items.dataset})),
        project=items.project,
    )
    assert items.total("Cost") == 100


def test_update_column_outside_draft_mode_waits_for_its_own_task(items: Table) -> None:
    data = items.ok("update-column", **_UPDATE_COST)

    assert data["run"]["transform_status"] == "DONE"
    assert items.draft_status()["is_draft"] is False
    assert items.total("Cost") == 120


def test_first_name_extracts_the_first_word_in_one_draft_call(items: Table) -> None:
    items.draft_enter()

    data = items.ok("first-name", column="Name", new_column="First name")

    assert data["run"]["transform_status"] == "DONE"
    assert items.values("First name") == ["Ada", "Bo", "Cy", "Dee"]


def test_first_name_needs_exactly_one_destination(items: Table) -> None:
    before = items.steps()

    error = items.err("first-name", column="Name")

    assert "new_column or existing_column" in json.dumps(error)
    assert items.steps() == before


# -- write read-back -------------------------------------------------------


def test_convert_type_reads_back_after_its_own_task_ran(items: Table) -> None:
    data = items.ok("convert-type", conversions=[{"column": "Qty", "to": "TEXT"}])

    assert data["run"]["transform_status"] == "DONE"
    view, _ = items.cli.ok("view", "get", str(items.view), project=items.project)
    assert {c["display_name"]: c["type"] for c in view["metadata"]}["Qty"] == "TEXT"
    assert "pipeline_error" not in data


# -- the view's parent --------------------------------------------------------


def test_a_transform_after_a_data_read_needs_no_dataset_id(items: Table) -> None:
    """The agent read the view, then the write was refused for a missing dataset id."""
    items.cli.ok(
        *("view", "data", "get", str(items.view), str(items.dataset)), project=items.project
    )

    envelope = items.op(
        "bulk-replace",
        with_dataset=False,
        columns=["Item"],
        mapping=[{"search": ["widget"], "replace": "W"}],
    )

    assert "error" not in envelope, envelope
    assert "W" in items.values("Item")


def test_bulk_replace_from_a_json_mapping_changes_the_display_named_column(items: Table) -> None:
    mapping = [{"search": ["widget", "gizmo"], "replace": "TOY"}]

    items.ok("bulk-replace", columns=["Item"], mapping=mapping)

    assert items.values("Item") == ["TOY", "TOY", "doohickey", "gadget"]


def test_the_service_turns_a_raw_json_mapping_into_the_bulk_replace_task(items: Table) -> None:
    mapping = [{"search": ["gadget", "doohickey"], "replace": "TOOL"}]

    with open_live_service(items.project) as service:
        service.call_view(
            items.view, "bulk_replace", dataset_id=items.dataset, columns=["Item"], mapping=mapping
        )

    deadline = time.monotonic() + 90
    while items.values("Item") != ["TOOL", "TOOL", "gizmo", "widget"]:
        assert time.monotonic() < deadline, items.values("Item")
        time.sleep(3)


# -- display-name resolution ----------------------------------------------


def test_math_uses_display_names_with_quotes_and_unicode_and_a_condition(local: Table) -> None:
    local.ok(
        "math",
        expression="Prix “brut” * Qty / 値",
        new_column="Total réservé",
        condition={"column": "Prix “brut”", "operator": "GTE", "value": 20},
    )

    assert local.total("Total réservé") == 20 * 2 + 30 * 3


def test_an_internal_column_id_is_rejected_before_any_step_is_added(local: Table) -> None:
    internal = local.columns()["Prix “brut”"]
    before = local.steps()

    error = local.err("math", expression=f"{internal} * 2", new_column="Total")

    assert error["code"] == "internal_column_name"
    assert local.steps() == before


def test_an_unknown_name_in_a_condition_names_the_reference_and_adds_no_step(
    local: Table,
) -> None:
    before = local.steps()

    error = local.err("filter", condition={"column": "Missing", "operator": "EQ", "value": 1})

    assert error["code"] == "unknown_column"
    assert error["details"]["reference"] == "Missing"
    assert "Source 名" in error["details"]["available"]
    assert error["message"] == "Column reference 'Missing' is not a display name in this view."
    assert local.steps() == before


def test_an_unknown_name_in_a_math_expression_is_named_in_the_error(local: Table) -> None:
    before = local.steps()

    error = local.err("math", expression="revision_rank * Unit Cost", new_column="Total")

    assert error["code"] == "unknown_column"
    assert error["details"]["reference"] == "Unit Cost"
    assert error["details"]["scope"] == "expression"
    assert "'Unit Cost'" in error["message"]
    assert local.steps() == before


def test_join_resolves_foreign_display_names_at_the_foreign_parent(
    local: Table, foreign_view: Table
) -> None:
    local.ok(
        "join",
        foreign_view=foreign_view.view,
        foreign_dataset_id=foreign_view.dataset,
        join_type="LEFT",
        on=[{"left": "Customer ID", "right": "Customer ID"}],
        select=['Name "quoted"', "SELECT"],
    )

    assert local.values('Name "quoted"') == ["n1", "n2", None]
    assert local.values("SELECT") == ["alpha", "beta", None]


def test_an_unknown_foreign_join_name_adds_no_step(local: Table, foreign_view: Table) -> None:
    before = local.steps()

    error = local.err(
        "join",
        foreign_view=foreign_view.view,
        foreign_dataset_id=foreign_view.dataset,
        join_type="LEFT",
        on=[{"left": "Customer ID", "right": "Not in foreign view"}],
        select=["SELECT"],
    )

    assert error["code"] == "unknown_column"
    assert local.steps() == before


def test_a_lookup_by_an_internal_foreign_id_is_rejected_and_by_a_unicode_name_posts_once(
    local: Table, foreign_view: Table
) -> None:
    internal = foreign_view.columns()["SKU 名"]
    parent = {
        "source": "Source 名",
        "lookup_view_id": foreign_view.view,
        "lookup_dataset_id": foreign_view.dataset,
        "value": "SELECT",
        "new_column": "Result 名",
    }
    before = local.steps()

    error = local.err("lookup", key=internal, **parent)
    assert error["code"] == "internal_column_name"
    assert local.steps() == before

    local.ok("lookup", key="SKU 名", **parent)
    assert local.steps() == before + 1
    assert local.values("Result 名") == ["alpha", "beta", "gamma"]


def test_a_numeric_string_condition_value_is_converted_before_the_step_is_added(
    local: Table,
) -> None:
    """eval T2-WPP-W2: a "1" against a NUMERIC column left the pipeline in a type mismatch."""
    local.ok(
        "filter",
        condition={"column": "revision_rank", "operator": "EQ", "value": "1"},
        filter_type="SHOW",
    )

    assert local.values("revision_rank") == [1, 1]
    assert local.draft_status()["step_errors"] == []


def test_an_unconvertible_numeric_condition_value_fails_before_the_step_is_added(
    local: Table,
) -> None:
    before = local.steps()

    error = local.err(
        "filter",
        condition={"column": "revision_rank", "operator": "EQ", "value": "abc"},
        filter_type="SHOW",
    )

    assert error["details"]["column"] == "revision_rank"
    assert error["details"]["column_type"] == "NUMERIC"
    assert error["details"]["value"] == "abc"
    assert local.steps() == before
