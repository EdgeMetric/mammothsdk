"""Live: a standing filter that removes no row today is refused without ``--standing``.

QA R-5: "keep only rows where Units is at least 0" on a view where every row passes.
Each test works on its own new view of the module's scratch dataset, deleted afterwards.
Run on the box with the test identity (see ``conftest.py``)::

    pytest tests/live/test_standing_filter.py -m live -v
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live

_KEEP_ALL = {"condition": {"column": "Units", "operator": "GTE", "value": 0}}


@dataclass(frozen=True)
class Fresh:
    cli: LiveCli
    project: int
    dataset: int
    view: int

    def filter(self, *flags: str) -> dict[str, Any]:
        body = json.dumps({"dataset_id": self.dataset, **_KEEP_ALL})
        return self.cli.run(
            *("view", "transform", "filter", str(self.view)),
            *("--input", body, *flags),
            project=self.project,
        )

    def steps(self) -> list[dict[str, Any]]:
        data, _ = self.cli.ok(
            *("view", "task", "list", str(self.view)),
            *("--input", json.dumps({"dataset_id": self.dataset})),
            project=self.project,
        )
        tasks: list[dict[str, Any]] = data["tasks"]
        return tasks


@pytest.fixture
def fresh(live_cli: LiveCli, sales_data: SalesData) -> Iterator[Fresh]:
    created, _ = live_cli.ok(
        *("view", "create", str(sales_data.dataset), "--yes"), project=sales_data.project
    )
    made = Fresh(live_cli, sales_data.project, sales_data.dataset, int(created["id"]))
    try:
        yield made
    finally:
        removed = live_cli.run(
            *("view", "delete", str(made.view), "--yes", "--confirm", str(made.view)),
            *("--input", json.dumps({"dataset_id": made.dataset})),
            project=made.project,
        )
        assert "error" not in removed, f"view {made.view} not deleted: {removed}"


def test_a_filter_that_removes_nothing_is_refused_and_names_the_flag(fresh: Fresh) -> None:
    dry = fresh.filter("--dry-run")
    assert dry["error"]["code"] == "no_op" and "--standing" in dry["error"]["hint"]

    real = fresh.filter("--yes")
    assert real["data"]["status"] == "no_change" and "--standing" in real["data"]["hint"]
    assert fresh.steps() == []


def test_standing_stages_a_filter_that_removes_nothing(fresh: Fresh) -> None:
    dry = fresh.filter("--dry-run", "--standing")
    impact = dry["data"]["predicted_impact"]
    assert impact["standing"] is True and impact["rows_removed"] == 0

    real = fresh.filter("--yes", "--standing")
    assert "error" not in real, real
    assert real["data"]["standing_rule"]["removed_now"] == 0
    assert len(fresh.steps()) == 1
