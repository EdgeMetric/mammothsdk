"""Replacing consecutive rules with one SQL rule: plan, generate, then one save."""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool, run

PROJECT, DATASET, VIEW = 3, 5, 9
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT, "dataset_id": DATASET, "view_id": VIEW}
VIEW_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"
PIPELINE = f"{VIEW_PATH}/pipeline"
TASKS = f"{PIPELINE}/tasks"
PLAN = f"{TASKS}/convert-to-sql/plan"
CONVERT = f"{TASKS}/convert-to-sql"
PREVIEW = f"{PIPELINE}/task_preview"
SQL_GENERATION = f"/workspaces/{WORKSPACE}/projects/{PROJECT}/sql_generation"
RUN_JOB = "/jobs/21"

# Rule numbers 1 to 6 have ids 11 to 16.
STEPS = [{"id": 10 + number, "sequence": number, "status": "executed"} for number in range(1, 7)]
GENERATED = {"response": {"status_code": "SQ01", "result": 'SELECT * FROM "view:9"'}}
SEEN = {"data": [{"a": 1}], "metadata": [{"display_name": "a"}]}
TEXT = "Keep orders from 2025 and add the total"


def a_view(api: FakeApi, draft_mode: str = "off") -> None:
    api.answer("GET", TASKS, {"tasks": STEPS})
    api.answer("GET", PIPELINE, {"draft_mode": draft_mode, "execution_state": "idle"})


def group(ids: list[int], text: str = TEXT, **more: Any) -> dict[str, Any]:
    return {"task_ids": ids, "text": text, **more}


