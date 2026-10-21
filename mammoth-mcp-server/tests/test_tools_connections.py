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
from mammoth_mcp_server.dataset_app import check_query
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
    """A sample as Mammoth sends it: the columns in `dataschema`, each row a list of values."""
    return {
        "data_sample": {
            "dataschema": [
                {"c_id": "column_1", "c_name": "region", "c_type": "text"},
                {"c_id": "column_2", "c_name": "revenue", "c_type": "numeric"},
            ],
            "rows": [[f"R{n}", n] for n in range(rows)],
        }
    }


class TestListConnections:
    def test_each_connection_names_its_key_and_what_it_connects_to(self) -> None:
        listed = [{"connection_key": KEY, "connection_config": {"host": "db", "database": "sales"}}]
        with a_fake_api() as api, as_caller():
            api.answer("GET", connections_path("postgres"), {"connections": listed})
            found = call_tool("list_connections", connector_key="postgres", **IDS)

        assert found["connections"] == listed


def a_job(job_id: int, response: dict[str, Any]) -> dict[str, Any]:
    return {"job": {"id": job_id, "status": "success", "response": response}}


def with_tables(*tables: str) -> dict[str, Any]:
    """The answer of the `ds_config_spec` concern: the form the web app draws, tables in it."""
    items = [{"name": table, "value": table} for table in tables]
    return {
        "is_valid": True,
        "ds_config_spec": {"ux": {"attributes": {"tables": {"items": items}}}},
    }


