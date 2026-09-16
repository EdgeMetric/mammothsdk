"""Independent typed task-pilot builder and wire controls."""

from unittest.mock import MagicMock

import pytest

from mammoth import Condition, Operator
from mammoth._pure.builders import (
    build_convert_params,
    build_filter_params,
    build_join_params,
    build_math_params,
)
from mammoth.api.pipeline import PipelineAPI
from mammoth.exceptions import MammothColumnError, MammothValidationError
from mammoth.models.pipeline import ColumnType, ConversionSpec, FilterType, JoinKeySpec, JoinType


def test_math_builder_transport_smoke_matches_literal_wire_shape() -> None:
    payload = build_math_params(
        "Price * Quantity",
        {"Price": "column_1", "Quantity": "column_2"},
        internal_names=["column_1", "column_2"],
        new_column="Total",
        name_gen=lambda: "column_3",
    )
    client = MagicMock()
    client.workspace_id = 1
    client.project_id = 2
    client._request_json.return_value = {"id": 9}
    client._wait_if_job.side_effect = lambda response, **_kwargs: response
    pipeline = PipelineAPI(client)
    pipeline.add_task(42, payload, dataset_id=7)
    client._request_json.assert_called_once_with(
        "POST",
        "/workspaces/1/projects/2/datasets/7/dataviews/42/pipeline/tasks",
        json={
            "DATAVIEW_ID": 42,
            "MATH": {
                "EXPRESSION": [
                    {"TYPE": "COLUMN", "VALUE": "column_1"},
                    {"TYPE": "OPERATOR", "VALUE": "*"},
                    {"TYPE": "COLUMN", "VALUE": "column_2"},
                ],
                "AS": {"COLUMN": "Total", "TYPE": "NUMERIC", "INTERNAL_NAME": "column_3"},
            },
        },
    )


def test_pilot_builders_emit_typed_backend_shapes() -> None:
    condition = Condition("Status", Operator.EQ, "Open")
    assert (
        build_filter_params(condition, {"Status": "column_1"}, filter_type=FilterType.SHOW)[
            "SELECT"
        ]
        == "ALL"
    )
    assert build_convert_params(
        [ConversionSpec(column="Amount", to=ColumnType.NUMERIC)],
        {"Amount": "column_2"},
        ["column_2"],
    ) == {"CONVERT": [{"SOURCE": "column_2", "TO_TYPE": "NUMERIC"}]}
    join = build_join_params(
        8,
        JoinType.INNER,
        [JoinKeySpec(left="Account", right="Account")],
        ["Name"],
        {"Account": "column_1"},
        ["column_1"],
        {"Account": "foreign_1", "Name": "foreign_2"},
        join_id="join_fixed",
    )
    assert join["JOIN"] == {
        "JOIN_ID": "join_fixed",
        "DATAVIEW_ID": 8,
        "TYPE": "INNER",
        "ON": [{"LEFT": "column_1", "RIGHT": "foreign_1"}],
        "SELECT": [{"COLUMN": "foreign_2", "ALIAS": "Name"}],
    }


def test_typed_builders_reject_unknown_or_unresolved_names() -> None:
    with pytest.raises((MammothValidationError, ValueError)):
        build_math_params("Price * Missing", {"Price": "column_1"}, internal_names=["column_1"])
    with pytest.raises((MammothValidationError, MammothColumnError)):
        build_join_params(
            8,
            JoinType.INNER,
            [JoinKeySpec(left="Unknown", right="Account")],
            ["Name"],
            {"Account": "column_1"},
            ["column_1"],
            {"Account": "foreign_1", "Name": "foreign_2"},
        )
