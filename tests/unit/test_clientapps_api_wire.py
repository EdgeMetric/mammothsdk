"""ClientAppsAPI against the pinned spec (ListApps, CreateApp, AppDetails, UpdateApp, DeleteApp)."""

from __future__ import annotations

import warnings
from typing import Any

import pytest
from pydantic import ValidationError

from mammoth.client import MammothClient
from mammoth.exceptions import MammothModelDriftWarning
from mammoth.models.clientapps import (
    ClientAppPostResponse,
    ClientAppSchema,
    ClientAppsListResponse,
    PatchOperation,
    PatchRequest,
)

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

APPS = "/workspaces/1/clientapps"
APP_ROW = {
    "id": 3,
    "app_name": "etl",
    "app_key": "key_abc",
    "description": "nightly",
    "workspace_id": 1,
    "user_id": 8,
    "last_usage": "2026-09-01T10:00:00",
    "created_at": "2026-08-01T10:00:00",
}


async def test_list_sends_no_query_by_default_and_parses_the_result(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {APPS}"] = {"result": [APP_ROW]}
    result = await client.client_apps.list()
    assert server.requests == [{"method": "GET", "path": APPS, "query": {}, "body": None}]
    assert isinstance(result, ClientAppsListResponse)
    assert result.result[0].app_key == "key_abc" and result.result[0].id == 3


async def test_list_sends_every_filter_and_an_explicit_workspace(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /workspaces/6/clientapps"] = {"result": []}
    await client.client_apps.list(
        workspace_id=6, limit=2, offset=4, fields="app_key", sort="(id:asc)"
    )
    sent = server.requests[0]
    assert sent["path"] == "/workspaces/6/clientapps"
    assert sent["query"] == {"limit": "2", "offset": "4", "fields": "app_key", "sort": "(id:asc)"}
    declared = {
        p["name"]
        for p in spec()["paths"]["/workspaces/{workspace_id}/clientapps"]["get"]["parameters"]
        if p["in"] == "query"
    }
    assert set(sent["query"]) == declared


async def test_list_with_narrowed_fields_still_parses(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {APPS}"] = {"result": [{"app_key": "k"}]}
    result = await client.client_apps.list(fields="app_key")
    assert result.result[0].app_key == "k" and result.result[0].id is None


async def test_create_posts_name_and_a_description_the_api_requires(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {APPS}"] = (
        201,
        {
            "app_name": "etl",
            "app_key": "key_abc",
            "description": "",
            "workspace_id": 1,
            "user_id": 8,
            "token": "mm_secret",
            "expires_at": None,
        },
    )
    created = await client.client_apps.create("etl")
    assert server.requests == [
        {
            "method": "POST",
            "path": APPS,
            "query": {},
            "body": {"app_name": "etl", "description": ""},
        }
    ]
    assert "description" in schema("ClientAppCreate")["required"]
    assert isinstance(created, ClientAppPostResponse) and created.token == "mm_secret"


async def test_create_keeps_the_one_time_token_when_the_response_drifts(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {APPS}"] = (
        201,
        {"app_name": "etl", "app_key": "k", "description": "d", "token": "mm_only_once"},
    )
    with pytest.warns(MammothModelDriftWarning, match="workspace_id"):
        created = await client.client_apps.create("etl", description="d", workspace_id=1)
    assert created.token == "mm_only_once"
    assert server.requests[0]["body"] == {"app_name": "etl", "description": "d"}


async def test_get_passes_fields_and_parses_the_app(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {APPS}/key_abc"] = APP_ROW
    app = await client.client_apps.get("key_abc", fields="__standard")
    assert server.requests == [
        {
            "method": "GET",
            "path": f"{APPS}/key_abc",
            "query": {"fields": "__standard"},
            "body": None,
        }
    ]
    assert isinstance(app, ClientAppSchema) and app.last_usage == "2026-09-01T10:00:00"
    await client.client_apps.get("key_abc", workspace_id=5)
    assert server.requests[-1]["path"] == "/workspaces/5/clientapps/key_abc"
    assert server.requests[-1]["query"] == {}


async def test_update_sends_the_patch_list(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {APPS}/key_abc"] = APP_ROW
    patch = PatchRequest(patch=[PatchOperation(op="replace", path="description", value="new text")])
    app = await client.client_apps.update("key_abc", patch)
    assert server.requests == [
        {
            "method": "PATCH",
            "path": f"{APPS}/key_abc",
            "query": {},
            "body": {"patch": [{"op": "replace", "path": "description", "value": "new text"}]},
        }
    ]
    assert app.app_name == "etl"
    assert schema("PatchRequest")["required"] == ["patch"]


@pytest.mark.xfail(
    strict=True,
    raises=ValidationError,
    reason="BUG: PatchOperation.value is str|None; the spec's PatchOperation.value also takes "
    "a list of strings",
)
def test_patch_operation_accepts_a_list_value_like_the_spec() -> None:
    value_schema: dict[str, Any] = schema("PatchOperation")["properties"]["value"]
    assert {"type": "array", "items": {"type": "string"}} in value_schema["oneOf"]
    assert PatchOperation(op="add", path="scopes", value=["a", "b"]).value == ["a", "b"]  # type: ignore[arg-type]


async def test_delete_sends_delete_and_returns_none(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"DELETE {APPS}/key_abc"] = (204, None)
    assert await client.client_apps.delete("key_abc", workspace_id=1) is None
    assert server.requests == [
        {"method": "DELETE", "path": f"{APPS}/key_abc", "query": {}, "body": None}
    ]


def test_create_model_rejects_an_empty_name() -> None:
    from mammoth.models.clientapps import ClientAppCreate

    with pytest.raises(ValidationError, match="app_name"):
        ClientAppCreate(app_name="")


async def test_matching_create_response_raises_no_warning(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {APPS}"] = (
        201,
        {
            "app_name": "a",
            "app_key": "k",
            "description": "",
            "workspace_id": 1,
            "user_id": 2,
            "token": "mm_t",
        },
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        created = await client.client_apps.create("a")
    assert created.expires_at is None


async def test_list_sends_a_first_offset_of_one(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {APPS}"] = {"result": []}
    await client.client_apps.list(offset=1)
    assert server.requests[0]["query"] == {"offset": "1"}
