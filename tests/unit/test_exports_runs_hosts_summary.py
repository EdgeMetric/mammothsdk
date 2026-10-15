"""Export runs, REST fill, export hosts and the view summary: the wire each SDK call sends.

Runs against a real loopback HTTP server that records every request.
"""

from __future__ import annotations

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from mammoth.models.exports import ExportHostPolicy, ExportHostPolicyRead, ExportRuns

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

VIEW = "/workspaces/1/projects/25654/datasets/77/dataviews/88"

RUNS = {
    "export_id": 5,
    "runs": [
        {
            "id": 9,
            "started_at": "2026-10-14T10:00:00Z",
            "finished_at": "2026-10-14T10:00:03Z",
            "duration_seconds": 3.0,
            "status": "success",
            "rows_exported": 120,
            "destination": {"handler_type": "S3", "target": "s3://bucket/key"},
            "error_message": None,
            "triggered_by": "schedule",
        },
        {"id": 8, "status": "failed", "error_message": "403", "triggered_by": "manual"},
    ],
}


async def test_runs_gets_the_run_history_with_the_limit(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {VIEW}/pipeline/exports/5/runs"] = RUNS
    result = await client.exports.runs(88, 5, limit=10, dataset_id=77)
    assert server.requests[-1] == {
        "method": "GET",
        "path": f"{VIEW}/pipeline/exports/5/runs",
        "query": {"limit": "10"},
        "body": None,
    }
    assert isinstance(result, ExportRuns)
    assert result.export_id == 5
    assert [run.id for run in result.runs] == [9, 8]
    assert result.runs[0].destination is not None
    assert result.runs[0].destination.target == "s3://bucket/key"
    assert result.runs[1].status.value == "failed"
    assert result.runs[1].triggered_by.value == "manual"


async def test_runs_finds_the_dataset_when_none_is_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {VIEW}/pipeline/exports/5/runs"] = {"export_id": 5, "runs": []}

    async def find(dataview_id: int) -> int:
        return 77

    client.pipeline.find_dataset_for_dataview = find  # type: ignore[method-assign]
    result = await client.exports.runs(88, 5)
    assert result.runs == []
    assert server.requests[-1]["query"] == {"limit": "20"}


@pytest.mark.parametrize(
    ("kwargs", "text"),
    [
        ({"dataview_id": 0, "export_id": 5}, "dataview_id"),
        ({"dataview_id": 88, "export_id": 0}, "export_id"),
        ({"dataview_id": 88, "export_id": 5, "limit": 0}, "limit"),
        ({"dataview_id": 88, "export_id": 5, "limit": 51}, "limit"),
    ],
)
async def test_runs_refuses_bad_input_before_any_request(
    server: RecordingServer, client: MammothClient, kwargs: dict[str, int], text: str  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=text):
        await client.exports.runs(dataset_id=77, **kwargs)
    assert server.requests == []


async def test_rest_fill_posts_the_docs_url_and_waits_for_the_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {VIEW}/pipeline/exports/rest-fill"] = (
        201,
        {"id": 31, "status": "processing"},
    )
    server.answers["GET /jobs/31"] = {
        "id": 31,
        "status": "success",
        "response": {"suggestion": {"method": "POST", "url": "https://api.example.com/v1/rows"}},
    }
    job = await client.exports.rest_fill(
        88, "https://docs.example.com/api", notes="bulk", dataset_id=77
    )
    assert server.requests[0] == {
        "method": "POST",
        "path": f"{VIEW}/pipeline/exports/rest-fill",
        "query": {},
        "body": {"docs_url": "https://docs.example.com/api", "notes": "bulk"},
    }
    assert server.requests[1]["path"] == "/jobs/31"
    assert job["response"]["suggestion"]["method"] == "POST"


async def test_rest_fill_without_wait_returns_the_queued_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {VIEW}/pipeline/exports/rest-fill"] = (
        201,
        {"id": 31, "status": "processing"},
    )
    job = await client.exports.rest_fill(
        88, "https://docs.example.com/api", wait=False, dataset_id=77
    )
    assert job == {"id": 31, "status": "processing"}
    assert len(server.requests) == 1


@pytest.mark.parametrize(
    ("docs_url", "notes", "text"),
    [("", "", "docs_url"), ("  ", "", "docs_url"), ("https://x.test", "n" * 2001, "notes")],
)
async def test_rest_fill_refuses_bad_input_before_any_request(
    server: RecordingServer,
    client: MammothClient,
    docs_url: str,
    notes: str,
    text: str,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=text):
        await client.exports.rest_fill(88, docs_url, notes=notes, dataset_id=77)
    assert server.requests == []


async def test_export_hosts_reads_the_policy(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /workspaces/1/export-hosts"] = {
        "restricted": True,
        "hosts": ["api.example.com"],
        "in_use": ["api.example.com", "hooks.example.com"],
    }
    policy = await client.exports.export_hosts()
    assert server.requests[-1]["method"] == "GET"
    assert server.requests[-1]["path"] == "/workspaces/1/export-hosts"
    assert isinstance(policy, ExportHostPolicyRead)
    assert policy.restricted is True
    assert policy.in_use == ["api.example.com", "hooks.example.com"]


async def test_set_export_hosts_puts_the_whole_policy(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["PUT /workspaces/1/export-hosts"] = {"restricted": True, "hosts": ["a.test"]}
    policy = await client.exports.set_export_hosts(True, ["a.test"])
    assert server.requests[-1] == {
        "method": "PUT",
        "path": "/workspaces/1/export-hosts",
        "query": {},
        "body": {"restricted": True, "hosts": ["a.test"]},
    }
    assert isinstance(policy, ExportHostPolicy)
    assert policy.hosts == ["a.test"]


async def test_set_export_hosts_unrestricted_sends_an_empty_list(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["PUT /workspaces/1/export-hosts"] = {"restricted": False, "hosts": []}
    await client.exports.set_export_hosts(False)
    assert server.requests[-1]["body"] == {"restricted": False, "hosts": []}


@pytest.mark.parametrize("hosts", [["ok.test", ""], ["x.test"] * 101])
async def test_set_export_hosts_refuses_bad_hosts_before_any_request(
    server: RecordingServer, client: MammothClient, hosts: list[str]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="hosts"):
        await client.exports.set_export_hosts(True, hosts)
    assert server.requests == []


async def test_summary_gets_the_view_summary(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    body = {
        "transformations": [{"id": 1}],
        "actions": [],
        "data_out": [],
        "dashboards": [],
        "result": None,
    }
    server.answers[f"GET {VIEW}/summary"] = body
    assert await client.dataviews.summary(77, 88) == body
    assert server.requests[-1] == {
        "method": "GET",
        "path": f"{VIEW}/summary",
        "query": {},
        "body": None,
    }


async def test_summary_refuses_a_bad_dataview_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="dataview_id"):
        await client.dataviews.summary(77, 0)
    assert server.requests == []
