"""End-to-end payload test for JSON-shaped transform arguments.

Finding #2 was that the CLI forwarded raw dicts and strings to typed View
transform methods, which crashed inside the payload builders before any request
was emitted. This exercises the whole real path with only the HTTP socket faked:

``call_view`` → argument coercion → the rich ``View`` → its mixin transform →
the payload builder → ``MammothClient`` → ``requests``.

It asserts on the actual task payload the production code emitted, proving the
JSON list-of-dicts became the ``BulkReplaceMapping`` the builder needs and that
the display-name column resolved to its internal name.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

PROJECT_ID = 180
DATASET_ID = 55
VIEW_ID = 1039

ServiceFactory = Callable[..., Any]

_VIEW_METADATA = {
    "id": VIEW_ID,
    "name": "V",
    "metadata": [
        {"display_name": "Item", "internal_name": "column_item", "type": "TEXT"},
    ],
}


def test_bulk_replace_json_becomes_real_task_payload(real_service: ServiceFactory) -> None:
    """Raw JSON mapping flows through real code into the correct task payload."""
    service, api = real_service(project_id=PROJECT_ID)
    # Resolve the view: workspace browse locates the dataset, then the dataview.
    api.on(
        "GET",
        r"/browse",
        body={
            "resources": [
                {"id": PROJECT_ID, "children": [{"type": "datasource", "id": DATASET_ID}]}
            ]
        },
    )
    api.on("GET", rf"/datasets/{DATASET_ID}/dataviews/{VIEW_ID}$", body=_VIEW_METADATA)
    # The transform posts the task, then the SDK polls the pipeline to ready.
    api.on("POST", r"/pipeline/tasks", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready"})

    service.call_view(
        VIEW_ID,
        "bulk_replace",
        columns=["Item"],
        mapping=[{"search": ["6 inch CAKE", "8 inch CAKE"], "replace": "CAKE"}],
    )

    posts = [r for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]
    assert len(posts) == 1, "the transform must emit exactly one add-task request"
    payload = posts[0].json_body
    assert payload["DATAVIEW_ID"] == VIEW_ID
    replace = payload["REPLACE"]
    assert replace["SOURCE"] == ["column_item"]  # display name resolved to internal
    assert replace["MAPPING"] == [
        {"SEARCH_VALUE": ["6 inch CAKE", "8 inch CAKE"], "REPLACE_VALUE": "CAKE"},
    ]
