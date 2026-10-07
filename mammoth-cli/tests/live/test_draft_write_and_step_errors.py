"""Live: a write in draft mode is staged without a settle wait; draft status lists step errors.

Each test works on its own new view of the module's scratch dataset, deleted afterwards.
Run on the box with the test identity (see ``conftest.py``)::

    pytest tests/live/test_draft_write_and_step_errors.py -m live -v
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


@dataclass(frozen=True)
class Fresh:
    cli: LiveCli
    project: int
    dataset: int
    view: int

    def ok(self, *args: str, **document: Any) -> Any:
        body = json.dumps({"dataset_id": self.dataset, **document})
        data, _ = self.cli.ok(*args, "--input", body, "--yes", project=self.project)
        return data


@pytest.fixture
def fresh(live_cli: LiveCli, sales_data: SalesData) -> Iterator[Fresh]:
    created, _ = live_cli.ok(
        *("view", "create", str(sales_data.dataset), "--yes"), project=sales_data.project
    )
    made = Fresh(live_cli, sales_data.project, sales_data.dataset, int(created["id"]))
    try:
        yield made
    finally:
        live_cli.run(
            *("view", "draft", "discard", str(made.view), "--yes"),
            *("--input", json.dumps({"dataset_id": made.dataset})),
            project=made.project,
        )
        removed = live_cli.run(
            *("view", "delete", str(made.view), "--yes", "--confirm", str(made.view)),
            *("--input", json.dumps({"dataset_id": made.dataset})),
            project=made.project,
        )
        assert "error" not in removed, f"view {made.view} not deleted: {removed}"


def _sort(fresh: Fresh) -> dict[str, Any]:
    data: dict[str, Any] = fresh.ok(
        *("view", "transform", "sort", str(fresh.view)), order_by=[["Revenue", "DESC"]]
    )
    return data


def _step_errors(fresh: Fresh) -> list[dict[str, Any]]:
    status: dict[str, Any] = fresh.ok("view", "draft", "status", str(fresh.view))
    errors: list[dict[str, Any]] = status["step_errors"]
    return errors


def test_a_sort_in_draft_mode_is_staged(fresh: Fresh) -> None:
    fresh.ok("view", "draft", "enter", str(fresh.view))

    data = _sort(fresh)

    assert data.get("status") == "staged"
    assert data["sort"] == [["Revenue", "DESC"]]
    assert "row_check" not in data


def test_a_sort_outside_draft_mode_is_not_staged(fresh: Fresh) -> None:
    data = _sort(fresh)

    assert data.get("status") != "staged"
    assert data["row_check"]["rows_after"] > 0


def test_draft_status_lists_the_step_whose_reference_is_in_error(fresh: Fresh) -> None:
    fresh.ok(
        *("view", "transform", "math", str(fresh.view)),
        expression="Units * 2",
        new_column="Double",
    )
    fresh.ok("view", "draft", "enter", str(fresh.view))
    fresh.ok(
        *("view", "transform", "filter", str(fresh.view)),
        condition={"column": "Double", "operator": "GT", "value": 5},
    )
    steps = fresh.ok("view", "task", "list", str(fresh.view))["tasks"]
    assert _step_errors(fresh) == []

    fresh.ok("view", "task", "delete", str(fresh.view), str(steps[0]["id"]))

    errors = _step_errors(fresh)
    assert [(e["item_type"], e["id"]) for e in errors] == [("task", steps[1]["id"])]
    assert [e["column"] for e in errors[0]["reference_errors"]] == ["Double"]


def test_draft_status_with_no_broken_step_lists_none(fresh: Fresh) -> None:
    fresh.ok("view", "draft", "enter", str(fresh.view))
    fresh.ok(*("view", "transform", "limit-rows", str(fresh.view)), n=5)

    assert _step_errors(fresh) == []
