"""Bring data in from a connected source: the user connects it in Mammoth, the tools find it.

Connecting a source means signing in to it, and that is the user's to do in
Mammoth, never through a model. So a tool hands the user the page that opens
the connector, and another finds the datasets the project gained afterwards.
"""

import base64
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool, run

PROJECT = 3
CONNECTORS = f"/workspaces/{WORKSPACE}/connectors"
RESOURCES = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/resources"
VIEWS = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/21/dataviews"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
HUBSPOT = {"name_key": "hubspot", "disp_name": "HubSpot", "is_available": True}
SINCE = "2026-10-14T09:00:00+00:00"


def connector_path(key: str) -> str:
    """The route of one connector: the SDK sends its key base64-encoded, as the route reads it."""
    return f"{CONNECTORS}/{base64.b64encode(key.encode()).decode()}"


def a_dataset(status: str, created_at: str = "2026-10-14T09:05:00Z") -> dict[str, Any]:
    return {
        "resource_type": "datasource",
        "object_id": 21,
        "name": "HubSpot deals",
        "status": status,
        "created_at": created_at,
        "object_properties": {},
    }


def query_of(url: str) -> dict[str, list[str]]:
    """The query of a link the web app routes by hash: it follows the `#`."""
    return parse_qs(urlsplit(urlsplit(url).fragment).query)


class TestListConnectors:
    def test_each_connector_names_its_key_and_whether_the_plan_has_it(self) -> None:
        page = {"connectors": [HUBSPOT], "limit": 100, "offset": 0, "next": ""}
        with a_fake_api() as api, as_caller():
            api.answer("GET", CONNECTORS, page)
            listed = call_tool("list_connectors", **IDS)

        assert listed["connectors"] == [HUBSPOT]
        (sent,) = api.sent("GET", CONNECTORS)
        assert sent.url.params["fields"] == "name_key,disp_name,is_available"
        assert sent.url.params["project_id"] == str(PROJECT)
        assert "has_connections" not in sent.url.params

    def test_the_connectors_the_project_already_uses_can_be_asked_for_alone(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", CONNECTORS, {"connectors": [], "next": ""})
            call_tool("list_connectors", connected_only=True, **IDS)

        (sent,) = api.sent("GET", CONNECTORS)
        assert sent.url.params["has_connections"] == "true"


class TestConnectSource:
    def test_the_link_opens_that_connector_in_the_project(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", connector_path("hubspot"), HUBSPOT)
            handed = call_tool("connect_source", connector_key="hubspot", **IDS)

        url = handed["mammoth_url"]
        assert f"/#/workspaces/{WORKSPACE}/projects/{PROJECT}/data/datasets?" in url
        assert query_of(url) == {"action": ["addConnector"], "connector": ["hubspot"]}
        assert handed["connector"] == {"key": "hubspot", "name": "HubSpot"}

    def test_without_a_connector_the_link_opens_the_list_to_pick_from(self) -> None:
        with a_fake_api() as api, as_caller():
            handed = call_tool("connect_source", **IDS)

        assert query_of(handed["mammoth_url"]) == {"action": ["addConnector"]}
        assert "connector" not in handed
        assert not api.requests

    def test_it_says_when_to_look_for_the_new_data_from(self) -> None:
        before = datetime.now(UTC)
        with a_fake_api(), as_caller():
            handed = call_tool("connect_source", **IDS)

        assert datetime.fromisoformat(handed["since"]) >= before.replace(microsecond=0)
        assert "find_new_datasets" in handed["next_step"]

    def test_a_connector_off_the_plan_says_mammoth_will_offer_the_upgrade(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", connector_path("hubspot"), {**HUBSPOT, "is_available": False})
            handed = call_tool("connect_source", connector_key="hubspot", **IDS)

        assert "plan" in handed["next_step"]

    def test_a_connector_mammoth_does_not_have_is_refused_with_where_to_look(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", connector_path("hubspots"), {"message": "Not found"}, status=404)
            with pytest.raises(ToolError) as refused:
                call_tool("connect_source", connector_key="hubspots", **IDS)

        assert "list_connectors" in str(refused.value)


class TestFindNewDatasets:
    def test_a_dataset_made_since_then_is_reported_with_its_view_and_page(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": [a_dataset("processed")]})
            api.answer("GET", VIEWS, {"dataviews": [{"id": 8161}]})
            found = call_tool("find_new_datasets", since=SINCE, **IDS)

        assert found["status"] == "done"
        (dataset,) = found["files"]
        assert dataset["dataset_id"] == 21
        assert dataset["view_id"] == 8161
        assert dataset["mammoth_url"].endswith(f"/projects/{PROJECT}/views/8161")

    def test_a_dataset_made_before_then_is_not_reported(self) -> None:
        old = a_dataset("processed", created_at="2026-10-14T08:59:59Z")
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": [old]})
            found = call_tool("find_new_datasets", since=SINCE, **IDS)

        assert found == {"status": "waiting", "files": []}

    def test_a_dataset_still_coming_in_says_so(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": [a_dataset("processing")]})
            found = call_tool("find_new_datasets", since=SINCE, **IDS)

        assert found["status"] == "processing"

    def test_a_time_that_is_not_one_is_refused(self) -> None:
        with a_fake_api(), as_caller(), pytest.raises(ToolError) as refused:
            call_tool("find_new_datasets", since="yesterday", **IDS)

        assert "connect_source" in str(refused.value)


def test_none_of_them_changes_anything() -> None:
    # The change is the user's, in Mammoth: a read-only connection may hand them the link.
    register_tools()
    tools = {t.name: t for t in run(mcp_server.list_tools())}
    for name in ("list_connectors", "connect_source", "find_new_datasets"):
        assert tools[name].annotations.read_only_hint is True, name
