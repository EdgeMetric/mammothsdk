"""A bad ``view transform batch`` step is named, and a bad operator is explained.

The steps are bound before anything is sent, so these need no service.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from mammoth_cli.commands.view_ops import _build_batch
from mammoth_cli.errors.envelope import CliError

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
