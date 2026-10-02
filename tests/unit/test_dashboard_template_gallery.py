"""Offline tests for template thumbnails and the public template gallery."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def _api() -> tuple[DashboardsAPI, AsyncMock]:
    client = AsyncMock()
    return DashboardsAPI(client), client


async def test_template_thumbnail_get_downloads_the_picture() -> None:
    api, client = _api()
    client._request_binary.return_value = {"content_type": "image/png", "size_bytes": 3}
    result = await api.template_thumbnail_get("sales-overview")
    client._request_binary.assert_called_once_with(
        "GET", "/dashboards/v3/templates/sales-overview/thumbnail"
    )
    assert result["content_type"] == "image/png"


async def test_template_thumbnail_path_encodes_the_slug() -> None:
    api, client = _api()
    await api.template_thumbnail_get("a/b c")
    client._request_binary.assert_called_once_with(
        "GET", "/dashboards/v3/templates/a%2Fb%20c/thumbnail"
    )


async def test_template_thumbnail_set_uploads_multipart_data_part(tmp_path: Path) -> None:
    api, client = _api()
    image = tmp_path / "card.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    client._request_json.return_value = {"ok": True}
    result = await api.template_thumbnail_set("sales-overview", image)
    assert result == {"ok": True}
    args, kwargs = client._request_json.call_args
    assert args == ("PUT", "/dashboards/v3/templates/sales-overview/thumbnail")
    [(part, (name, _stream, media_type))] = kwargs["files"]
    assert (part, name, media_type) == ("data", "card.png", "application/octet-stream")


async def test_template_thumbnail_set_rejects_missing_file(tmp_path: Path) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="File not found"):
        await api.template_thumbnail_set("sales-overview", tmp_path / "absent.png")
    client._request_json.assert_not_called()


async def test_template_thumbnail_clear() -> None:
    api, client = _api()
    client._request_json.return_value = {"ok": False}
    result = await api.template_thumbnail_clear("sales-overview")
    client._request_json.assert_called_once_with(
        "DELETE", "/dashboards/v3/templates/sales-overview/thumbnail"
    )
    assert result == {"ok": False}


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.template_thumbnail_get(""),
        lambda api: api.template_thumbnail_clear(""),
        lambda api: api.template_thumbnail_set("", "card.png"),
    ],
)
async def test_template_thumbnail_rejects_empty_template_id(call) -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="template_id"):
        await call(api)
    client._request_json.assert_not_called()
    client._request_binary.assert_not_called()


async def test_gallery_list_without_facets() -> None:
    api, client = _api()
    await api.gallery_list()
    client._request_json.assert_called_once_with("GET", "/dashboards/public/templates", params=None)


async def test_gallery_list_narrows_by_facet() -> None:
    api, client = _api()
    await api.gallery_list(function="sales", industry="retail")
    client._request_json.assert_called_once_with(
        "GET",
        "/dashboards/public/templates",
        params={"function": "sales", "industry": "retail"},
    )


async def test_gallery_get() -> None:
    api, client = _api()
    client._request_json.return_value = {"template": {"slug": "sales-overview"}}
    result = await api.gallery_get("sales-overview")
    client._request_json.assert_called_once_with(
        "GET", "/dashboards/public/templates/sales-overview"
    )
    assert result["template"]["slug"] == "sales-overview"


async def test_gallery_get_rejects_empty_slug() -> None:
    api, client = _api()
    with pytest.raises(MammothValidationError, match="slug"):
        await api.gallery_get("")
    client._request_json.assert_not_called()
