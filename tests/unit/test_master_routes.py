"""The SDK methods for the server-master routes send the route, query and body the server takes.

Dashboard drill, rows, describe-a-chart and workspace chart types; automation watched
folders, file routing and run history; connector drafts. Each call goes through a
loopback server, so the request on the wire is what is checked.
"""

from __future__ import annotations

import base64
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth.api import connector_drafts
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

PROJECT = "/workspaces/1/projects/25654"
DRAFTS = f"{PROJECT}/connector-drafts"
AUTOMATIONS = f"{PROJECT}/automations"
DRILL = {"params": {"figure": "p1:add:t-1", "path": [{"key": "West"}]}}
ROWS = {"params": {"figure": "p1:add:t-1", "key": "West"}}
RECIPE = {"params": {"describe": "Revenue by region as bars"}}
CHART_TYPE = {"params": {"name": "Bullet", "recipe": {"mark": "bar"}, "needs": []}}

Call = Callable[[MammothClient], Awaitable[Any]]

# (id, call, method, path, query, body); body None means no JSON body was sent.
CASES: list[tuple[str, Call, str, str, dict[str, str], object]] = [
    (
        "figure-drill",
        lambda c: c.dashboards.figure_drill(7, DRILL),
        "POST",
        "/dashboards/7/drill",
        {},
        DRILL,
    ),
    (
        "published-drill",
        lambda c: c.dashboards.published_drill("abc", DRILL),
        "POST",
        "/dashboards/url/abc/drill",
        {},
        DRILL,
    ),
    (
        "figure-rows",
        lambda c: c.dashboards.figure_rows(7, ROWS),
        "POST",
        "/dashboards/7/rows",
        {},
        ROWS,
    ),
    (
        "published-rows",
        lambda c: c.dashboards.published_rows("abc", ROWS),
        "POST",
        "/dashboards/url/abc/rows",
        {},
        ROWS,
    ),
    (
        "figure-recipe",
        lambda c: c.dashboards.figure_recipe(7, RECIPE),
        "POST",
        "/dashboards/7/figure-recipe",
        {},
        RECIPE,
    ),
    (
        "chart-type-list",
        lambda c: c.dashboards.chart_type_list(),
        "GET",
        "/dashboards/v3/chart-types",
        {},
        None,
    ),
    (
        "chart-type-create",
        lambda c: c.dashboards.chart_type_create(CHART_TYPE),
        "POST",
        "/dashboards/v3/chart-types",
        {},
        CHART_TYPE,
    ),
    (
        "chart-type-delete",
        lambda c: c.dashboards.chart_type_delete("4"),
        "DELETE",
        "/dashboards/v3/chart-types/4",
        {},
        None,
    ),
    (
        "watched-folders",
        lambda c: c.automations.watched_folders(),
        "GET",
        f"{AUTOMATIONS}/folders",
        {},
        None,
    ),
    (
        "runs",
        lambda c: c.automations.runs(12, limit=5),
        "GET",
        f"{AUTOMATIONS}/12/runs",
        {"limit": "5"},
        None,
    ),
    (
        "preview-routes",
        lambda c: c.automations.preview_routes(30, names=["a.csv"], draft={"position": 0}),
        "POST",
        f"{AUTOMATIONS}/route-preview",
        {},
        {"folder_resource_id": 30, "names": ["a.csv"], "draft": {"position": 0}},
    ),
    (
        "set-route-order",
        lambda c: c.automations.set_route_order(30, [12, 11]),
        "PUT",
        f"{AUTOMATIONS}/route-order",
        {},
        {"folder_resource_id": 30, "automation_ids": [12, 11]},
    ),
    (
        "add-run-file-anyway",
        lambda c: c.automations.add_run_file_anyway(44),
        "POST",
        f"{AUTOMATIONS}/run-files/44/add-anyway",
        {},
        None,
    ),
    (
        "draft-list",
        lambda c: c.connector_drafts.list(status="all"),
        "GET",
        DRAFTS,
        {"status": "all"},
        None,
    ),
    (
        "draft-create",
        lambda c: c.connector_drafts.create(connector_key="hubspot", title="Deals"),
        "POST",
        DRAFTS,
        {},
        {"origin": "connections", "connector_key": "hubspot", "title": "Deals"},
    ),
    (
        "draft-known-sources",
        lambda c: c.connector_drafts.known_sources(),
        "GET",
        f"{DRAFTS}/known-sources",
        {},
        None,
    ),
    ("draft-get", lambda c: c.connector_drafts.get(9), "GET", f"{DRAFTS}/9", {}, None),
    (
        "draft-update",
        lambda c: c.connector_drafts.update(9, title="Deals", echo="note"),
        "PATCH",
        f"{DRAFTS}/9",
        {},
        {"title": "Deals", "echo": "note"},
    ),
    ("draft-discard", lambda c: c.connector_drafts.discard(9), "DELETE", f"{DRAFTS}/9", {}, None),
    (
        "draft-browse",
        lambda c: c.connector_drafts.browse(9, folder="root/sub"),
        "GET",
        f"{DRAFTS}/9/browse",
        {"folder": "root/sub"},
        None,
    ),
    (
        "draft-fill",
        lambda c: c.connector_drafts.fill(9, "region", dataset_id=5, key_columns=["id"]),
        "POST",
        f"{DRAFTS}/9/fill",
        {},
        {"column": "region", "dataset_id": 5, "key_columns": ["id"]},
    ),
    (
        "draft-open",
        lambda c: c.connector_drafts.open(9, "ref-1", "Sales"),
        "POST",
        f"{DRAFTS}/9/open",
        {},
        {"ref": "ref-1", "name": "Sales"},
    ),
    (
        "draft-read-tables",
        lambda c: c.connector_drafts.read_tables(9),
        "POST",
        f"{DRAFTS}/9/read-tables",
        {},
        None,
    ),
    (
        "draft-save",
        lambda c: c.connector_drafts.save(9, "daily", dataset_name="Deals"),
        "POST",
        f"{DRAFTS}/9/save",
        {},
        {"refresh": "daily", "dataset_name": "Deals"},
    ),
    (
        "draft-sources",
        lambda c: c.connector_drafts.sources(9),
        "GET",
        f"{DRAFTS}/9/sources",
        {},
        None,
    ),
    (
        "draft-join-candidates",
        lambda c: c.connector_drafts.join_candidates(9, "s2"),
        "GET",
        f"{DRAFTS}/9/sources/s2/join-candidates",
        {},
        None,
    ),
    (
        "draft-preview-source",
        lambda c: c.connector_drafts.preview_source(9, "s1", limit=3),
        "POST",
        f"{DRAFTS}/9/sources/s1/preview",
        {},
        {"limit": 3},
    ),
]


