"""Bring data in from a connected source: the user connects it in Mammoth, the tools find it.

Connecting a source means signing in to it, and that is the user's to do in
Mammoth, never through a model. So a tool hands the user the page that opens
the connector, and another finds the datasets the project gained afterwards.
"""

import base64
import json
import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.server import mcp_server, register_tools
from mammoth_mcp_server.telemetry import EVENT_LOGGER
from mammoth_mcp_server.tools import sources

from .helpers import WORKSPACE, FakeRedis, a_fake_api, a_fake_store, as_caller, call_tool, run

PROJECT = 3
CONNECTORS = f"/workspaces/{WORKSPACE}/connectors"
RESOURCES = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/resources"
VIEWS = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/21/dataviews"
DATASET_21 = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/21"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
HUBSPOT = {"name_key": "hubspot", "disp_name": "HubSpot", "is_available": True}
SINCE = "2026-10-14T09:00:00+00:00"
SELF = "/self"
ADMIN = {"user_roles": {"projects": {str(PROJECT): "project_admin"}, "workspaces": {}}}
ANALYST = {"user_roles": {"projects": {str(PROJECT): "project_analyst"}, "workspaces": {}}}


def connector_path(key: str) -> str:
    """The route of one connector: the SDK sends its key base64-encoded, as the route reads it."""
    return f"{CONNECTORS}/{base64.b64encode(key.encode()).decode()}"


def connections_path(key: str) -> str:
    """The project's connections to one connector, under its base64-encoded key."""
    encoded = base64.b64encode(key.encode()).decode()
    return f"/workspaces/{WORKSPACE}/projects/{PROJECT}/connectors/{encoded}/connections"


OLD = {"connection_key": "old-1", "connection_config": {"name": "Sales team"}}
NEW = {"connection_key": "new-1", "connection_config": {"name": "Marketing"}}


