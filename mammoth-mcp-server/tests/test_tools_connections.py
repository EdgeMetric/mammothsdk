"""Bring data in from a source the project already has connected, without leaving the chat.

A connection holds the sign-in, so once the user made it in Mammoth, the model
can bring more data in through it. Databases first: their data is chosen with
SQL, which a model writes well.
"""

import base64
from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.consts import ConnectionFields
from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool, run

PROJECT = 3
KEY = "conn-1"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
ON_POSTGRES = {**IDS, "connector_key": "postgres", "connection_key": KEY}
DATASETS = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets"
JOB = 41


@pytest.fixture(autouse=True)
def brief_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the tests quick: the check waits on a job that may still be pulling."""
    monkeypatch.setattr(ConnectionFields, "CHECK_SECONDS", 0.05)


def connections_path(connector: str) -> str:
    encoded = base64.b64encode(connector.encode()).decode()
    return f"/workspaces/{WORKSPACE}/projects/{PROJECT}/connectors/{encoded}/connections"


def a_sample(rows: int) -> dict[str, Any]:
    return {
        "data_sample": {
            "dataschema": [{"name": "region"}, {"name": "revenue"}],
            "rows": [{"region": f"R{n}", "revenue": n} for n in range(rows)],
        }
    }


class TestListConnections:
    def test_each_connection_names_its_key_and_what_it_connects_to(self) -> None:
        listed = [{"connection_key": KEY, "connection_config": {"host": "db", "database": "sales"}}]
        with a_fake_api() as api, as_caller():
            api.answer("GET", connections_path("postgres"), {"connections": listed})
            found = call_tool("list_connections", connector_key="postgres", **IDS)

        assert found["connections"] == listed


class TestPreviewQuery:
    def test_it_returns_the_first_rows_the_database_sends(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{connections_path('postgres')}/{KEY}/ds_configs", {"job_id": JOB})
            api.answer(
                "GET",
                f"/jobs/{JOB}",
                {"job": {"id": JOB, "status": "success", "response": a_sample(40)}},
            )
            sample = call_tool("preview_query", query="select * from sales", **ON_POSTGRES)

        assert sample["columns"] == ["region", "revenue"]
        assert len(sample["rows"]) == 20
        (sent,) = api.sent("POST", f"{connections_path('postgres')}/{KEY}/ds_configs")
        assert api.body(sent)["data_sample"] is True

    def test_a_query_that_does_not_read_is_refused_before_it_is_sent(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            call_tool("preview_query", query="delete from sales", **ON_POSTGRES)

        assert "SELECT" in str(refused.value)
        assert not api.requests


def add_dataset(**arguments: Any) -> dict[str, Any]:
    # `call_tool` takes the tool's name as `name`, which this tool takes too.
    register_tools()
    called = run(mcp_server.call_tool("add_dataset_from_connection", arguments))
    return dict(called.structured_content)


class TestAddDatasetFromConnection:
    def test_it_asks_mammoth_for_the_dataset_and_says_how_to_find_it(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", DATASETS, {"job_id": JOB})
            api.answer("GET", f"/jobs/{JOB}", {"job": {"id": JOB, "status": "processing"}})
            added = add_dataset(
                name="Sales by region",
                table="sales",
                query="select region, revenue from sales",
                **ON_POSTGRES,
            )

        (sent,) = api.sent("POST", DATASETS)
        assert api.body(sent) == {
            "ds_creation_type": "cloud",
            "dataset_spec": {
                "connector_key": "postgres",
                "connection_key": KEY,
                "query_properties": {
                    "ds_name": "Sales by region",
                    "table_name": "sales",
                    "query": "select region, revenue from sales",
                },
                # Mammoth refuses a dataset with no schedule: this is one pull, now.
                "schedule_properties": {
                    "schedule_type": "moment",
                    "first_pull_at": "now",
                    "on_refresh_action": "replace",
                },
            },
        }
        assert "find_new_datasets" in added["next_step"]
        assert added["since"]

    def test_a_dataset_mammoth_could_not_make_is_reported_at_once(self) -> None:
        # Left to `find_new_datasets`, a failed job reads as "nothing yet", forever.
        failed = {
            "job": {
                "id": JOB,
                "status": "failure",
                "response": {"message": "relation sales does not exist"},
            }
        }
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            api.answer("POST", DATASETS, {"job_id": JOB})
            api.answer("GET", f"/jobs/{JOB}", failed)
            add_dataset(name="Sales", table="sales", query="select * from sales", **ON_POSTGRES)

        assert "relation sales does not exist" in str(refused.value)

    def test_a_source_that_is_not_a_database_goes_to_connect_source(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            add_dataset(
                name="Deals",
                table="deals",
                query="select * from deals",
                **{**ON_POSTGRES, "connector_key": "hubspot"},
            )

        assert "connect_source" in str(refused.value)
        assert not api.requests


def test_what_each_one_may_do() -> None:
    # The SQL runs on the user's own database, and Mammoth does not make it
    # read-only, so a client asks the user before either sends it.
    register_tools()
    tools = {t.name: t for t in run(mcp_server.list_tools())}
    assert tools["list_connections"].annotations.read_only_hint is True
    for name in ("preview_query", "add_dataset_from_connection"):
        assert tools[name].annotations.read_only_hint is False, name
        assert tools[name].annotations.destructive_hint is True, name
