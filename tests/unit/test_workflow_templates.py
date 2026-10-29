"""The project workflow-template catalog client: routes, bodies, wrapped lists and refusals.

The loopback server records each request; nothing here reaches a real server.
"""

from __future__ import annotations

import pytest

from mammoth.client import SUB_CLIENTS, MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

_BASE = "/workspaces/1/projects/25654/workflow-templates"
_MATCHES = {"main": {"amount": {"column": "Amount"}}}


def test_the_catalog_is_a_sub_client_apart_from_the_legacy_templates() -> None:
    assert SUB_CLIENTS["workflow_templates"][1] == "WorkflowTemplatesAPI"
    assert SUB_CLIENTS["templates"][1] == "TemplatesAPI"


async def test_list_reads_the_project_catalog_and_wraps_the_bare_array(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {_BASE}"] = [{"key": "bank-reconciliation"}]
    assert await client.workflow_templates.list() == {"templates": [{"key": "bank-reconciliation"}]}
    assert [(r["method"], r["path"]) for r in server.requests] == [("GET", _BASE)]


async def test_rank_posts_the_input_and_wraps_the_bare_array(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {_BASE}/bank-reconciliation/rank"] = [{"dataset_id": 4}]
    ranked = await client.workflow_templates.rank("bank-reconciliation", "main", [4, 5])
    assert ranked == {"tables": [{"dataset_id": 4}]}
    assert server.requests[0]["body"] == {"input": "main", "dataset_ids": [4, 5]}


async def test_the_read_calls_use_their_own_routes(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    api = client.workflow_templates
    await api.get("bank-reconciliation")
    await api.sample_result("bank-reconciliation")
    await api.fit("bank-reconciliation", {"main": 4})
    await api.import_samples("bank-reconciliation")
    assert [(r["method"], r["path"]) for r in server.requests] == [
        ("GET", f"{_BASE}/bank-reconciliation"),
        ("GET", f"{_BASE}/bank-reconciliation/sample-result"),
        ("POST", f"{_BASE}/bank-reconciliation/fit"),
        ("POST", f"{_BASE}/bank-reconciliation/samples"),
    ]
    assert server.requests[2]["body"] == {"inputs": {"main": 4}}


async def test_preview_and_build_send_matches_settings_and_destination(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    api = client.workflow_templates
    await api.preview("bank-reconciliation", {"main": 4}, _MATCHES, settings={"days": 3})
    await api.build(
        "bank-reconciliation", {"main": 4}, _MATCHES, "Result", destination_emails=["a@b.c"]
    )
    preview, build = (r["body"] for r in server.requests)
    assert preview == {"inputs": {"main": 4}, "matches": _MATCHES, "settings": {"days": 3}}
    assert build == {
        "inputs": {"main": 4},
        "matches": _MATCHES,
        "destination": {"name": "Result", "emails": ["a@b.c"]},
    }


async def test_a_key_is_one_path_segment(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workflow_templates.get("a/b")
    assert server.requests[0]["path"] == f"{_BASE}/a%2Fb"


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get(""),
        lambda api: api.get("  "),
        lambda api: api.list(project_id=0),
        lambda api: api.rank("k", "", [1]),
        lambda api: api.rank("k", "main", []),
        lambda api: api.rank("k", "main", [0]),
        lambda api: api.rank("k", "main", list(range(1, 202))),
        lambda api: api.fit("k", {}),
        lambda api: api.fit("k", {"main": 0}),
        lambda api: api.fit("k", {"main": True}),
        lambda api: api.build("k", {"main": 4}, _MATCHES, ""),
        lambda api: api.build("k", {"main": 4}, _MATCHES, "x" * 121),
    ],
)
async def test_bad_input_is_refused_before_any_request(
    server: RecordingServer, client: MammothClient, call: object  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await call(client.workflow_templates)  # type: ignore[operator]
    assert server.requests == []