@pytest.fixture(autouse=True)
def store() -> FakeRedis:
    with a_fake_store() as fake:
        yield fake


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
            api.answer("GET", SELF, ADMIN)
            api.answer("GET", connector_path("hubspot"), HUBSPOT)
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            handed = call_tool("connect_source", connector_key="hubspot", **IDS)

        url = handed["mammoth_url"]
        assert f"/#/workspaces/{WORKSPACE}/projects/{PROJECT}/data/datasets?" in url
        assert query_of(url) == {
            "action": ["addConnector"],
            "connector": ["hubspot"],
            "from": ["assistant"],
        }
        assert handed["connector"] == {"key": "hubspot", "name": "HubSpot"}

    def test_without_a_connector_the_link_opens_the_list_to_pick_from(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            handed = call_tool("connect_source", **IDS)

        assert query_of(handed["mammoth_url"]) == {
            "action": ["addConnector"],
            "from": ["assistant"],
        }
        assert "connector" not in handed
        assert not [r for r in api.requests if r.url.path.startswith(CONNECTORS)]

    def test_it_says_when_to_look_for_the_new_data_from(self) -> None:
        before = datetime.now(UTC)
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            handed = call_tool("connect_source", **IDS)

        assert datetime.fromisoformat(handed["since"]) >= before.replace(microsecond=0)
        assert "find_new_datasets" in handed["next_step"]

    def test_a_connector_off_the_plan_says_mammoth_will_offer_the_upgrade(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            api.answer("GET", connector_path("hubspot"), {**HUBSPOT, "is_available": False})
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            handed = call_tool("connect_source", connector_key="hubspot", **IDS)

        assert "plan" in handed["next_step"]

    def test_a_connector_mammoth_does_not_have_is_refused_with_where_to_look(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            api.answer("GET", connector_path("hubspots"), {"message": "Not found"}, status=404)
            with pytest.raises(ToolError) as refused:
                call_tool("connect_source", connector_key="hubspots", **IDS)

        assert "list_connectors" in str(refused.value)


@pytest.fixture(autouse=True)
def brief_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the tests quick; the waiting itself is what some of them test."""
    monkeypatch.setattr(sources, "CONNECT_WAIT_SECONDS", 0.2)
    monkeypatch.setattr(sources, "CONNECT_POLL_SECONDS", 0.02)


class TestWatchingForTheNewConnection:
    """Connecting a source makes a connection. It takes the user two or three minutes in
    Mammoth, so the watch runs for five, ten seconds apart, over as many calls as it needs."""

    def a_watch(self) -> str:
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            api.answer("GET", connector_path("hubspot"), HUBSPOT)
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            return str(call_tool("connect_source", connector_key="hubspot", **IDS)["watch_id"])

    def test_the_connection_the_user_makes_ends_the_wait(self) -> None:
        watch = self.a_watch()
        with a_fake_api() as api, as_caller():
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD, NEW]})
            found = call_tool("find_new_connection", watch_id=watch)

        assert found["status"] == "connected"
        assert found["connections"] == [NEW]
        assert found["connector"] == "hubspot"
        assert len(api.sent("GET", connections_path("hubspot"))) == 2

    def test_a_connection_that_was_there_before_is_not_new(self) -> None:
        watch = self.a_watch()
        with a_fake_api() as api, as_caller():
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            found = call_tool("find_new_connection", watch_id=watch)

        assert found["status"] == "waiting"
        assert "find_new_connection" in found["next_step"]

    def test_after_five_minutes_it_stops_and_says_so(self, monkeypatch: pytest.MonkeyPatch) -> None:
        watch = self.a_watch()
        monkeypatch.setattr(sources, "CONNECT_WATCH_SECONDS", 0)
        with a_fake_api() as api, as_caller():
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            found = call_tool("find_new_connection", watch_id=watch)

        assert found["status"] == "gave_up"

    def test_the_watch_lasts_five_minutes(self, store: FakeRedis) -> None:
        self.a_watch()

        assert max(store.seconds.values()) >= 5 * 60

    def test_a_watch_it_never_started_is_refused(self) -> None:
        with a_fake_api(), as_caller(), pytest.raises(ToolError) as refused:
            call_tool("find_new_connection", watch_id="never-started")

        assert "connect_source" in str(refused.value)

    def test_without_a_connector_there_is_nothing_to_watch(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            handed = call_tool("connect_source", **IDS)

        assert "watch_id" not in handed
        assert "find_new_datasets" in handed["next_step"]


class TestOnlyAProjectAdminGetsTheLink:
    """Mammoth lets only a project admin connect a source, so nobody leaves the chat for nothing."""

    def test_an_analyst_is_told_who_can_connect_it_and_gets_no_link(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ANALYST)
            handed = call_tool("connect_source", connector_key="hubspot", **IDS)

        assert "mammoth_url" not in handed
        assert "project admin" in handed["next_step"]
        assert not api.sent("GET", connector_path("hubspot"))
        (sent,) = api.sent("GET", SELF)
        assert sent.url.params["fields"] == "user_roles"

    def test_a_workspace_role_alone_is_not_enough(self) -> None:
        # Mammoth checks the role on the project itself, not on the workspace.
        owner = {"user_roles": {"projects": {}, "workspaces": {str(WORKSPACE): "workspace_owner"}}}
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, owner)
            handed = call_tool("connect_source", **IDS)

        assert "mammoth_url" not in handed


class TestFindNewDatasets:
    def test_it_looks_again_until_the_dataset_comes_in(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": []})
            api.answer("GET", RESOURCES, {"resources": [a_dataset("processed")]})
            api.answer("GET", VIEWS, {"dataviews": [{"id": 8161}]})
            found = call_tool("find_new_datasets", since=SINCE, **IDS)

        assert found["status"] == "done"
        assert len(api.sent("GET", RESOURCES)) == 2

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

    def test_a_dataset_a_teammate_added_meanwhile_is_not_reported(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": [a_dataset("processed")]})
            api.answer("GET", SELF, {"name": "Asha Rao"})
            api.answer("GET", DATASET_21, {"dataset": {"id": 21, "created_by": "Lee Chen"}})
            found = call_tool("find_new_datasets", since=SINCE, **IDS)

        assert found == {"status": "waiting", "files": []}

    def test_a_dataset_the_caller_added_is_reported(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": [a_dataset("processed")]})
            api.answer("GET", SELF, {"name": "Asha Rao"})
            api.answer("GET", DATASET_21, {"dataset": {"id": 21, "created_by": "Asha Rao"}})
            api.answer("GET", VIEWS, {"dataviews": [{"id": 8161}]})
            found = call_tool("find_new_datasets", since=SINCE, **IDS)

        (dataset,) = found["files"]
        assert dataset["dataset_id"] == 21

    def test_a_time_that_is_not_one_is_refused(self) -> None:
        with a_fake_api(), as_caller(), pytest.raises(ToolError) as refused:
            call_tool("find_new_datasets", since="yesterday", **IDS)

        assert "connect_source" in str(refused.value)


def events(caplog: pytest.LogCaptureFixture, name: str) -> list[dict[str, Any]]:
    logged = [json.loads(one.getMessage()) for one in caplog.records if one.name == EVENT_LOGGER]
    return [one for one in logged if one["event"] == name]


class TestWhatIsMeasured:
    """Which connectors people link to, and how many of those links bring data in."""

    def test_the_link_records_the_connector(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger=EVENT_LOGGER)
        with a_fake_api() as api, as_caller():
            api.answer("GET", SELF, ADMIN)
            api.answer("GET", connector_path("hubspot"), HUBSPOT)
            api.answer("GET", connections_path("hubspot"), {"connections": [OLD]})
            call_tool("connect_source", connector_key="hubspot", **IDS)

        assert events(caplog, "mcp_source_linked") == [
            {"event": "mcp_source_linked", "connector": "hubspot"}
        ]

    def test_a_find_records_what_came_in_but_not_what_it_is(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger=EVENT_LOGGER)
        with a_fake_api() as api, as_caller():
            api.answer("GET", RESOURCES, {"resources": [a_dataset("processed")]})
            api.answer("GET", VIEWS, {"dataviews": [{"id": 8161}]})
            call_tool("find_new_datasets", since=SINCE, **IDS)

        [found] = events(caplog, "mcp_new_datasets")
        assert found == {"event": "mcp_new_datasets", "status": "done", "datasets": 1}


def test_none_of_them_changes_anything() -> None:
    # The change is the user's, in Mammoth: a read-only connection may hand them the link.
    register_tools()
    tools = {t.name: t for t in run(mcp_server.list_tools())}
    for name in ("list_connectors", "connect_source", "find_new_datasets"):
        assert tools[name].annotations.read_only_hint is True, name
