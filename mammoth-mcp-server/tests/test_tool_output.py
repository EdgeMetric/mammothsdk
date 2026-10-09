"""What a model reads back from the read tools, on answers recorded from a real Mammoth.

The shapes below are what a Mammoth server answered (koyal, 9 Oct 2026): rows
under internal names with every value as text, a `total` of 0, a `next` link
after every page, and one 404 for any missing id.
"""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.sdk import set_api_url

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool

PROJECT, DATASET, VIEW = 3, 5, 9
VIEWS = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews"
VIEW_PATH = f"{VIEWS}/{VIEW}"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET}
RECORDED_VIEW = {
    "id": VIEW,
    "name": "View 1",
    "ds_id": DATASET,
    "display_properties": {"SORT": [], "COLUMN_ORDER": {"0": "column_0"}},
    "metadata": [
        {
            "type": "NUMERIC",
            "display_name": "doc_count",
            "internal_name": "column_0",
            "format": None,
            "min": "1.000000",
            "max": "3454.000000",
            "lineage": {"origin": "SOURCE", "task_id": None},
        },
        {
            "type": "TEXT",
            "display_name": "key.task",
            "internal_name": "column_1",
            "format": None,
            "lineage": {"origin": "SOURCE", "task_id": None},
        },
    ],
    "sys_cols": [{"display_name": "Batch ID", "internal_name": "batch_id"}],
    "status": "ready",
    "row_count": 3,
    "column_count": 2,
    "dependencies_info": {"dependents": {}, "dependees": {}},
}
NOT_FOUND = {"detail": "Invalid resource id or given resource id does not exist."}


def rows(count: int) -> dict:
    data = [{"column_0": str(n), "column_1": "handle_file"} for n in range(1, count + 1)]
    return {"data": data, "paging": {"offset": 1, "count": count, "total": 0, "limit": 2}}


class TestGetData:
    def test_rows_use_display_names_and_numbers_and_say_what_is_left(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{VIEW_PATH}/data", rows(2))
            api.answer("GET", VIEW_PATH, RECORDED_VIEW)
            answer = call_tool("get_data", view_id=VIEW, limit=2, **IDS)

        assert answer["data"] == [
            {"doc_count": 1, "key.task": "handle_file"},
            {"doc_count": 2, "key.task": "handle_file"},
        ]
        assert answer["paging"] == {
            "offset": 1,
            "count": 2,
            "limit": 2,
            "total": 3,
            "next_offset": 3,
        }

    def test_a_key_the_api_adds_beside_data_and_paging_is_kept(self) -> None:
        answer_with_extra = {**rows(2), "warnings": ["column hidden"]}
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{VIEW_PATH}/data", answer_with_extra)
            api.answer("GET", VIEW_PATH, RECORDED_VIEW)
            answer = call_tool("get_data", view_id=VIEW, limit=2, **IDS)

        assert answer["warnings"] == ["column hidden"]
        assert answer["paging"]["total"] == 3

    def test_the_last_page_has_the_real_total_and_no_next(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{VIEW_PATH}/data", rows(1))
            api.answer("GET", VIEW_PATH, RECORDED_VIEW)
            answer = call_tool("get_data", view_id=VIEW, limit=2, offset=3, **IDS)

        assert answer["paging"] == {"offset": 3, "count": 1, "limit": 2, "total": 3}

    def test_a_missing_view_is_named_with_the_tool_that_lists_views(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("POST", f"{VIEW_PATH}/data", NOT_FOUND, status=404)
            api.answer("GET", VIEW_PATH, NOT_FOUND, status=404)
            with pytest.raises(ToolError) as refused:
                call_tool("get_data", view_id=VIEW, **IDS)

        assert f"view {VIEW}" in str(refused.value)
        assert "list_views" in str(refused.value)


class TestGetView:
    def test_the_view_is_cut_to_identity_size_and_columns(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEW_PATH, RECORDED_VIEW)
            view = call_tool("get_view", view_id=VIEW, **IDS)

        assert set(view) == {
            "id",
            "name",
            "ds_id",
            "status",
            "row_count",
            "column_count",
            "metadata",
        }
        assert view["metadata"][0] == {
            "display_name": "doc_count",
            "internal_name": "column_0",
            "type": "NUMERIC",
            "min": "1.000000",
            "max": "3454.000000",
        }


class TestPaging:
    def test_a_short_page_has_no_next_link(self) -> None:
        page = {
            "dataviews": [{"id": VIEW}],
            "offset": 0,
            "limit": 50,
            "next": "http://koyal.mammoth.io/x?limit=50&offset=50",
        }
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEWS, page)
            answer = call_tool("list_views", **IDS)

        assert "next" not in answer

    def test_a_full_page_keeps_its_next_link(self) -> None:
        page = {
            "dataviews": [{"id": 1}, {"id": 2}],
            "offset": 0,
            "limit": 2,
            "next": "http://koyal.mammoth.io/x?limit=2&offset=2",
        }
        with a_fake_api() as api, as_caller():
            api.answer("GET", VIEWS, page)
            answer = call_tool("list_views", limit=2, **IDS)

        assert answer["next"] == page["next"]

    def test_the_next_link_is_secure_when_the_api_is(self) -> None:
        page = {
            "dataviews": [{"id": 1}, {"id": 2}],
            "next": "http://koyal.mammoth.io/x?limit=2&offset=2",
        }
        with a_fake_api() as api, as_caller():
            set_api_url("https://koyal.mammoth.io")
            api.answer("GET", VIEWS, page)
            answer = call_tool("list_views", limit=2, **IDS)

        assert answer["next"].startswith("https://koyal.mammoth.io/")