class TestListTables:
    CONNECTION = f"{connections_path('postgres')}/{KEY}"

    def answer(self, api: Any, schemas: list[str], tables: dict[str, Any] | None = None) -> None:
        """Mammoth lists the schemas in one job, then a schema's tables in another."""
        api.answer("GET", self.CONNECTION, {"job_id": 51})
        api.answer("GET", self.CONNECTION, {"job_id": 52})
        api.answer(
            "GET", "/jobs/51", a_job(51, {"profiles": [{"name": s, "value": s} for s in schemas]})
        )
        api.answer("GET", "/jobs/52", a_job(52, tables or with_tables("orders", "customers")))

    def test_it_lists_the_tables_of_the_schema_asked_for(self) -> None:
        with a_fake_api() as api, as_caller():
            self.answer(api, ["public", "sales"])
            found = call_tool("list_tables", schema="sales", **ON_POSTGRES)

        assert found == {
            "schemas": ["public", "sales"],
            "schema": "sales",
            "tables": ["orders", "customers"],
        }
        schemas, tables = api.sent("GET", self.CONNECTION)
        assert schemas.url.params["concern"] == "profiles"
        assert tables.url.params["concern"] == "ds_config_spec"
        assert tables.url.params["profile"] == "sales"

    def test_a_schema_mammoth_did_not_list_is_never_sent(self) -> None:
        # Some databases put the schema straight into their own SQL.
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            self.answer(api, ["public", "sales"])
            call_tool("list_tables", schema="x'; DROP TABLE t; --", **ON_POSTGRES)

        assert "public, sales" in str(refused.value)
        (only,) = api.sent("GET", self.CONNECTION)
        assert only.url.params["concern"] == "profiles"

    def test_with_several_schemas_and_none_asked_for_it_lists_the_schemas(self) -> None:
        with a_fake_api() as api, as_caller():
            self.answer(api, ["public", "sales"])
            found = call_tool("list_tables", **ON_POSTGRES)

        assert found["schemas"] == ["public", "sales"]
        assert "tables" not in found
        assert "schema" in found["next_step"]
        assert len(api.sent("GET", self.CONNECTION)) == 1

    def test_the_only_schema_is_picked_by_itself(self) -> None:
        with a_fake_api() as api, as_caller():
            self.answer(api, ["dbo"])
            found = call_tool("list_tables", **ON_POSTGRES)

        assert found["schema"] == "dbo"
        assert found["tables"] == ["orders", "customers"]

    def test_a_database_without_schemas_lists_its_tables_at_once(self) -> None:
        # MySQL and Redshift name no schemas: a connection reads one database.
        with a_fake_api() as api, as_caller():
            self.answer(api, [])
            found = call_tool("list_tables", **ON_POSTGRES)

        assert found["tables"] == ["orders", "customers"]
        assert "profile" not in api.sent("GET", self.CONNECTION)[1].url.params

    def test_a_connection_the_database_refuses_says_so(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            self.answer(api, [], {"is_valid": False, "message": "password authentication failed"})
            call_tool("list_tables", **ON_POSTGRES)

        assert "password authentication failed" in str(refused.value)

    def test_a_source_that_is_not_a_database_is_refused_before_anything_is_sent(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError):
            call_tool("list_tables", **{**ON_POSTGRES, "connector_key": "hubspot"})

        assert api.requests == []


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
        assert sample["rows"][3] == {"region": "R3", "revenue": 3}
        (sent,) = api.sent("POST", f"{connections_path('postgres')}/{KEY}/ds_configs")
        assert api.body(sent)["data_sample"] is True

    def test_a_query_that_does_not_read_is_refused_before_it_is_sent(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            call_tool("preview_query", query="delete from sales", **ON_POSTGRES)

        assert "SELECT" in str(refused.value)
        assert not api.requests


class TestTheReadCheck:
    """A query that starts with SELECT or WITH can still write, so the check looks past the start."""

    @pytest.mark.parametrize(
        "query",
        [
            "SELECT 1; DROP TABLE orders",
            "WITH d AS (DELETE FROM orders RETURNING *) SELECT * FROM d",
            "SELECT * INTO orders_copy FROM orders",
            "with u as (update orders set paid = true returning id) select * from u",
            # Postgres reads brackets as an array index, not as a quoted name.
            "SELECT (ARRAY[1,2,3])[1:(SELECT length(']'))]; DROP TABLE t; SELECT '1'",
        ],
    )
    def test_a_query_that_writes_is_refused(self, query: str) -> None:
        with pytest.raises(ToolError) as refused:
            check_query("postgres", query)

        assert "SELECT" in str(refused.value)

    @pytest.mark.parametrize(
        "query",
        [
            # Postgres reads \' in an E'' string as a quote, so the rest runs.
            "SELECT E'\\'' ; DROP TABLE orders; -- '",
            # MySQL runs what a /*! */ comment holds.
            "SELECT 1 /*! ; DROP TABLE orders */",
            "SELECT * FROM orders /*! INTO OUTFILE '/tmp/o.csv' */",
            # Postgres and Snowflake read $$'$$ as a string, so the rest runs.
            "SELECT $$'$$; DROP TABLE orders; SELECT $$'$$",
            "SELECT $q$'$q$; DROP TABLE orders; SELECT $q$'$q$",
            # MySQL ends the line at #, so the quote after it opens nothing.
            "SELECT 1 # '\n; DROP TABLE orders; -- '",
            # Postgres nests /* */, so the quote is inside the comment.
            "SELECT 1 /* /* */ ' */; DELETE FROM t; -- '",
            # MySQL reads 1--1 as 1 - -1, not as a comment.
            "SELECT 1--1;DELETE FROM t",
            # Snowflake ends the line at //.
            "SELECT 1 // '\n; DROP TABLE t // '",
            "SELECT 1 /* a note */; insert into audit values (1)",
            "SELECT region -- drop the old ones later\nFROM sales",
        ],
    )
    def test_a_query_that_hides_text_from_the_check_is_refused(self, query: str) -> None:
        with pytest.raises(ToolError) as refused:
            check_query("postgres", query)

        assert "backslashes" in str(refused.value)

    @pytest.mark.parametrize(
        "query",
        [
            "select * from sales;",
            "SELECT 'delete me' AS note, \"update\" FROM sales",
            "SELECT '-- not a note' AS a, '/* nor this */' AS b, '//' AS c FROM sales",
            "SELECT replace(region, 'a', 'b'), created_at, updated_by FROM sales",
            "select `insert` from sales",
            "SELECT tags[1], '#1' AS ref, 'cost $5' AS note FROM sales",
        ],
    )
    def test_a_read_that_only_names_a_write_word_passes(self, query: str) -> None:
        check_query("postgres", query)

    @pytest.mark.parametrize(
        "query",
        [
            # SQL Server reads [a'] as a name, so the quote opens no string.
            "SELECT 1 AS [a'], 2; DELETE FROM t; SELECT 3 AS [']",
            "SELECT [region] FROM sales",
        ],
    )
    def test_a_bracket_name_on_sql_server_is_refused(self, query: str) -> None:
        with pytest.raises(ToolError) as refused:
            check_query("mssql", query)

        assert '"name"' in str(refused.value)

    def test_a_bracket_inside_a_string_on_sql_server_passes(self) -> None:
        check_query("mssql", "SELECT \"region\", '[draft]' AS note FROM sales")

    def test_a_column_named_like_a_write_word_is_told_to_quote_it(self) -> None:
        with pytest.raises(ToolError) as refused:
            check_query("postgres", "SELECT call, merge FROM phone_log")

        assert "quote" in str(refused.value)


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
                # Mammoth refuses a dataset with no schedule. Unless asked, it is one pull, now.
                "schedule_properties": {
                    "schedule_type": "moment",
                    "first_pull_at": "now",
                    "on_refresh_action": "replace",
                },
            },
        }
        assert "find_new_datasets" in added["next_step"]
        assert added["since"]

    def a_dataset_made(self, **choices: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """The dataset spec sent and the answer, for a call with these choices."""
        with a_fake_api() as api, as_caller():
            api.answer("POST", DATASETS, {"job_id": JOB})
            api.answer("GET", f"/jobs/{JOB}", {"job": {"id": JOB, "status": "processing"}})
            added = add_dataset(
                name="Sales", query="select * from sales", **{**ON_POSTGRES, **choices}
            )
        (sent,) = api.sent("POST", DATASETS)
        return api.body(sent)["dataset_spec"], added

    def test_the_table_defaults_to_the_dataset_name(self) -> None:
        spec, _ = self.a_dataset_made()

        assert spec["query_properties"]["table_name"] == "Sales"

    def test_once_is_the_default_and_says_so(self) -> None:
        spec, added = self.a_dataset_made()

        assert "recurrence_info" not in spec
        assert added["schedule"] == "Once, now."

    def test_a_dataset_kept_fresh_repeats_on_the_schedule_asked_for(self) -> None:
        spec, added = self.a_dataset_made(
            repeat="daily",
            every=2,
            start_at="2026-10-16T06:00:00+00:00",
            until="2026-12-31T00:00:00+00:00",
            on_refresh="append",
        )

        assert spec["schedule_properties"] == {
            "schedule_type": "period",
            "first_pull_at": "later",
            "on_refresh_action": "append",
        }
        assert spec["recurrence_info"] == {
            "interval": 2,
            "frequency": "daily",
            "start_at": "2026-10-16T06:00:00+00:00",
            "until": "2026-12-31T00:00:00+00:00",
        }
        assert added["schedule"] == (
            "Every 2 days from 2026-10-16T06:00:00+00:00 until"
            " 2026-12-31T00:00:00+00:00, adding the new rows."
        )

    def test_a_repeat_with_no_start_starts_now(self) -> None:
        spec, _ = self.a_dataset_made(repeat="hourly")

        assert spec["schedule_properties"]["first_pull_at"] == "now"
        assert spec["recurrence_info"]["start_at"]

    def test_combine_matches_rows_on_the_column_named(self) -> None:
        spec, _ = self.a_dataset_made(
            repeat="daily", on_refresh="combine", unique_column="id", unique_column_type="numeric"
        )

        assert spec["schedule_properties"]["on_refresh_action"] == "combine"
        assert spec["schedule_properties"]["unique_sequence_column"] == {
            "c_name": "id",
            "c_type": "numeric",
        }

    def test_combine_without_a_column_to_match_on_is_refused(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError) as refused:
            add_dataset(
                name="Sales", query="select * from sales", on_refresh="combine", **ON_POSTGRES
            )

        assert "unique_column" in str(refused.value)
        assert not api.sent("POST", DATASETS)

    def test_a_time_that_is_not_one_is_refused(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError):
            add_dataset(
                name="Sales",
                query="select * from sales",
                repeat="daily",
                start_at="tomorrow",
                **ON_POSTGRES,
            )

        assert not api.sent("POST", DATASETS)

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
