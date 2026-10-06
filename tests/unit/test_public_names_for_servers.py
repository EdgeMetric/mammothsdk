"""The public names a server built on the SDK uses instead of the SDK's private ones.

The client is real; only its HTTP transport is replaced, so each test sees the
request the client sends and decides what the API answers.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx

from mammoth import builders
from mammoth._pure import builders as private_builders
from mammoth.client import MammothClient
from mammoth.models.exports import HandlerType

API = "https://api.invalid/api/v2"


def client_answering(serve: Callable[[httpx.Request], httpx.Response]) -> MammothClient:
    client = MammothClient(api_token="mm_test", base_url=API)
    headers = client.session.headers
    client.session = httpx.AsyncClient(transport=httpx.MockTransport(serve), headers=headers)
    return client


async def test_current_names_the_workspace_and_the_resource_of_the_token() -> None:
    seen: list[httpx.Request] = []

    def serve(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 7, "resource": "https://mcp.invalid/mcp"})

    async with client_answering(serve) as client:
        current = await client.workspaces.current()

    assert (current.id, current.resource) == (7, "https://mcp.invalid/mcp")
    assert seen[0].url.path == "/api/v2/workspaces/current"
    assert seen[0].headers["Authorization"] == "Bearer mm_test"


async def test_current_says_none_for_a_token_issued_for_no_resource() -> None:
    def serve(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": 7})

    async with client_answering(serve) as client:
        current = await client.workspaces.current()

    assert current.resource is None


async def test_a_workspace_set_on_the_client_is_used_without_asking_the_api() -> None:
    seen: list[httpx.Request] = []

    def serve(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 7})

    async with client_answering(serve) as client:
        client.set_workspace_id(7)
        await client.workspaces.get()

    assert client.workspace_id == 7
    assert [request.url.path for request in seen] == ["/api/v2/workspaces/7"]
    assert seen[0].headers["X-WORKSPACE-ID"] == "7"


async def test_request_json_calls_a_route_with_the_clients_credentials() -> None:
    seen: list[httpx.Request] = []

    def serve(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"done": True})

    async with client_answering(serve) as client:
        answer = await client.request_json(
            "PATCH", "/workspaces/7/things/3", params={"fields": "id"}, json={"name": "x"}
        )

    assert answer == {"done": True}
    assert (seen[0].method, seen[0].url.path) == ("PATCH", "/api/v2/workspaces/7/things/3")
    assert seen[0].url.params["fields"] == "id"
    assert json.loads(seen[0].content) == {"name": "x"}
    assert seen[0].headers["Authorization"] == "Bearer mm_test"


def test_builders_are_public_under_their_own_names() -> None:
    assert builders.build_export_spec is private_builders.build_export_spec
    assert builders.build_filter_params is private_builders.build_filter_params
    contract = builders.export_contract(HandlerType.POSTGRES)
    assert contract is not None and "host" in contract.required
    assert set(builders.EXPORT_CONTRACTS) == set(private_builders._EXPORT_CONTRACTS)