@pytest.mark.parametrize(
    ("call", "method", "path", "query", "body"),
    [case[1:] for case in CASES],
    ids=[case[0] for case in CASES],
)
async def test_each_route_is_sent_as_the_server_takes_it(
    server: RecordingServer,
    client: MammothClient,
    call: Call,
    method: str,
    path: str,
    query: dict[str, str],
    body: object,
) -> None:
    await call(client)

    (request,) = server.requests
    assert (request["method"], request["path"], request["query"]) == (method, path, query)
    assert request["body"] == body


async def test_a_sample_file_goes_up_as_base64_under_its_own_name(
    server: RecordingServer, client: MammothClient, tmp_path: Path
) -> None:
    sample = tmp_path / "wanted.csv"
    sample.write_bytes(b"region,sales\nWest,10\n")

    await client.connector_drafts.sample(9, sample)

    (request,) = server.requests
    assert request["path"] == f"{DRAFTS}/9/sample"
    assert request["body"] == {
        "file_name": "wanted.csv",
        "content_base64": base64.b64encode(b"region,sales\nWest,10\n").decode(),
    }


async def test_a_sample_over_the_server_limit_is_refused_before_sending(
    server: RecordingServer,
    client: MammothClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connector_drafts, "SAMPLE_MAX_BASE64", 8)
    sample = tmp_path / "big.csv"
    sample.write_bytes(b"0123456789")

    with pytest.raises(MammothValidationError, match="too big"):
        await client.connector_drafts.sample(9, sample)
    assert server.requests == []


async def test_deletes_answer_what_they_removed(
    server: RecordingServer, client: MammothClient
) -> None:
    server.answers[f"DELETE {DRAFTS}/9"] = (204, None)
    server.answers["DELETE /dashboards/v3/chart-types/4"] = (204, None)

    assert await client.connector_drafts.discard(9) == {"draft_id": 9, "discarded": True}
    assert await client.dashboards.chart_type_delete("4") == {
        "chart_type_id": "4",
        "deleted": True,
    }


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda c: c.connector_drafts.fill(9, "region"), "exactly one"),
        (lambda c: c.connector_drafts.fill(9, "r", file_object_id=1, dataset_id=2), "exactly one"),
        (lambda c: c.connector_drafts.update(9), "at least one"),
        (lambda c: c.connector_drafts.get(0), "positive"),
        (lambda c: c.connector_drafts.list(status="old"), "status"),
        (lambda c: c.connector_drafts.create(origin="cli"), "origin"),
        (lambda c: c.connector_drafts.create(kind="ftp"), "kind"),
        (lambda c: c.connector_drafts.save(9, "hourly"), "refresh"),
        (lambda c: c.connector_drafts.preview_source(9, "s1", limit=0), "between 1 and 100"),
        (lambda c: c.automations.runs(12, limit=101), "between 0 and 100"),
        (lambda c: c.automations.runs(0), "positive"),
        (lambda c: c.automations.set_route_order(30, []), "at least one"),
        (lambda c: c.dashboards.figure_rows(0, ROWS), "positive"),
        (lambda c: c.connector_drafts.sample(9, "/nonexistent/sample.csv"), "readable"),
    ],
)
async def test_bad_arguments_are_refused_before_sending(
    server: RecordingServer, client: MammothClient, call: Call, message: str
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await call(client)
    assert server.requests == []
