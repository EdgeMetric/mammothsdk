"""Turning an operation into the task the pipeline route takes.

The builder reads everything through the caller's SDK client: the view's
columns, a joined view's columns and the query the AI writes. So the client is
the one thing stubbed here, and what is checked is what the builder asks it and
what it makes of the answers.
"""

import typing
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from mammoth.exceptions import MammothColumnError, MammothValidationError
from pydantic import TypeAdapter

from mammoth_mcp_server.consts import ApiFields, TaskFields
from mammoth_mcp_server.task_params import (
    _FOREIGN_OPERATION_BUILDERS,
    _OPERATION_BUILDERS,
    build_task_param,
)
from mammoth_mcp_server.transform_operations import TransformOperation

from .helpers import run

DATASET = 5
VIEW = 9
OTHER_VIEW = 12
OTHER_DATASET = 6

OPERATION: TypeAdapter[TransformOperation] = TypeAdapter(TransformOperation)


def a_column(display: str, internal: str, kind: str = "TEXT") -> dict:
    return {"display_name": display, "internal_name": internal, "type": kind}


SALES = [a_column("Region", "column_1"), a_column("Amount", "column_2", "NUMERIC")]
REGIONS = [a_column("Code", "column_a"), a_column("Manager", "column_b")]


def a_client(views: dict[int, dict]) -> MagicMock:
    """A client whose views answer a full read with what the test gives them."""
    client = MagicMock()

    async def read_view(dataset_id: int, view_id: int, **asked: Any) -> dict:
        assert asked == {"fields": ApiFields.FULL}
        return {"id": view_id, **views[view_id]}

    client.dataviews.get = AsyncMock(side_effect=read_view)
    client.pipeline.find_dataset_for_dataview = AsyncMock(return_value=OTHER_DATASET)
    client.pipeline.latest_task_sequence = AsyncMock(return_value=0)
    return client


def build(client: MagicMock, operation: dict) -> dict:
    return run(build_task_param(client, OPERATION.validate_python(operation), DATASET, VIEW))


class TestAStepBuiltFromTheViewsColumns:
    def test_a_column_is_named_by_its_display_name_and_sent_by_its_internal_one(self) -> None:
        client = a_client({VIEW: {"metadata": SALES}})

        param = build(client, {"op": "delete", "columns": ["Region"]})

        assert "column_1" in str(param)
        assert "Region" not in str(param)

    def test_the_step_names_the_view_it_is_for(self) -> None:
        client = a_client({VIEW: {"metadata": SALES}})

        assert build(client, {"op": "limit", "n": 2})[TaskFields.DATAVIEW_ID] == VIEW

    def test_a_column_a_staged_step_adds_can_be_used_by_the_next_step(self) -> None:
        # Only the full read lists the columns each step leaves, staged steps
        # included; the plain metadata lists the columns of the data that exists.
        staged = [*SALES, a_column("Added", "column_3")]
        client = a_client(
            {
                VIEW: {
                    "metadata": SALES,
                    "taskwise_info": {"0": {"metadata": SALES}, "1": {"metadata": staged}},
                }
            }
        )

        param = build(client, {"op": "delete", "columns": ["Added"]})

        assert "column_3" in str(param)

    def test_a_column_the_view_does_not_have_is_refused_by_name(self) -> None:
        client = a_client({VIEW: {"metadata": SALES}})

        with pytest.raises(MammothColumnError, match="No such column"):
            build(client, {"op": "delete", "columns": ["No such column"]})


class TestAStepThatReadsASecondView:
    LOOKUP = {
        "op": "lookup",
        "foreign_view_id": OTHER_VIEW,
        "source": "Region",
        "key": "Code",
        "value": "Manager",
        "new_column": "Manager",
    }

    def test_the_second_views_columns_are_read_as_the_caller(self) -> None:
        # Read through the API, the second view is refused to a caller who may
        # not see it, exactly as the first is.
        client = a_client({VIEW: {"metadata": SALES}, OTHER_VIEW: {"metadata": REGIONS}})

        param = build(client, self.LOOKUP)

        client.pipeline.find_dataset_for_dataview.assert_awaited_once_with(OTHER_VIEW)
        assert "column_a" in str(param)
        assert "column_b" in str(param)

    def test_a_second_view_the_project_does_not_hold_is_refused(self) -> None:
        client = a_client({VIEW: {"metadata": SALES}})
        client.pipeline.find_dataset_for_dataview.side_effect = ValueError(
            "Dataview 12 not found in the project"
        )

        with pytest.raises(MammothValidationError, match="Dataview 12 not found"):
            build(client, self.LOOKUP)


class TestAStepTheAiWrites:
    SQL = {"op": "sql", "intent": "keep every row"}

    @staticmethod
    def an_ai(response: dict, steps: int = 0) -> MagicMock:
        client = a_client({})
        client.pipeline.latest_task_sequence = AsyncMock(return_value=steps)
        client.ai.generate_sql = AsyncMock(return_value={"response": response})
        return client

    def test_the_query_is_asked_for_the_step_after_the_views_last(self) -> None:
        client = self.an_ai({"status_code": "SQ01", "result": "SELECT 1"}, steps=2)

        param = build(client, self.SQL)

        client.ai.generate_sql.assert_awaited_once_with(
            "keep every row", sequence_number=3, dataset_id=DATASET, dataview_id=VIEW
        )
        assert "SELECT 1" in str(param)

    def test_a_query_the_ai_could_not_write_is_refused_with_its_reason(self) -> None:
        client = self.an_ai({"status_code": "SQ02", "detail": "no column holds a price"})

        with pytest.raises(MammothValidationError, match="no column holds a price"):
            build(client, self.SQL)

    def test_a_refusal_with_no_reason_still_says_what_to_do(self) -> None:
        client = self.an_ai({"status_code": "SQ02"})

        with pytest.raises(MammothValidationError, match="Rephrase"):
            build(client, self.SQL)


def test_every_operation_has_a_builder() -> None:
    # An operation the schema offers and no builder takes would be accepted
    # from the model and then fail with a KeyError.
    offered = {
        model.model_fields["op"].default
        for model in typing.get_args(typing.get_args(TransformOperation)[0])
    }

    assert offered == {*_OPERATION_BUILDERS, *_FOREIGN_OPERATION_BUILDERS, "sql"}
