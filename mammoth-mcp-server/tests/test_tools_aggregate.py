"""`aggregate_data`: Mammoth works out a total, count or average, so the model does not."""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool, run

PROJECT, DATASET, VIEW = 3, 5, 9
VIEW_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"
QUERY = f"{VIEW_PATH}/data/query"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "view_id": VIEW}
SALES_VIEW = {
    "id": VIEW,
    "name": "q1_sales_raw.csv",
    "metadata": [
        {"display_name": "Site", "internal_name": "column_1", "type": "TEXT"},
        {"display_name": "Revenue", "internal_name": "column_2", "type": "NUMERIC"},
        {"display_name": "Order Date", "internal_name": "column_3", "type": "DATE"},
    ],
}
REVENUE_BY_SITE = [{"column": "Revenue", "function": "SUM", "as_name": "Revenue"}]


def answers(api: FakeApi, rows: list[dict[str, Any]]) -> None:
    api.answer("GET", VIEW_PATH, SALES_VIEW)
    api.answer("POST", QUERY, {"data": rows})


def aggregate(**arguments: Any) -> dict[str, Any]:
    return dict(call_tool("aggregate_data", **IDS, **arguments))


class TestWhatIsAsked:
    def test_columns_are_named_as_the_user_sees_them_and_sent_by_internal_name(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [])
            aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"])

        (sent,) = api.sent("POST", QUERY)
        pivot = api.body(sent)["param"]["PIVOT"]
        assert pivot["SELECT"][0]["COLUMN"] == "column_2"
        assert pivot["GROUP_BY"] == [{"COLUMN": "column_1", "INTERNAL_NAME": "group_0"}]

    def test_a_date_is_grouped_by_the_period_asked_for(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [])
            aggregate(
                aggregations=REVENUE_BY_SITE,
                group_by=[{"column": "Order Date", "truncate": "month"}],
            )

        (sent,) = api.sent("POST", QUERY)
        group = api.body(sent)["param"]["PIVOT"]["GROUP_BY"][0]
        assert group == {"COLUMN": "column_3", "INTERNAL_NAME": "group_0", "TRUNCATE": "MONTH"}

    def test_the_groups_are_ranked_by_a_result_before_the_limit_cuts_them(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [])
            aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"], order_by="Revenue", limit=3)

        (sent,) = api.sent("POST", QUERY)
        assert api.body(sent)["display_properties"] == {"LIMIT": 3, "SORT": [["agg_0", "DESC"]]}

    def test_a_result_with_no_name_is_named_for_what_it_counts(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [{"agg_0": "10998.05", "agg_1": 240}])
            answer = aggregate(
                aggregations=[{"column": "Revenue", "function": "sum"}, {"function": "COUNT"}]
            )

        assert answer["data"] == [{"Sum of Revenue": 10998.05, "Count": 240}]


class TestWhatComesBack:
    def test_rows_are_keyed_by_the_group_column_and_the_result_names(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [{"group_0": "Cardiff", "agg_0": "2327.75"}])
            answer = aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"])

        assert answer["data"] == [{"Site": "Cardiff", "Revenue": 2327.75}]
        assert "note" not in answer

    def test_a_full_page_of_groups_says_there_may_be_more(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [{"group_0": "Cardiff", "agg_0": 1}, {"group_0": "Bath", "agg_0": 2}])
            answer = aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"], limit=2)

        assert "more groups" in answer["note"]

    def test_a_ranked_full_page_says_these_are_the_top_groups(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [{"group_0": "Cardiff", "agg_0": 2}, {"group_0": "Bath", "agg_0": 1}])
            answer = aggregate(
                aggregations=REVENUE_BY_SITE, group_by=["Site"], order_by="Revenue", limit=2
            )

        assert "top 2" in answer["note"]
        assert "order_by" not in answer["note"]

    def test_the_row_identity_mammoth_adds_is_left_out(self) -> None:
        # The query route adds `hash` to every row, as the data route does.
        with a_fake_api() as api, as_caller():
            answers(api, [{"group_0": "Cardiff", "agg_0": "2327.75", "hash": "991279133"}])
            answer = aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"])

        assert answer["data"] == [{"Site": "Cardiff", "Revenue": 2327.75}]

    def test_a_date_group_comes_back_as_a_valid_iso_time(self) -> None:
        # Mammoth writes the offset and then a `Z` as well, which no ISO reader takes.
        with a_fake_api() as api, as_caller():
            answers(api, [{"group_0": "2026-11-01T00:00:00+00:00Z", "agg_0": 1}])
            answer = aggregate(
                aggregations=REVENUE_BY_SITE,
                group_by=[{"column": "Order Date", "truncate": "MONTH"}],
            )

        assert answer["data"][0]["Order Date"] == "2026-11-01T00:00:00+00:00"


class TestWhatIsRefused:
    def test_a_column_the_view_does_not_have_is_named_with_the_ones_it_has(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [])
            with pytest.raises(ToolError) as refused:
                aggregate(aggregations=[{"column": "Profit", "function": "SUM"}])

        assert "Profit" in str(refused.value)
        assert "Site, Revenue, Order Date" in str(refused.value)
        assert not api.sent("POST", QUERY)

    def test_a_condition_on_a_column_the_view_does_not_have_is_refused(self) -> None:
        # Mammoth answers such a query with no rows, which reads as "none match".
        with a_fake_api() as api, as_caller():
            answers(api, [])
            with pytest.raises(ToolError, match="no column 'Site'") as refused:
                aggregate(aggregations=REVENUE_BY_SITE, condition={"Site": {"EQ": "a"}})

        assert "Site = column_1" in str(refused.value)
        assert api.sent("POST", QUERY) == []

    def test_ranking_by_a_name_that_is_not_a_result_names_the_ones_that_are(self) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [])
            with pytest.raises(ToolError) as refused:
                aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"], order_by="Total")

        assert "Revenue, Site" in str(refused.value)

    @pytest.mark.parametrize("limit", [0, -5])
    def test_a_limit_below_one_is_refused_before_the_query_is_sent(self, limit: int) -> None:
        with a_fake_api() as api, as_caller():
            answers(api, [])
            with pytest.raises(ToolError) as refused:
                aggregate(aggregations=REVENUE_BY_SITE, group_by=["Site"], limit=limit)

        assert "at least 1" in str(refused.value)
        assert not api.sent("POST", QUERY)


def test_it_reads_and_changes_nothing() -> None:
    # A read-only connection may run it, and a client runs it without asking.
    register_tools()
    (tool,) = [t for t in run(mcp_server.list_tools()) if t.name == "aggregate_data"]
    assert tool.annotations.read_only_hint is True
