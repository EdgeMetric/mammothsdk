"""ExportsAPI wire requests held to the pinned spec, plus the file download behaviour.

Spec operations: GetPipelineExports, AddExport (AddExportSpec), GetPipelineExport, EditExport,
DeleteExport, ListExportRuns, Suggest (rest-fill), CreatePublishToDb, UpdatePublishToDb.
"""

from __future__ import annotations

import errno
import json
import re
from pathlib import Path
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothValidationError
from mammoth.models.exports import ExportStatus, HandlerType, OdbcType

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

DV = "/workspaces/1/projects/25654/datasets/7/dataviews/3"
EXPORTS = f"{DV}/pipeline/exports"
SPEC_EXPORTS = (
    "/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
    "/dataviews/{dataview_id}/pipeline/exports"
)
JOB = {
    "id": 90,
    "status": "success",
    "response": {},
    "operation": "x",
    "path": "/x",
    "created_at": "2026-09-01T10:00:00",
    "last_updated_at": "2026-09-01T10:00:05",
}


def _only(server: RecordingServer) -> dict[str, Any]:
    assert len(server.requests) == 1
    return server.requests[0]


def _declared(path: str, method: str) -> set[str]:
    op = spec()["paths"][path][method]
    return {p["name"] for p in op.get("parameters", []) if p["in"] == "query"}


def _projectless(server: RecordingServer) -> MammothClient:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.project_id = None  # type: ignore[assignment]
    return c


# --- list -------------------------------------------------------------------------------------


