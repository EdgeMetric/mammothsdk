"""A view read that names the dataset leaves the view's parent behind for the next command."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.testing import make_runner
from tests.realcode.test_end_to_end_cli import _bind_real_service

ServiceFactory = Callable[..., Any]
DATASET, VIEW = 55, 1039


def _run(*argv: str) -> Any:
    return make_runner().invoke([*argv, "--project", "180", "--output", "json", "--no-input"])


def test_a_transform_after_a_data_read_needs_no_dataset_id(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """Attempt 1 of the Rashmi session: the agent read the view, then the write was refused."""
    api = _bind_real_service(monkeypatch, real_service, project_id=180)
    api.on(
        "GET",
        rf"/datasets/{DATASET}/dataviews/{VIEW}$",
        body={
            "id": VIEW,
            "metadata": [{"display_name": "Item", "internal_name": "col_item", "type": "TEXT"}],
        },
    )
    api.on("GET", rf"/datasets/{DATASET}$", body={"id": DATASET, "name": "Gifts"})
    api.on("GET", r"/data$", body={"data": []})
    api.on("POST", r"/pipeline/tasks", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready"})

    read = _run("view", "data", "get", str(VIEW), str(DATASET))
    assert read.exit_code == 0, read.output
    write = _run(
        "view",
        "transform",
        "bulk-replace",
        str(VIEW),
        "--input",
        json.dumps({"columns": ["Item"], "mapping": [{"search": ["a"], "replace": "b"}]}),
        "--yes",
    )

    assert write.exit_code == 0, write.output
    assert "missing_argument" not in write.output
