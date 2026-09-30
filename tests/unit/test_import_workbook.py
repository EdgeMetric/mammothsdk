from unittest.mock import AsyncMock, MagicMock

from mammoth.api.dashboards import DashboardsAPI


async def test_import_workbook_posts_multipart_and_closes(tmp_path):
    path = tmp_path / "book.twbx"
    path.write_bytes(b"twbx")
    client = MagicMock()
    client._request_json = AsyncMock(return_value={"data_source": "fitted_sample"})
    await DashboardsAPI(client).import_workbook(path, project_id=3)
    call = client._request_json.call_args.kwargs
    assert call["data"] == {"project_id": "3"}
    assert call["files"][0][0] == "file"
    assert call["files"][0][1][0] == "book.twbx"
    assert call["files"][0][1][1].closed
