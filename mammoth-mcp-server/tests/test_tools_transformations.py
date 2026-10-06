"""Whether a pipeline change was made, and what a model is told about operations."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mammoth_mcp_server.server import mcp_server, register_tools
from mammoth_mcp_server.tools.transformations import _OPERATIONS, check_change, check_run

from .helpers import as_caller, call_tool, run


class TestPipelineChangeOutcome:
    """Whether a pipeline change was made.

    Mammoth rejects a change up front only for a dependency violation, which no
    single fresh view can produce, so the refusals are checked on the change
    itself.
    """

    @pytest.mark.parametrize(
        "change",
        [
            {
                "status": "error",
                "future_id": None,
                "error_info": {"reason": "depends on a deleted column"},
            },
            {
                "status": "processing",
                "future_id": None,
                "error_info": {"reason": "no run to wait for"},
            },
            {
                "status": "done",
                "has_error": True,
                "future_id": None,
                "error_info": {"reason": "bad ref"},
            },
        ],
        ids=["rejected", "processing-without-a-run", "staged-with-reference-error"],
    )
    def test_a_change_that_was_not_made_is_refused(self, change: dict) -> None:
        with pytest.raises(ToolError, match=change["error_info"]["reason"]):
            check_change(change)

    def test_a_failed_run_names_only_the_tasks_that_failed(self) -> None:
        # A run reports every task it ran; the real failing run above has only
        # one, so a clean task next to a failed one is checked here.
        run = {
            "has_error": True,
            "taskwise_execution_result": {
                "1": {"error_details": None},
                "2": {"error_details": {"exception": "boom"}},
            },
        }

        with pytest.raises(ToolError, match="failed to run") as refused:
            check_run(run, "The pipeline")

        assert "boom" in str(refused.value)
        assert "None" not in str(refused.value)


class TestTransformationSchema:
    def test_the_schema_of_an_operation_lists_its_arguments(self) -> None:
        with as_caller():
            schema = call_tool("get_transformation_schema", operation="limit")

        assert {"op", "n", "bottom"} <= set(schema["properties"])
        assert "n" in schema["required"]

    def test_an_unknown_operation_names_the_operations_that_exist(self) -> None:
        with as_caller(), pytest.raises(ToolError, match="limit") as refused:
            call_tool("get_transformation_schema", operation="pivot2")

        assert "unnest" in str(refused.value)

    def test_the_tool_description_names_every_operation(self) -> None:
        # The model picks an operation from the description, so every one the
        # server supports has to be there.
        register_tools()
        tools = {tool.name: tool for tool in run(mcp_server.list_tools())}
        description = tools["add_transformations"].description or ""

        assert len(_OPERATIONS) == 29
        for operation in _OPERATIONS:
            assert operation in description
