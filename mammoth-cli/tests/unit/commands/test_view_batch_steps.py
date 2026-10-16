"""A bad ``view transform batch`` step is named, and a bad operator is explained.

The steps are bound before anything is sent, so these need no service.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from mammoth import CopySpec, SplitColumnSpec, View

from mammoth_cli.commands.view_ops import _batch_steps, _build_batch, _created_columns
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.sdk_service import add_columns_to_view

_BAD_OPERATOR = {"column": "Status", "operator": "NOT_EQUALS", "value": "x"}


def _build(steps: list[dict[str, Any]]) -> None:
    _build_batch(SimpleNamespace(command_id="view.transform.batch"), object(), 1, 2, steps)  # type: ignore[arg-type]


def test_a_step_missing_a_required_field_is_named() -> None:
    steps = [
        {"op": "sort", "input": {"order_by": [{"column": "A", "direction": "ASC"}]}},
        {"op": "sort", "input": {"columns": ["A"]}},
    ]
    with pytest.raises(CliError) as excinfo:
        _build(steps[1:])
    error = excinfo.value
    assert error.message.startswith("steps[0] (sort): ")
    assert "order_by" in error.message
    assert error.details["step_index"] == 0 and error.details["op"] == "sort"


@pytest.mark.parametrize(
    ("op", "field"),
    [("filter", "condition"), ("set-values", "condition")],
)
def test_a_bad_operator_in_a_step_names_the_step_and_the_closest_operator(
    op: str, field: str
) -> None:
    payload: dict[str, Any] = {field: _BAD_OPERATOR}
    if op == "set-values":
        payload["values"] = [{"column": "Status", "value": "y"}]
    with pytest.raises(CliError) as excinfo:
        _build([{"op": op, "input": payload}])
    error = excinfo.value
    assert error.message.startswith(f"steps[0] ({op}): ")
    assert "NOT_EQUALS" in error.message and "Did you mean NE?" in error.message
    assert error.details["step_index"] == 0 and error.details["op"] == op
    assert "NE" in error.details["accepted"]


@pytest.mark.parametrize("op", ["split", "unnest", "pivot"])
def test_a_batch_takes_split_unnest_and_pivot_as_its_last_step(op: str) -> None:
    steps = [{"op": "limit-rows", "input": {"n": 3}}, {"op": op, "input": {}}]

    assert _batch_steps({"steps": steps}) == steps


def test_a_batch_takes_a_split_before_other_steps() -> None:
    steps = [{"op": "split", "input": {}}, {"op": "limit-rows", "input": {"n": 3}}]

    assert _batch_steps({"steps": steps}) == steps


@pytest.mark.parametrize("op", ["unnest", "pivot"])
def test_a_step_that_replaces_the_columns_must_be_last(op: str) -> None:
    with pytest.raises(CliError) as excinfo:
        _batch_steps({"steps": [{"op": op, "input": {}}, {"op": "limit-rows", "input": {"n": 3}}]})
    assert excinfo.value.message.startswith(f"steps[0] ({op})")
    assert excinfo.value.details == {"step": 0, "op": op}


def _view() -> View:
    metadata = [
        {"internal_name": "column_actors", "display_name": "Top Actors", "type": "TEXT"},
        {"internal_name": "column_year", "display_name": "Year", "type": "NUMERIC"},
    ]
    return View(None, {"id": 1, "metadata": metadata}, 2)


def _built(view: View, method: str, **kwargs: Any) -> dict[str, Any]:
    with view.build_only():
        return asyncio.run(getattr(view, method)(**kwargs))["task_spec"]


def test_split_then_trim_the_split_columns_then_unnest_passes_validation() -> None:
    view = _view()
    split = _built(
        view,
        "split_column",
        column="Top Actors",
        delimiter=",",
        new_columns=[SplitColumnSpec("Actor 1"), SplitColumnSpec("Actor 2")],
    )
    steps = [
        {"op": "split", "input": {}},
        {"op": "text", "input": {}},
        {"op": "unnest", "input": {}},
    ]
    assert _batch_steps({"steps": steps}) == steps

    add_columns_to_view(view, _created_columns(split))
    trim = _built(view, "text_transform", columns=["Actor 1", "Actor 2"], trim=True)
    unnest = _built(view, "unnest", columns=["Actor 1", "Actor 2"])

    assert trim["TEXT_TRANSFORM"]
    assert unnest["UNNEST"]["COLUMNS"][0]["COLUMN"] == split["SPLIT"]["AS"][0]["INTERNAL_NAME"]


def test_a_column_a_split_creates_is_unknown_to_a_view_that_was_not_told() -> None:
    view = _view()
    split = _built(
        view,
        "split_column",
        column="Top Actors",
        delimiter=",",
        new_columns=[SplitColumnSpec("A1")],
    )
    assert _created_columns(split)[0]["COLUMN"] == "A1"

    with pytest.raises(Exception, match="A1"):
        _built(view, "text_transform", columns=["A1"], trim=True)


def test_a_copy_columns_new_column_is_carried_to_later_steps() -> None:
    view = _view()
    copy = _built(view, "copy_columns", copies=[CopySpec("Year", as_name="Year 2")])
    add_columns_to_view(view, _created_columns(copy))

    assert view.columns["Year 2"] == _created_columns(copy)[0]["INTERNAL_NAME"]
    assert view.column_types["Year 2"] == _created_columns(copy)[0]["TYPE"]


@pytest.mark.parametrize("last", ["unnest", "pivot"])
def test_a_sort_before_a_step_that_replaces_the_columns_is_refused(last: str) -> None:
    steps = [{"op": "sort", "input": {"order_by": [["A", "ASC"]]}}, {"op": last, "input": {}}]
    with pytest.raises(CliError) as excinfo:
        _batch_steps({"steps": steps})
    assert excinfo.value.message.startswith("steps[0] (sort)")