async def test_list_sends_no_query_by_default_and_parses_the_page(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {EXPORTS}"] = {"exports": [{"id": 5, "handler_type": "s3"}], "next": ""}
    page = await client.exports.list(3, dataset_id=7)
    assert _only(server) == {"method": "GET", "path": EXPORTS, "query": {}, "body": None}
    assert page.exports[0].id == 5


async def test_list_sends_every_filter_under_the_spec_names(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {EXPORTS}"] = {"exports": [], "next": ""}
    await client.exports.list(
        3,
        fields="id",
        limit=5,
        offset=10,
        sort="(id:asc)",
        sequence=2,
        status=ExportStatus.EXECUTED,
        reordered=False,
        handler_type=HandlerType.POSTGRES,
        end_of_pipeline=True,
        runnable=False,
        dataset_id=7,
    )
    query = _only(server)["query"]
    assert query == {
        "fields": "id",
        "limit": "5",
        "offset": "10",
        "sort": "(id:asc)",
        "sequence": "2",
        "status": "executed",
        "reorderd": "false",  # the pinned spec itself spells the parameter this way
        "handler_type": "postgres",
        "end_of_pipeline": "true",
        "runnable": "false",
    }
    assert set(query) == _declared(SPEC_EXPORTS, "get")


async def test_list_finds_the_dataset_of_the_dataview_when_not_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /workspaces/1/projects/25654/resources/dataview/3"] = {
        "resource": {"dataset": {"id": 7, "name": "d"}}
    }
    server.answers[f"GET {EXPORTS}"] = {"exports": [], "next": ""}
    await client.exports.list(3)
    assert [r["path"] for r in server.requests] == [
        "/workspaces/1/projects/25654/resources/dataview/3",
        EXPORTS,
    ]


@pytest.mark.parametrize("dataset_id", [0, -1])
async def test_list_refuses_a_non_positive_dataset(
    dataset_id: int, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(
        MammothValidationError, match=f"`dataset_id` must be a positive.*{dataset_id}"
    ):
        await client.exports.list(3, dataset_id=dataset_id)
    assert server.requests == []


@pytest.mark.xfail(
    strict=True,
    reason="BUG: ExportStatus.QUEUED is not in the spec's PipelineItemStatus filter enum, so "
    "list(status=QUEUED) sends a value the server rejects",
)
def test_every_export_status_is_a_value_the_spec_filter_accepts() -> None:
    allowed = set(schema("PipelineItemStatus")["enum"])
    assert {s.value for s in ExportStatus} <= allowed


def test_every_handler_and_odbc_type_is_in_the_spec_enums() -> None:
    assert {h.value for h in HandlerType} <= set(schema("ExportHandlerType")["enum"])
    assert {o.value for o in OdbcType} == set(schema("OdbcTypes")["enum"])


# --- create (via the helper wrappers) ------------------------------------------------------------


async def test_to_dataset_posts_an_internal_dataset_export(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /workspaces/1/projects/25654/resources/dataview/3"] = {
        "resource": {"dataset": {"id": 7}}
    }
    server.answers[f"POST {EXPORTS}"] = (201, {"trigger_id": 12, "status": "added"})
    result = await client.exports.to_dataset(3, "Out", column_mapping={"a": "b"}, sequence=2)
    sent = server.requests[-1]
    assert (sent["method"], sent["path"]) == ("POST", EXPORTS)
    body = sent["body"]
    assert body["handler_type"] == "internal_dataset"
    assert body["target_properties"] == {"dataset_name": "Out", "COLUMN_MAPPING": {"a": "b"}}
    assert body["DATAVIEW_ID"] == 3 and body["sequence"] == 2
    assert body["trigger_type"] == "pipeline" and body["run_immediately"] is True
    assert set(schema("AddExportSpec")["required"]) <= set(body)
    assert result.trigger_id == 12  # type: ignore[union-attr]


async def test_to_dataset_without_column_mapping_sends_only_the_name(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /workspaces/1/projects/25654/resources/dataview/3"] = {
        "resource": {"dataset": {"id": 7}}
    }
    server.answers[f"POST {EXPORTS}"] = (201, {"trigger_id": 1})
    await client.exports.to_dataset(3, "Out")
    assert server.requests[-1]["body"]["target_properties"] == {"dataset_name": "Out"}


async def test_to_s3_names_the_file_and_returns_the_download_url_of_the_finished_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {EXPORTS}"] = (202, {"job": JOB})
    server.answers["GET /jobs/90"] = {
        "job": {**JOB, "response": {"url": "https://files/x.csv", "trigger_id": 4}}
    }
    result = await client.exports.to_s3(3, file="out.csv", dataset_id=7)
    assert result == {"url": "https://files/x.csv", "trigger_id": 4}
    sent = next(r for r in server.requests if r["method"] == "POST")
    assert sent["body"]["handler_type"] == "s3"
    assert sent["body"]["target_properties"] == {
        "file": "out.csv",
        "file_type": "csv",
        "include_hidden": False,
        "is_format_set": True,
        "use_format": True,
    }


async def test_to_s3_generates_a_timestamped_file_name_with_the_requested_type(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {EXPORTS}"] = (201, {"trigger_id": 4})
    result = await client.exports.to_s3(3, file_type="json", dataset_id=7)
    file = _only(server)["body"]["target_properties"]["file"]
    assert re.fullmatch(r"dataview_3_export_\d{8}_\d{6}\.json", file)
    assert result.trigger_id == 4  # type: ignore[union-attr]


async def test_to_s3_returns_the_whole_job_when_it_finished_without_a_url(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {EXPORTS}"] = (202, {"job": JOB})
    server.answers["GET /jobs/90"] = {"job": {**JOB, "response": {"rows": 3}}}
    result = await client.exports.to_s3(3, file="o.csv", dataset_id=7)
    assert isinstance(result, dict) and result["response"] == {"rows": 3}


@pytest.mark.parametrize("method", ["to_s3", "to_dataset", "to_file_url", "to_file"])
async def test_wrappers_need_a_project_on_the_client(method: str, server: RecordingServer) -> None:
    c = _projectless(server)
    args = {"to_dataset": (3, "n")}.get(method, (3,))
    with pytest.raises(ValueError, match="project_id must be set"):
        await getattr(c.exports, method)(*args)
    assert server.requests == []


# --- get / runs / update / delete ---------------------------------------------------------------


async def test_get_sends_fields_only_when_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {EXPORTS}/5"] = {"id": 5}
    assert await client.exports.get(3, 5, dataset_id=7) == {"id": 5}
    await client.exports.get(3, 5, fields="id,status", dataset_id=7)
    assert [r["query"] for r in server.requests] == [{}, {"fields": "id,status"}]
    assert all(r["path"] == f"{EXPORTS}/5" for r in server.requests)
    assert "fields" in _declared(SPEC_EXPORTS + "/{export_id}", "get")


async def test_get_with_an_explicit_project_overrides_the_client_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.exports.get(3, 5, dataset_id=7, project_id=9)
    assert (
        _only(server)["path"]
        == "/workspaces/1/projects/9/datasets/7/dataviews/3/pipeline/exports/5"
    )


async def test_runs_sends_limit_and_parses_the_history(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {EXPORTS}/5/runs"] = {
        "export_id": 5,
        "runs": [{"id": 1, "status": "success", "triggered_by": "manual"}],
    }
    history = await client.exports.runs(3, 5, limit=7, dataset_id=7)
    assert _only(server)["query"] == {"limit": "7"}
    assert history.export_id == 5 and history.runs[0].id == 1


async def test_runs_default_limit_and_bounds(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {EXPORTS}/5/runs"] = {"export_id": 5, "runs": []}
    await client.exports.runs(3, 5, dataset_id=7)
    assert _only(server)["query"] == {"limit": "20"}
    server.requests.clear()
    await client.exports.runs(3, 5, limit=50, dataset_id=7)
    assert _only(server)["query"] == {"limit": "50"}
    server.requests.clear()
    for bad in (0, 51):
        with pytest.raises(MammothValidationError, match=f"between 1 and 50, got {bad}"):
            await client.exports.runs(3, 5, limit=bad, dataset_id=7)
    assert server.requests == []


async def test_update_wraps_patches_and_sends_skip_validation(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    patches = [{"op": "replace", "path": "status", "value": "suspended"}]
    await client.exports.update(3, 5, patches, skip_validation=True, dataset_id=7)
    assert _only(server) == {
        "method": "PATCH",
        "path": f"{EXPORTS}/5",
        "query": {"skip_validation": "true"},
        "body": {"patches": patches},
    }
    assert schema("ExportPatch")["required"] == ["patches"]
    server.requests.clear()
    await client.exports.update(3, 5, patches, dataset_id=7)
    assert _only(server)["query"] == {}


async def test_delete_sends_skip_validation_only_when_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.exports.delete(3, 5, dataset_id=7)
    await client.exports.delete(3, 5, skip_validation=False, dataset_id=7)
    assert [(r["method"], r["path"], r["query"]) for r in server.requests] == [
        ("DELETE", f"{EXPORTS}/5", {}),
        ("DELETE", f"{EXPORTS}/5", {"skip_validation": "false"}),
    ]


CALLS = {
    "get": lambda a: a.get(0, 5, dataset_id=7),
    "get_export": lambda a: a.get(3, 0, dataset_id=7),
    "runs": lambda a: a.runs(0, 5, dataset_id=7),
    "runs_export": lambda a: a.runs(3, -2, dataset_id=7),
    "update": lambda a: a.update(0, 5, [], dataset_id=7),
    "update_export": lambda a: a.update(3, 0, [], dataset_id=7),
    "delete": lambda a: a.delete(0, 5, dataset_id=7),
    "delete_export": lambda a: a.delete(3, 0, dataset_id=7),
    "publish_db": lambda a: a.publish_db(0, OdbcType.POSTGRES, {}, dataset_id=7),
    "publish_db_update": lambda a: a.publish_db_update(0, [], dataset_id=7),
    "rest_fill": lambda a: a.rest_fill(0, "https://docs", dataset_id=7),
}


@pytest.mark.parametrize("name", list(CALLS))
async def test_ids_must_be_positive_before_any_request(
    name: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    what = "export_id" if name.endswith("_export") else "dataview_id"
    with pytest.raises(MammothValidationError, match=f"`{what}` must be a positive integer"):
        await CALLS[name](client.exports)
    assert server.requests == []


@pytest.mark.parametrize(
    "name",
    ["get", "runs", "update", "delete", "publish_db", "publish_db_update", "rest_fill"],
)
async def test_project_scoped_calls_need_a_project(name: str, server: RecordingServer) -> None:
    c = _projectless(server)
    calls = {
        "get": lambda a: a.get(3, 5, dataset_id=7),
        "runs": lambda a: a.runs(3, 5, dataset_id=7),
        "update": lambda a: a.update(3, 5, [], dataset_id=7),
        "delete": lambda a: a.delete(3, 5, dataset_id=7),
        "publish_db": lambda a: a.publish_db(3, OdbcType.POSTGRES, {}, dataset_id=7),
        "publish_db_update": lambda a: a.publish_db_update(3, [], dataset_id=7),
        "rest_fill": lambda a: a.rest_fill(3, "https://docs", dataset_id=7),
    }
    with pytest.raises(ValueError, match="project_id must be provided either to the method"):
        await calls[name](c.exports)
    assert server.requests == []


async def test_list_and_create_need_a_project_too(server: RecordingServer) -> None:
    c = _projectless(server)
    with pytest.raises(ValueError, match="project_id must be set"):
        await c.exports.list(3, dataset_id=7)
    assert server.requests == []


# --- rest-fill -----------------------------------------------------------------------------------


async def test_rest_fill_without_waiting_returns_the_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {EXPORTS}/rest-fill"] = (202, {"id": 31})
    job = await client.exports.rest_fill(
        3, "https://docs.x/api", notes="n", wait=False, dataset_id=7
    )
    assert job == {"id": 31}
    assert _only(server) == {
        "method": "POST",
        "path": f"{EXPORTS}/rest-fill",
        "query": {},
        "body": {"docs_url": "https://docs.x/api", "notes": "n"},
    }
    assert set(schema("RestFillRequest")["required"]) <= set(_only(server)["body"])


async def test_rest_fill_waits_for_the_job_result(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {EXPORTS}/rest-fill"] = (202, {"id": 31})
    server.answers["GET /jobs/31"] = {"job": {**JOB, "id": 31, "response": {"suggestion": "ok"}}}
    job = await client.exports.rest_fill(3, "https://docs.x", dataset_id=7)
    assert job["response"] == {"suggestion": "ok"}
    assert [r["path"] for r in server.requests] == [f"{EXPORTS}/rest-fill", "/jobs/31"]


@pytest.mark.parametrize(
    ("docs_url", "notes", "message"),
    [
        ("", "", "`docs_url` must be a non-empty string"),
        ("   ", "", "`docs_url` must be a non-empty string"),
        ("https://d", "x" * 2001, "`notes` must be at most 2000 characters, got 2001"),
    ],
)
async def test_rest_fill_validates_before_any_request(
    docs_url: str,
    notes: str,
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.exports.rest_fill(3, docs_url, notes=notes, dataset_id=7)
    assert server.requests == []


# --- export hosts ---------------------------------------------------------------------------------


async def test_set_export_hosts_puts_the_policy_and_checks_the_limits(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["PUT /workspaces/1/export-hosts"] = {"restricted": True, "hosts": ["a.io"]}
    policy = await client.exports.set_export_hosts(True, ["a.io"])
    assert _only(server)["body"] == {"restricted": True, "hosts": ["a.io"]}
    assert policy.restricted is True and policy.hosts == ["a.io"]
    server.requests.clear()
    await client.exports.set_export_hosts(False)
    assert _only(server)["body"] == {"restricted": False, "hosts": []}
    server.requests.clear()
    for hosts, message in (
        (["h"] * 101, "at most 100 hosts, got 101"),
        (["ok", "  "], "entries must be non-empty strings"),
    ):
        with pytest.raises(MammothValidationError, match=message):
            await client.exports.set_export_hosts(True, hosts)
    assert server.requests == []


# --- publish to db --------------------------------------------------------------------------------

PUB = f"{DV}/publish-to-db"


async def test_publish_db_posts_the_connection_type_and_target(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    example = schema("TriggerPropertiesSchema")["examples"][0]["value"]
    await client.exports.publish_db(3, OdbcType.BIGQUERY, example, dataset_id=7)
    assert _only(server) == {
        "method": "POST",
        "path": PUB,
        "query": {},
        "body": {"odbc_type": "bigquery", "target_properties": example},
    }
    assert set(schema("PublishDataSchema")["required"]) <= set(_only(server)["body"])


async def test_publish_db_update_wraps_the_patch(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    patch = [{"op": "replace", "path": "table", "value": "t2"}]
    await client.exports.publish_db_update(3, patch, dataset_id=7)
    assert _only(server) == {"method": "PATCH", "path": PUB, "query": {}, "body": {"patch": patch}}
    assert schema("PublishToDBPatchRequest")["required"] == ["patch"]


# --- to_file_url and to_file ----------------------------------------------------------------


def _url_job(server: RecordingServer, response: dict[str, Any]) -> None:
    server.answers[f"POST {EXPORTS}"] = (202, {"job": JOB})
    server.answers["GET /jobs/90"] = {"job": {**JOB, "response": response}}


async def test_to_file_url_exports_to_a_temp_s3_file_and_returns_the_url(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _url_job(server, {"url": "https://files/e.xlsx", "trigger_id": 8})
    result = await client.exports.to_file_url(3, "xlsx", dataset_id=7)
    assert result == {"url": "https://files/e.xlsx", "trigger_id": 8, "job_id": 90}
    body = next(r["body"] for r in server.requests if r["method"] == "POST")
    assert body["handler_type"] == "s3" and body["trigger_type"] == "none"
    assert body["target_properties"]["file"] == "temp_export_7_3.xlsx"
    assert body["target_properties"]["file_type"] == "xlsx"
    assert body["run_immediately"] is True and body["validate_only"] is False


async def test_to_file_url_fails_clearly_when_the_job_has_no_url(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _url_job(server, {"rows": 3})
    with pytest.raises(ValueError, match="No download URL found in completed job 90"):
        await client.exports.to_file_url(3, dataset_id=7)


async def test_to_file_url_fails_clearly_when_no_job_was_started(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {EXPORTS}"] = (201, {"trigger_id": 1})
    with pytest.raises(ValueError, match="No job ID found in export result"):
        await client.exports.to_file_url(3, dataset_id=7)


async def test_to_file_url_rejects_an_unknown_file_type(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="file_type must be one of"):
        await client.exports.to_file_url(3, "exe", dataset_id=7)  # type: ignore[arg-type]
    assert server.requests == []


async def test_to_csv_url_is_the_csv_file_url(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    _url_job(server, {"url": "https://files/e.csv"})
    result = await client.exports.to_csv_url(3, dataset_id=7)
    assert result["url"] == "https://files/e.csv"
    body = next(r["body"] for r in server.requests if r["method"] == "POST")
    assert body["target_properties"]["file_type"] == "csv"


def _download_url(server: RecordingServer, path: str) -> str:
    return f"http://127.0.0.1:{server.server_port}{path}"


async def test_to_file_downloads_the_exported_bytes_to_the_default_name(
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    _url_job(server, {"url": _download_url(server, "/dl/e.csv"), "trigger_id": 8})
    server.answers["GET /dl/e.csv"] = {"a": [1, 2]}
    path = await client.exports.to_file(3, dataset_id=7)
    assert path == Path("dataview_7_3_export.csv")
    assert json.loads((tmp_path / path).read_text()) == {"a": [1, 2]}
    assert [p.name for p in tmp_path.iterdir()] == ["dataview_7_3_export.csv"]


async def test_to_csv_downloads_to_the_requested_path_creating_parents(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    _url_job(server, {"url": _download_url(server, "/dl/e.csv")})
    server.answers["GET /dl/e.csv"] = {"rows": 1}
    target = tmp_path / "deep" / "out.csv"
    assert await client.exports.to_csv(3, target, dataset_id=7) == target
    assert json.loads(target.read_text()) == {"rows": 1}
    assert [p.name for p in target.parent.iterdir()] == ["out.csv"]


async def test_a_failed_download_leaves_no_file_and_says_the_export_itself_succeeded(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    _url_job(server, {"url": _download_url(server, "/dl/gone.csv")})
    server.answers["GET /dl/gone.csv"] = (404, {"detail": "expired"})
    target = tmp_path / "out.csv"
    with pytest.raises(MammothAPIError, match="Failed to download file") as exc:
        await client.exports.to_csv(3, target, dataset_id=7)
    err = exc.value
    assert err.status_code == 404
    assert err.phase == "download" and err.job_handle == 90
    assert err.operation_state == "succeeded"
    assert err.details["local_artifact_state"] == "failed"
    assert err.details["remote_export_state"] == "succeeded"
    assert list(tmp_path.iterdir()) == []


async def test_an_unreachable_download_host_has_no_status_code(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    _url_job(server, {"url": "http://127.0.0.1:1/dl/e.csv"})
    with pytest.raises(MammothAPIError, match="Failed to download file") as exc:
        await client.exports.to_csv(3, tmp_path / "o.csv", dataset_id=7)
    assert exc.value.status_code is None
    assert exc.value.details["exception_type"] in {"ConnectError", "ConnectTimeout"}
    assert list(tmp_path.iterdir()) == []


async def test_download_never_replaces_a_symlink_destination(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    precious = tmp_path / "precious.txt"
    precious.write_text("keep")
    link = tmp_path / "out.csv"
    link.symlink_to(precious)
    _url_job(server, {"url": _download_url(server, "/dl/e.csv")})
    with pytest.raises(MammothAPIError, match="Failed to save downloaded file") as exc:
        await client.exports.to_csv(3, link, dataset_id=7)
    assert exc.value.details["errno"] == errno.ELOOP
    assert precious.read_text() == "keep"
    assert not any(r["path"] == "/dl/e.csv" for r in server.requests)
