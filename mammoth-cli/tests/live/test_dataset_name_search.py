"""Live checks: one command finds a dataset by name; a huge ``limit`` is refused up front.

    MAMMOTH_LIVE_LOGIN_FACTORY=api.agents.evals.world:build_login \\
        pytest tests/live/test_dataset_name_search.py -m live -v
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _input(payload: dict[str, Any]) -> list[str]:
    return ["--input", json.dumps(payload)]


def test_a_name_finds_the_dataset_in_one_command(live_cli: LiveCli, sales_data: SalesData) -> None:
    """A case-insensitive fragment of the uploaded file's name returns it, with no columns."""
    found, _ = live_cli.ok(
        *("dataset", "list"), *_input({"name": "SALES_"}), project=sales_data.project
    )
    assert sales_data.dataset in [row["id"] for row in found["datasets"]]
    assert all("columns" not in row for row in found["datasets"])
    assert found["matched"] >= 1

    none, _ = live_cli.ok(
        *("dataset", "list"), *_input({"name": "no-such-dataset-zz"}), project=sales_data.project
    )
    assert none["datasets"] == [] and none["matched"] == 0


def test_limit_over_100_is_refused_before_the_call(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    error = live_cli.err(*("dataset", "list"), *_input({"limit": 1000}), project=sales_data.project)
    assert error["code"] == "invalid_argument"
    assert "100" in error["message"]


def test_no_project_error_names_dataset_find(live_cli: LiveCli) -> None:
    error = live_cli.err("dataset", "list", project=None)
    assert error["code"] == "project_required"
    assert "mammoth dataset find SUBSTRING" in error["recovery_commands"]
