"""``view transform join --dry-run`` reports key overlap and writes nothing."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.view import key_overlap
from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]


def test_key_overlap_weights_rows_and_treats_blank_keys_as_unmatched() -> None:
    out = key_overlap({"a": 6, "b": 2, None: 1, "": 1}, {"a"})
    assert out["match_rate"] == 0.6
    assert out["unmatched_rows"] == 4
    assert out["unmatched_keys"] == ["b", "None", ""]


def test_key_overlap_of_an_empty_view_has_no_rate() -> None:
    assert key_overlap({}, {"a"})["match_rate"] is None


def _view(name: str, internal: str) -> dict[str, Any]:
    return {
        "id": 1,
        "name": "V",
        "row_count": 4,
        "metadata": [{"display_name": name, "internal_name": internal, "type": "TEXT"}],
    }


def test_dry_run_reports_match_rate_without_writing(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Path
) -> None:
    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    api.on("GET", r"/datasets/10/dataviews/1$", body=_view("cust", "column_1"))
    api.on("GET", r"/datasets/20/dataviews/2$", body={**_view("id", "column_9"), "id": 2})

    def aggregate(request: Any) -> tuple[int, Any]:
        left = "/dataviews/1/" in request.path
        rows = [("a", 3), ("b", 1)] if left else [("a", 1)]
        return 200, {"data": [{"group_0": k, "agg_0": n} for k, n in rows]}

    api.on("POST", r"/dataviews/\d+/data/query", handler=aggregate)
    doc = tmp_path / "join.json"
    doc.write_text(
        json.dumps(
            {
                "dataset_id": 10,
                "foreign_view": 2,
                "foreign_dataset_id": 20,
                "join_type": "LEFT",
                "on": [{"left": "cust", "right": "id"}],
                "select": ["id"],
            }
        ),
        encoding="utf-8",
    )
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "join",
            "1",
            "--project",
            "180",
            "--input",
            "@" + str(doc),
            "--dry-run",
            "--output",
            "json",
        ]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)["data"]
    assert data["join_preview"]["checked"] is True, data["join_preview"]
    assert data["join_preview"]["match_rate"] == 0.75
    assert [
        r
        for r in api.requests
        if r.method in ("POST", "PUT", "PATCH", "DELETE") and "task" in r.path
    ] == []
