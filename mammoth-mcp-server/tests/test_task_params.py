"""Turning an operation into the task the pipeline route takes.

The builder reads everything through the caller's SDK client: the view's
columns, a joined view's columns and the query the AI writes. The client is
real; only its HTTP transport is replaced, so what is checked is what the
builder asks the API and what it makes of the answers.
"""

import typing

import pytest
from mammoth.exceptions import MammothColumnError, MammothValidationError
from pydantic import TypeAdapter

from mammoth_mcp_server.consts import ApiFields, TaskFields
from mammoth_mcp_server.sdk import build_client
from mammoth_mcp_server.task_params import (
    _FOREIGN_OPERATION_BUILDERS,
    _OPERATION_BUILDERS,
    build_task_param,
)
from mammoth_mcp_server.transform_operations import TransformOperation

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, run

PROJECT = 3
DATASET = 5
VIEW = 9
OTHER_VIEW = 12
OTHER_DATASET = 6
PROJECT_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}"
SQL_GENERATION = f"{PROJECT_PATH}/sql_generation"

OPERATION: TypeAdapter[TransformOperation] = TypeAdapter(TransformOperation)


def a_column(display: str, internal: str, kind: str = "TEXT") -> dict:
    return {"display_name": display, "internal_name": internal, "type": kind}


SALES = [a_column("Region", "column_1"), a_column("Amount", "column_2", "NUMERIC")]
REGIONS = [a_column("Code", "column_a"), a_column("Manager", "column_b")]


def view_path(dataset_id: int, view_id: int) -> str:
    return f"{PROJECT_PATH}/datasets/{dataset_id}/dataviews/{view_id}"


def a_view(api: FakeApi, dataset_id: int, view_id: int, read: dict) -> None:
    """Answer a read of one view with what the test gives it."""
    api.answer("GET", view_path(dataset_id, view_id), {"id": view_id, **read})


def build(api: FakeApi, operation: dict) -> dict:
    """Build the task through a real client over `api`, as the caller."""

    async def built() -> dict:
        async with build_client(WORKSPACE, PROJECT) as client:
            return await build_task_param(
                client, OPERATION.validate_python(operation), DATASET, VIEW
            )

    with as_caller():
        return typing.cast(dict, run(built()))


class TestAStepBuiltFromTheViewsColumns:
    def test_a_column_is_named_by_its_display_name_and_sent_by_its_internal_one(self) -> None:
        with a_fake_api() as api:
            a_view(api, DATASET, VIEW, {"metadata": SALES})
            param = build(api, {"op": "delete", "columns": ["Region"]})

        assert "column_1" in str(param)
        assert "Region" not in str(param)
        [read] = api.sent("GET", view_path(DATASET, VIEW))
        assert read.url.params["fields"] == ApiFields.FULL

    def test_the_step_names_the_view_it_is_for(self) -> None:
        with a_fake_api() as api:
            a_view(api, DATASET, VIEW, {"metadata": SALES})
            param = build(api, {"op": "limit", "n": 2})

        assert param[TaskFields.DATAVIEW_ID] == VIEW

    def test_a_column_a_staged_step_adds_can_be_used_by_the_next_step(self) -> None:
        # Only the full read lists the columns each step leaves, staged steps
        # included; the plain metadata lists the columns of the data that exists.
        staged = [*SALES, a_column("Added", "column_3")]
        with a_fake_api() as api:
            a_view(
                api,
                DATASET,
                VIEW,
                {
                    "metadata": SALES,
                    "taskwise_info": {"0": {"metadata": SALES}, "1": {"metadata": staged}},
                },
            )
            param = build(api, {"op": "delete", "columns": ["Added"]})

        assert "column_3" in str(param)

    def test_a_column_the_view_does_not_have_is_refused_by_name(self) -> None:
        with a_fake_api() as api:
            a_view(api, DATASET, VIEW, {"metadata": SALES})
            with pytest.raises(MammothColumnError, match="No such column"):
                build(api, {"op": "delete", "columns": ["No such column"]})


class TestAStepThatReadsASecondView:
    LOOKUP = {
        "op": "lookup",
        "foreign_view_id": OTHER_VIEW,
        "source": "Region",
        "key": "Code",
        "value": "Manager",
        "new_column": "Manager",
    }
    OTHER_VIEW_RESOURCE = f"{PROJECT_PATH}/resources/dataview/{OTHER_VIEW}"

    def test_the_second_views_columns_are_read_as_the_caller(self) -> None:
        # Read through the API, the second view is refused to a caller who may
        # not see it, exactly as the first is.
        with a_fake_api() as api:
            a_view(api, DATASET, VIEW, {"metadata": SALES})
            api.answer(
                "GET", self.OTHER_VIEW_RESOURCE, {"resource": {"dataset": {"id": OTHER_DATASET}}}
            )
            a_view(api, OTHER_DATASET, OTHER_VIEW, {"metadata": REGIONS})
            param = build(api, self.LOOKUP)

        assert len(api.sent("GET", view_path(OTHER_DATASET, OTHER_VIEW))) == 1
        assert "column_a" in str(param)
        assert "column_b" in str(param)

    def test_a_second_view_the_project_does_not_hold_is_refused(self) -> None:
        with a_fake_api() as api:
            a_view(api, DATASET, VIEW, {"metadata": SALES})
            api.answer("GET", self.OTHER_VIEW_RESOURCE, {"message": "not found"}, status=404)
            with pytest.raises(MammothValidationError, match="Dataview 12 not found"):
                build(api, self.LOOKUP)


class TestAStepTheAiWrites:
    SQL = {"op": "sql", "intent": "keep every row"}

    @staticmethod
    def an_ai(api: FakeApi, response: dict, steps: int = 0) -> None:
        """A view with `steps` steps, and an AI that answers `response`."""
        items = [
            {"item_type": "task", "sequence": sequence, "status": "executed"}
            for sequence in range(1, steps + 1)
        ]
        api.answer("GET", f"{view_path(DATASET, VIEW)}/pipeline/items", {"items": items})
        api.answer("POST", SQL_GENERATION, {"response": response})

    def test_the_query_is_asked_for_the_step_after_the_views_last(self) -> None:
        with a_fake_api() as api:
            self.an_ai(api, {"status_code": "SQ01", "result": "SELECT 1"}, steps=2)
            param = build(api, self.SQL)

        [asked] = api.sent("POST", SQL_GENERATION)
        assert api.body(asked)["params"] == {"intent": "keep every row", "sequence_number": 3}
        assert asked.url.params["dataset_id"] == str(DATASET)
        assert asked.url.params["dataview_id"] == str(VIEW)
        assert "SELECT 1" in str(param)

    def test_a_query_the_ai_could_not_write_is_refused_with_its_reason(self) -> None:
        with a_fake_api() as api:
            self.an_ai(api, {"status_code": "SQ02", "detail": "no column holds a price"})
            with pytest.raises(MammothValidationError, match="no column holds a price"):
                build(api, self.SQL)

    def test_a_refusal_with_no_reason_still_says_what_to_do(self) -> None:
        with a_fake_api() as api:
            self.an_ai(api, {"status_code": "SQ02"})
            with pytest.raises(MammothValidationError, match="Rephrase"):
                build(api, self.SQL)


def test_every_operation_has_a_builder() -> None:
    # An operation the schema offers and no builder takes would be accepted
    # from the model and then fail with a KeyError.
    offered = {
        model.model_fields["op"].default
        for model in typing.get_args(typing.get_args(TransformOperation)[0])
    }

    assert offered == {*_OPERATION_BUILDERS, *_FOREIGN_OPERATION_BUILDERS, "sql"}