class TestPlan:
    def test_it_speaks_in_rule_numbers_and_says_why_a_rule_stays(self) -> None:
        plan = {
            "groups": [{"task_ids": [11, 12, 13], "first_sequence": 1, "last_sequence": 3}],
            "cuts": [
                {"sequence": 4, "task_id": 14, "reason": "rule_type_not_supported"},
                {"sequence": 5, "task_id": None, "reason": "gate_between_rules"},
            ],
        }
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer("GET", PLAN, plan)
            answer = call_tool("plan_convert_to_sql", **IDS)

        assert answer["groups"] == [
            {"rules": "1 to 3", "first_rule": 1, "last_rule": 3, "task_ids": [11, 12, 13]}
        ]
        assert answer["kept_as_is"][0]["rule"] == 4
        assert "join" in answer["kept_as_is"][0]["why"]
        assert answer["boundaries"][0]["after_rule"] == 5
        assert "checkpoint" in answer["boundaries"][0]["why"]
        assert "rules 1 to 3" in answer["summary"]
        assert "task_ids" not in api.sent("GET", PLAN)[0].url.params

    def test_rule_numbers_are_sent_as_step_ids(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer("GET", PLAN, {"groups": [], "cuts": []})
            answer = call_tool("plan_convert_to_sql", rules=[2, 3], **IDS)

        [sent] = api.sent("GET", PLAN)
        assert sent.url.params.get_list("task_ids") == ["12", "13"]
        assert answer["groups"] == []
        assert answer["summary"] == "No rules can be merged into a SQL rule."

    def test_a_rule_number_the_view_does_not_have_is_refused_before_the_plan_is_asked(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            with pytest.raises(ToolError, match=r"no rule \[9\]"):
                call_tool("plan_convert_to_sql", rules=[1, 9], **IDS)

        assert api.sent("GET", PLAN) == []

    def test_a_server_without_the_route_says_so(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            with pytest.raises(ToolError, match="does not support convert-to-sql yet"):
                call_tool("plan_convert_to_sql", **IDS)


class TestGenerate:
    def test_it_passes_the_rules_and_the_text_and_saves_nothing(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer("POST", SQL_GENERATION, GENERATED)
            api.answer("POST", PREVIEW, SEEN)
            answer = call_tool("generate_convert_sql", groups=[group([12, 13])], **IDS)

        [asked] = api.sent("POST", SQL_GENERATION)
        assert api.body(asked)["params"] == {
            "intent": TEXT,
            "sequence_number": 2,
            "task_ids": [12, 13],
        }
        [previewed] = api.sent("POST", PREVIEW)
        spec = api.body(previewed)
        assert spec["SQL"] == {"USER_QUERY": 'SELECT * FROM "view:9"', "INTENT": TEXT}
        assert spec["SEQUENCE_NUMBER"] == 2
        [made] = answer["groups"]
        assert made["query"] == 'SELECT * FROM "view:9"'
        assert made["preview"] == SEEN
        assert api.sent("POST", CONVERT) == []
        assert api.sent("PATCH", TASKS) == []

    def test_a_blank_text_is_refused_and_nothing_is_sent(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="needs a `text`"):
            call_tool("generate_convert_sql", groups=[group([11, 12], "   ")], **IDS)

        assert api.requests == []

    def test_a_query_the_ai_could_not_write_gives_its_reason(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer(
                "POST",
                SQL_GENERATION,
                {"response": {"status_code": "SQ02", "detail": "no such column"}},
            )
            with pytest.raises(ToolError, match="no such column"):
                call_tool("generate_convert_sql", groups=[group([11, 12])], **IDS)

        assert api.sent("POST", PREVIEW) == []

    def test_a_step_of_another_view_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            with pytest.raises(ToolError, match="not in this view"):
                call_tool("generate_convert_sql", groups=[group([11, 99])], **IDS)

        assert api.sent("POST", SQL_GENERATION) == []


class TestConvert:
    @staticmethod
    def accepted(api: FakeApi, draft_mode: str = "off") -> None:
        a_view(api, draft_mode)
        api.answer("POST", CONVERT, {"job": {"id": 21}})
        api.answer("GET", RUN_JOB, {"job": {"id": 21, "status": "success", "response": {}}})

    def test_all_groups_go_in_one_request(self) -> None:
        groups = [
            group([11, 12], "Keep 2025", query="SELECT 1"),
            group([14, 15, 16], "Add totals", query="SELECT 2"),
        ]
        with a_fake_api() as api, as_caller():
            self.accepted(api)
            answer = call_tool("convert_to_sql", groups=groups, **IDS)

        [sent] = api.sent("POST", CONVERT)
        assert api.body(sent) == {
            "groups": [
                {"task_ids": [11, 12], "SQL": {"USER_QUERY": "SELECT 1", "INTENT": "Keep 2025"}},
                {
                    "task_ids": [14, 15, 16],
                    "SQL": {"USER_QUERY": "SELECT 2", "INTENT": "Add totals"},
                },
            ]
        }
        assert api.sent("DELETE", f"{TASKS}/11") == []
        assert answer["outcome"] == "converted"
        assert answer["mammoth_url"].endswith(f"/views/{VIEW}")

    def test_a_view_in_draft_mode_says_the_change_is_staged(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api, "dirty")
            api.answer("POST", CONVERT, {"status": "done", "type_of_modification": "x"})
            answer = call_tool("convert_to_sql", groups=[group([11, 12], query="SELECT 1")], **IDS)

        assert answer["outcome"] == "staged"
        assert "manage_draft" in answer["next_step"]

    @pytest.mark.parametrize("text", ["", "  \n"])
    def test_a_blank_text_is_refused_before_any_request(self, text: str) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="needs a `text`"):
            call_tool("convert_to_sql", groups=[group([11, 12], text, query="SELECT 1")], **IDS)

        assert api.requests == []

    def test_a_blank_query_is_refused_before_any_request(self) -> None:
        with a_fake_api() as api, as_caller(), pytest.raises(ToolError, match="needs `query`"):
            call_tool("convert_to_sql", groups=[group([11, 12], query=" ")], **IDS)

        assert api.requests == []

    def test_a_404_says_the_server_cannot_and_does_not_fall_back_to_deleting(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer("POST", CONVERT, {"message": "not found"}, status=404)
            with pytest.raises(ToolError) as refused:
                call_tool("convert_to_sql", groups=[group([11, 12], query="SELECT 1")], **IDS)

        assert "this server does not support convert-to-sql yet" in str(refused.value)
        assert "Do not delete the rules one by one" in str(refused.value)
        assert [r for r in api.requests if r.method == "DELETE"] == []
        assert len(api.sent("POST", CONVERT)) == 1

    def test_a_refusal_of_the_server_reaches_the_model_in_its_words(self) -> None:
        with a_fake_api() as api, as_caller():
            a_view(api)
            api.answer(
                "POST",
                CONVERT,
                {"message": "rules are not consecutive", "error_code": "4DTVW041"},
                status=400,
            )
            with pytest.raises(ToolError, match="not consecutive"):
                call_tool("convert_to_sql", groups=[group([11, 13], query="SELECT 1")], **IDS)


def test_the_tools_tell_the_model_never_to_delete_rules_one_by_one() -> None:
    register_tools()
    tools = {tool.name: tool for tool in run(mcp_server.list_tools())}

    for name in ("plan_convert_to_sql", "convert_to_sql"):
        assert "one by one" in (tools[name].description or ""), name
    assert "approv" in (tools["plan_convert_to_sql"].description or "")
