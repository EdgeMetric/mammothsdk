"""Download formats (``to_file`` / ``to_file_url``) against a real loopback HTTP server."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth.api.exports import DownloadFileType
from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError
from tests.unit._loopback import RecordingServer, client, server  # noqa: F401

DATAVIEWS = "/workspaces/1/projects/25654/datasets/500/dataviews/42"


def _script(server: RecordingServer, file_type: str) -> None:  # noqa: F811
    """The export create answers a job; the job answers success with a URL on this server."""
    url = f"http://127.0.0.1:{server.server_port}/files/out.{file_type}"
    job = {
        "id": 9001,
        "status": "success",
        "response": {"url": url, "trigger_id": 77},
        "last_updated_at": "2026-10-21T00:00:00Z",
        "created_at": "2026-10-21T00:00:00Z",
        "path": "/pipeline/exports",
        "operation": "add_export",
    }
    server.answers[f"POST {DATAVIEWS}/pipeline/exports"] = {"job": job}
    server.answers["GET /jobs/9001"] = {"job": job}
    server.answers["GET /files/out." + file_type] = {"ok": True}


def _export_body(server: RecordingServer) -> dict[str, object]:  # noqa: F811
    posts = [r for r in server.requests if r["method"] == "POST"]
    assert len(posts) == 1
    body = posts[0]["body"]
    assert isinstance(body, dict)
    return body


@pytest.mark.parametrize("file_type", ["csv", "xlsx", "json", "ndjson", "xml", "yaml", "parquet"])
async def test_to_file_url_asks_the_backend_for_that_file_type(
    client: MammothClient, server: RecordingServer, file_type: DownloadFileType  # noqa: F811
) -> None:
    _script(server, file_type)

    result = await client.exports.to_file_url(42, file_type, dataset_id=500)

    target = _export_body(server)["target_properties"]
    assert isinstance(target, dict)
    assert target["file_type"] == file_type
    assert str(target["file"]).endswith(f".{file_type}")
    assert result["url"].endswith(f"/files/out.{file_type}")


async def test_to_file_writes_the_download_with_the_matching_extension(
    client: MammothClient, server: RecordingServer, tmp_path: Path  # noqa: F811
) -> None:
    _script(server, "xlsx")
    target_file = tmp_path / "dataview_500_42_export.xlsx"

    path = await client.exports.to_file(42, str(target_file), "xlsx", dataset_id=500)

    assert path == target_file and path.exists()
    target = _export_body(server)["target_properties"]
    assert isinstance(target, dict) and target["file_type"] == "xlsx"


async def test_to_csv_still_asks_for_csv(
    client: MammothClient, server: RecordingServer, tmp_path: Path  # noqa: F811
) -> None:
    _script(server, "csv")

    await client.exports.to_csv(42, str(tmp_path / "o.csv"), dataset_id=500)

    target = _export_body(server)["target_properties"]
    assert isinstance(target, dict) and target["file_type"] == "csv"


async def test_a_file_type_outside_the_download_menu_is_refused_before_any_request(
    client: MammothClient, server: RecordingServer  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="csv, xlsx, json, ndjson, xml, yaml, parquet"):
        await client.exports.to_file_url(42, "docx", dataset_id=500)  # type: ignore[arg-type]
    assert server.requests == []
