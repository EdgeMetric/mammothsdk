"""FilesAPI: the exact wire request for each call and what it returns / raises.

Runs against a real loopback HTTP server that records every request. Route shapes and
query names come from the pinned prod OpenAPI spec (ListFiles, GetFileDetails, DeleteFiles,
UpdateFileConfigs, PreviewMultiSheetInterpretation, CreateDatasetsFromMultiSheetFile);
the upload job shape (``{"job_ids": [{"job_id": N}], "errors": {...}}``) is the one
mvc-service's ``handle_data_upload`` resolves the upload future with.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from mammoth.models.files import FileSchema, FilesList

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema

BASE = "/workspaces/1/projects/25654/files"

FILE_ROW = {
    "id": 11,
    "name": "orders.csv",
    "status": "ready",
    "created_at": "2026-09-01T10:00:00",
    "last_updated_at": "2026-09-02T10:00:00",
    "status_info": {"processed": "done", "is_hidden": False, "is_empty": False},
    "additional_info": {"append_to_ds_id": None, "final_ds_id": 77, "password_protected": False},
}


def _job(job_id: int, response: dict[str, Any], status: str = "success") -> dict[str, Any]:
    return {
        "job": {
            "id": job_id,
            "status": status,
            "response": response,
            "operation": "x",
            "path": "/x",
            "created_at": "2026-09-01T10:00:00",
            "last_updated_at": "2026-09-01T10:00:01",
        }
    }


# --- list / get -----------------------------------------------------------------------------


async def test_list_sends_no_query_by_default_and_parses_the_page(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {BASE}"] = {"files": [FILE_ROW], "limit": 10, "offset": 0, "next": ""}
    result = await client.files.list()
    assert server.requests == [{"method": "GET", "path": BASE, "query": {}, "body": None}]
    assert isinstance(result, FilesList)
    assert result.files[0].id == 11 and result.files[0].additional_info is not None
    assert result.files[0].additional_info.final_ds_id == 77


async def test_list_filters_use_the_spec_query_names_and_comma_joins(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {BASE}"] = {"files": [], "next": ""}
    await client.files.list(
        fields="__full",
        file_ids=[3, 4],
        names=["a.csv", "b.csv"],
        statuses=["ready", "error"],
        created_at="(from:'2026-01-01T00:00:00.000Z',to:'2026-02-01T00:00:00.000Z')",
        updated_at="(from:'2026-03-01T00:00:00.000Z',to:'2026-04-01T00:00:00.000Z')",
        limit=5,
        offset=10,
        sort="(id:asc)",
    )
    query = server.requests[-1]["query"]
    declared = {p["name"] for p in _list_params()}
    assert set(query) <= declared
    assert query == {
        "fields": "__full",
        "id": "3,4",
        "name": "a.csv,b.csv",
        "status": "ready,error",
        "created_at": "(from:'2026-01-01T00:00:00.000Z',to:'2026-02-01T00:00:00.000Z')",
        "updated_at": "(from:'2026-03-01T00:00:00.000Z',to:'2026-04-01T00:00:00.000Z')",
        "limit": "5",
        "offset": "10",
        "sort": "(id:asc)",
    }


def _list_params() -> list[dict[str, Any]]:
    from ._spec import spec

    params: list[dict[str, Any]] = spec()["paths"][
        "/workspaces/{workspace_id}/projects/{project_id}/files"
    ]["get"]["parameters"]
    return [p for p in params if p["in"] == "query"]


async def test_list_requires_a_project(server: RecordingServer) -> None:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.project_id = None  # type: ignore[assignment]
    with pytest.raises(ValueError, match="project_id must be set"):
        await c.files.list()
    assert server.requests == []


async def test_get_unwraps_the_file_and_passes_fields(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {BASE}/11"] = {"file": FILE_ROW}
    result = await client.files.get(11, fields="__full")
    assert server.requests[-1] == {
        "method": "GET",
        "path": f"{BASE}/11",
        "query": {"fields": "__full"},
        "body": None,
    }
    assert isinstance(result, FileSchema) and result.name == "orders.csv"


async def test_get_without_fields_sends_no_query(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {BASE}/11"] = {"file": FILE_ROW}
    await client.files.get(11)
    assert server.requests[-1]["query"] == {}


# --- delete ---------------------------------------------------------------------------------


async def test_delete_sends_delete_to_the_file(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {BASE}/11"] = (204, None)
    assert await client.files.delete(11) is None
    assert server.requests == [
        {"method": "DELETE", "path": f"{BASE}/11", "query": {}, "body": None}
    ]


async def test_bulk_delete_joins_ids_into_the_ids_query(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {BASE}"] = (204, None)
    await client.files.bulk_delete([5, 6, 7])
    assert server.requests == [
        {"method": "DELETE", "path": BASE, "query": {"ids": "5,6,7"}, "body": None}
    ]
    assert "ids" in {p["name"] for p in _delete_params()}


def _delete_params() -> list[dict[str, Any]]:
    from ._spec import spec

    params: list[dict[str, Any]] = spec()["paths"][
        "/workspaces/{workspace_id}/projects/{project_id}/files"
    ]["delete"]["parameters"]
    return params


# --- patch-based updates --------------------------------------------------------------------


async def test_set_password_patches_the_password_path_and_waits_for_the_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {BASE}/11"] = {"job_id": 90}
    server.answers["GET /jobs/90"] = _job(90, {"ok": True})
    result = await client.files.set_password(11, "s3cret")
    patch = server.requests[0]
    assert (patch["method"], patch["path"]) == ("PATCH", f"{BASE}/11")
    assert patch["body"] == {"patch": [{"op": "replace", "path": "password", "value": "s3cret"}]}
    assert server.requests[1]["path"] == "/jobs/90"
    assert result.job_id == 90
    # The wire values are members of the spec's enums.
    assert patch["body"]["patch"][0]["op"] in schema("files_schema_OpValues")["enum"]
    assert patch["body"]["patch"][0]["path"] in schema("files_schema_PathValues")["enum"]


async def test_extract_sheets_sends_the_extract_config(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {BASE}/11"] = {"job_id": 91}
    server.answers["GET /jobs/91"] = _job(91, {})
    await client.files.extract_sheets(
        11, ["Sheet1", "Sheet2"], delete_file_after_extract=False, combine_after_extract=True
    )
    assert server.requests[0]["body"] == {
        "patch": [
            {
                "op": "replace",
                "path": "extract_sheets",
                "value": {
                    "sheets": ["Sheet1", "Sheet2"],
                    "delete_file_after_extract": False,
                    "combine_after_extract": True,
                },
            }
        ]
    }


async def test_extract_sheets_defaults_match_the_spec(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {BASE}/11"] = {"job_id": 92}
    server.answers["GET /jobs/92"] = _job(92, {})
    await client.files.extract_sheets(11, ["S"])
    value = server.requests[0]["body"]["patch"][0]["value"]
    props = schema("ExtractSheetsPatch")["properties"]
    assert value["delete_file_after_extract"] is props["delete_file_after_extract"]["default"]
    assert value["combine_after_extract"] is props["combine_after_extract"]["default"]


async def test_update_surfaces_a_failed_job(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    from mammoth.exceptions import MammothJobFailedError

    server.answers[f"PATCH {BASE}/11"] = {"job_id": 93}
    server.answers["GET /jobs/93"] = _job(93, {"error": "wrong password"}, status="failure")
    with pytest.raises(MammothJobFailedError) as exc:
        await client.files.set_password(11, "bad")
    assert exc.value.job_id == 93


# --- multi-sheet ----------------------------------------------------------------------------


async def test_preview_multi_sheet_posts_only_the_given_fields(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    path = f"{BASE}/11/sheets/interpretation/preview"
    server.answers[f"POST {path}"] = (201, {"blocks": [], "resolved": None})
    result = await client.files.preview_multi_sheet(11, "Q1", user_instruction="header row 3")
    assert server.requests == [
        {
            "method": "POST",
            "path": path,
            "query": {},
            "body": {"sheet_name": "Q1", "user_instruction": "header row 3"},
        }
    ]
    assert result == {"blocks": [], "resolved": None}


async def test_preview_multi_sheet_sends_block_and_structure_map(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.files.preview_multi_sheet(11, "Q1", block_id="b2", structure_map={"hr": 3})
    assert server.requests[-1]["body"] == {
        "sheet_name": "Q1",
        "block_id": "b2",
        "structure_map": {"hr": 3},
    }
    required = schema("MultiSheetPreviewBody")["required"]
    assert required == ["sheet_name"]


async def test_create_datasets_from_multi_sheet_returns_resource_ids(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    path = f"{BASE}/11/multi-sheet-extraction"
    server.answers[f"POST {path}"] = (202, {"job": {"id": 70, "status": "processing"}})
    server.answers["GET /jobs/70"] = _job(70, {"resource_ids": ["res_a", "res_b"]})
    tables = [{"sheet_name": "Q1", "dataset_name": "Q1 data", "structure_map": {"hr": 1}}]
    result = await client.files.create_datasets_from_multi_sheet(
        11, tables, delete_file_after_extract=False
    )
    assert server.requests[0]["body"] == {"tables": tables, "delete_file_after_extract": False}
    assert result == {"job_id": 70, "status": "success", "resource_ids": ["res_a", "res_b"]}


async def test_create_datasets_from_multi_sheet_without_resource_ids_returns_empty_list(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    path = f"{BASE}/11/multi-sheet-extraction"
    server.answers[f"POST {path}"] = (202, {"job": {"id": 71, "status": "processing"}})
    server.answers["GET /jobs/71"] = _job(71, {"resource_ids": None})
    result = await client.files.create_datasets_from_multi_sheet(11, [])
    assert result["resource_ids"] == []
    assert server.requests[0]["body"]["delete_file_after_extract"] is True


# --- upload ---------------------------------------------------------------------------------


def _csv(tmp_path: Path, name: str = "orders.csv") -> Path:
    f = tmp_path / name
    f.write_text("a,b\n1,2\n")
    return f


def _multipart_names(body: str) -> list[str]:
    import re

    return re.findall(r'name="files"; filename="([^"]+)"', body)


async def test_upload_without_waiting_returns_the_initial_job_and_sends_multipart(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55, "status": "processing"})
    job_id = await client.files.upload(
        _csv(tmp_path),
        folder_resource_id="folder_9",
        append_to_ds_id=77,
        override_target_schema=False,
        wait_for_completion=False,
    )
    assert job_id == 55
    req = server.requests[0]
    assert (req["method"], req["path"]) == ("POST", BASE)
    assert req["query"] == {
        "folder_resource_id": "folder_9",
        "append_to_ds_id": "77",
        "override_target_schema": "false",
    }
    assert _multipart_names(str(req["body"])) == ["orders.csv"]
    assert "a,b\n1,2\n" in str(req["body"])
    assert len(server.requests) == 1  # no polling


async def test_upload_single_file_waits_and_returns_one_dataset_id(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55, "status": "processing"})
    server.answers["GET /jobs/55"] = _job(55, {"job_ids": [{"job_id": 56}], "errors": {}})
    server.answers["GET /jobs"] = {
        "jobs": [
            {
                "id": 56,
                "status": "success",
                "response": {"ds_id": 901},
                "operation": "x",
                "path": "/x",
                "created_at": "t",
                "last_updated_at": "t",
            }
        ]
    }
    assert await client.files.upload(str(_csv(tmp_path))) == 901
    polled = [r for r in server.requests if r["path"] == "/jobs"]
    assert polled and polled[-1]["query"] == {"job_ids": "56"}
    assert server.requests[0]["query"] == {}


async def test_upload_several_files_returns_a_list_of_dataset_ids(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55, "status": "processing"})
    server.answers["GET /jobs/55"] = _job(
        55, {"job_ids": [{"job_id": 56}, {"job_id": 57}], "errors": {}}
    )
    server.answers["GET /jobs"] = {
        "jobs": [
            {
                "id": i,
                "status": "success",
                "response": {"ds_id": 900 + i},
                "operation": "x",
                "path": "/x",
                "created_at": "t",
                "last_updated_at": "t",
            }
            for i in (56, 57)
        ]
    }
    ids = await client.files.upload([_csv(tmp_path, "a.csv"), _csv(tmp_path, "b.csv")])
    assert ids == [956, 957]
    assert _multipart_names(str(server.requests[0]["body"])) == ["a.csv", "b.csv"]
    polled = [r for r in server.requests if r["path"] == "/jobs"]
    assert polled[-1]["query"] == {"job_ids": "56,57"}


async def test_upload_raises_when_the_server_refused_every_file(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55, "status": "processing"})
    server.answers["GET /jobs/55"] = _job(55, {"errors": {"unsupported_files": ["X.pbix"]}})
    with pytest.raises(MammothValidationError, match="unsupported_files") as exc:
        await client.files.upload(_csv(tmp_path, "X.pbix"))
    assert exc.value.details == {"errors": {"unsupported_files": ["X.pbix"]}}


async def test_upload_returns_none_when_no_dataset_job_was_started(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55, "status": "processing"})
    server.answers["GET /jobs/55"] = _job(55, {"errors": {}})
    assert await client.files.upload(_csv(tmp_path)) is None


async def test_upload_result_reports_errors_alongside_created_datasets(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55, "status": "processing"})
    server.answers["GET /jobs/55"] = _job(
        55, {"job_ids": [{"job_id": 56}, {}], "errors": {"harmful_files": ["bad.exe"]}}
    )
    server.answers["GET /jobs"] = {
        "jobs": [
            {
                "id": 56,
                "status": "success",
                "response": None,
                "operation": "x",
                "path": "/x",
                "created_at": "t",
                "last_updated_at": "t",
            }
        ]
    }
    outcome = await client.files.upload_result(_csv(tmp_path))
    assert outcome["job_id"] == 55
    assert outcome["errors"] == {"harmful_files": ["bad.exe"]}
    assert outcome["dataset_ids"] == []  # the finished job reported no ds_id
    assert outcome["nested_job_ids"] == [{"job_id": 56}, {}]
    # Only the nested job that has a job_id is polled.
    assert [r["query"] for r in server.requests if r["path"] == "/jobs"][-1] == {"job_ids": "56"}


async def test_upload_accepts_a_file_object_and_uses_its_basename(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55})
    buf = io.BytesIO(b"x,y\n3,4\n")
    buf.name = "/some/dir/stream.csv"  # type: ignore[misc]
    await client.files.upload(buf, wait_for_completion=False)
    assert _multipart_names(str(server.requests[0]["body"])) == ["stream.csv"]


async def test_upload_a_bare_stream_without_a_name_is_called_uploaded_file(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55})
    await client.files.upload(io.BytesIO(b"x\n1\n"), wait_for_completion=False)
    assert _multipart_names(str(server.requests[0]["body"])) == ["uploaded_file"]


async def test_upload_requires_files(
    server: RecordingServer, client: MammothClient
) -> None:  # noqa: F811
    with pytest.raises(ValueError, match="files parameter is required"):
        await client.files.upload()
    assert server.requests == []


async def test_upload_missing_path_raises_before_any_request(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    with pytest.raises(ValueError, match="File not found: .*missing.csv"):
        await client.files.upload(tmp_path / "missing.csv")
    assert server.requests == []


async def test_upload_folder_uploads_only_regular_files(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    (tmp_path / "sub").mkdir()
    _csv(tmp_path, "one.csv")
    _csv(tmp_path, "two.csv")
    server.answers[f"POST {BASE}"] = (202, {"id": 55})
    job_id = await client.files.upload_folder(
        tmp_path, folder_resource_id="folder_1", wait_for_completion=False
    )
    assert job_id == 55
    assert sorted(_multipart_names(str(server.requests[0]["body"]))) == ["one.csv", "two.csv"]
    assert server.requests[0]["query"] == {"folder_resource_id": "folder_1"}


async def test_upload_folder_rejects_missing_and_empty_folders(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    with pytest.raises(ValueError, match="Folder not found or not a directory"):
        await client.files.upload_folder(tmp_path / "nope")
    with pytest.raises(ValueError, match="No files found in folder"):
        await client.files.upload_folder(tmp_path)
    assert server.requests == []


def _finished_job(job_id: int, ds_id: int) -> dict[str, Any]:
    return {
        "id": job_id,
        "status": "success",
        "response": {"ds_id": ds_id},
        "operation": "x",
        "path": "/x",
        "created_at": "t",
        "last_updated_at": "t",
    }


async def test_upload_of_a_one_item_list_still_returns_a_single_id(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    server.answers[f"POST {BASE}"] = (202, {"id": 55})
    server.answers["GET /jobs/55"] = _job(55, {"job_ids": [{"job_id": 56}], "errors": {}})
    server.answers["GET /jobs"] = {"jobs": [_finished_job(56, 901)]}
    assert await client.files.upload([_csv(tmp_path)]) == 901


async def test_upload_with_some_refused_files_returns_the_created_datasets(
    server: RecordingServer, client: MammothClient, tmp_path: Path  # noqa: F811
) -> None:
    # Only a total refusal (errors and no dataset) raises; a partial one returns what was made.
    server.answers[f"POST {BASE}"] = (202, {"id": 55})
    server.answers["GET /jobs/55"] = _job(
        55, {"job_ids": [{"job_id": 56}], "errors": {"unsupported_files": ["X.pbix"]}}
    )
    server.answers["GET /jobs"] = {"jobs": [_finished_job(56, 901)]}
    result = await client.files.upload([_csv(tmp_path, "a.csv"), _csv(tmp_path, "X.pbix")])
    assert result == [901]
