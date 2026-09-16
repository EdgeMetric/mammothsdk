"""Offline wire contract for bounded pipeline-items readback."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.runtime.invocation import Invocation


def test_items_all_follows_bounded_offsets_on_exact_parent(
    real_service, monkeypatch, tmp_path: Path
):
    service, api = real_service(project_id=3)

    def respond(request):
        offset = int(request.query.get("offset", ["0"])[0])
        if offset == 0:
            return 200, {
                "items": [{"id": 41, "item_type": "task"}],
                "next": (
                    "/api/v2/workspaces/4/projects/3/datasets/731/dataviews/278/"
                    "pipeline/items?limit=1&offset=1"
                ),
            }
        return 200, {"items": [{"id": 42, "item_type": "task"}], "next": ""}

    api.on(
        "GET",
        r"/workspaces/4/projects/3/datasets/731/dataviews/278/pipeline/items",
        handler=respond,
    )
    input_file = tmp_path / "items-all.json"
    input_file.write_text(
        json.dumps({"dataset_id": 731, "limit": 1, "max_pages": 3}), encoding="utf-8"
    )

    @contextmanager
    def bound(_invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(view_cmd, "open_service", bound)
    invocation = Invocation(
        "view.pipeline.items-all",
        output="json",
        project=3,
        no_input=True,
        extra_args=["278"],
        input_file=str(input_file),
    )
    data, _ = view_cmd.view_pipeline_items_all(invocation)

    assert data["items"] == [{"id": 41, "item_type": "task"}, {"id": 42, "item_type": "task"}]
    assert [request.query for request in api.requests] == [
        {"limit": ["1"], "offset": ["0"]},
        {"limit": ["1"], "offset": ["1"]},
    ]
    assert all(
        request.path
        == "/api/v2/workspaces/4/projects/3/datasets/731/dataviews/278/pipeline/items"
        for request in api.requests
    )
