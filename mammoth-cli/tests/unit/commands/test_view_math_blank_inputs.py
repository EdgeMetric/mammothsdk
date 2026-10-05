"""A math step over a column with blanks says so: Mammoth computes a blank
input as 0, so ``qty * unit_price`` gives revenue 0 for an unpriced order and
a later total counts it at $0 with no warning (FB-01)."""

from __future__ import annotations

import json
from typing import Any

from mammoth_cli.commands import view_ops

_VIEW = {
    "id": 7,
    "row_count": 20,
    "metadata": [
        {"display_name": "qty", "internal_name": "column_7", "type": "NUMERIC"},
        {"display_name": "unit_price", "internal_name": "column_8", "type": "NUMERIC"},
        {"display_name": "notes", "internal_name": "column_11", "type": "TEXT"},
    ],
}


class _FakeService:
    """``unit_price`` has one blank cell; ``qty`` has none."""

    def __init__(self) -> None:
        self.counted: list[str] = []

    def call(self, symbol: str, **kwargs: Any) -> Any:
        if "condition" not in kwargs:
            return _VIEW
        sent = json.dumps(kwargs["condition"])
        self.counted.append(sent)
        return {"data": [{"agg_0": 1 if "column_8" in sent else 0}]}


def test_blank_inputs_counts_only_the_columns_the_expression_names() -> None:
    service = _FakeService()

    blanks = view_ops._blank_math_inputs(service, 4, 7, 1, "qty * unit_price")

    assert blanks == {"unit_price": 1}
    assert not any("column_11" in sent for sent in service.counted)


def test_the_result_names_the_blank_inputs() -> None:
    data = view_ops._with_blank_input_note({"status": "done"}, {"unit_price": 1})

    assert data["blank_inputs"] == {
        "columns": {"unit_price": 1},
        "note": "A blank input counts as 0 in this math step: unit_price is blank in 1 "
        "row(s), so the result there is computed as if it were 0. Fill or filter those "
        "rows first if a blank must not count as 0.",
    }


def test_no_blank_inputs_leaves_the_result_unchanged() -> None:
    assert view_ops._with_blank_input_note({"status": "done"}, {}) == {"status": "done"}
