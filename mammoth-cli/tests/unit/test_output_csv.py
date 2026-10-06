"""``-o csv``: a result's rows through the real renderer, and a loud refusal without rows."""

from __future__ import annotations

import csv
import io
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENTS, CliError
from mammoth_cli.output.render import render


def _csv(data: Any) -> list[list[str]]:
    stream = io.StringIO()
    render({"schema_version": 1, "data": data, "meta": {}}, output="csv", stream=stream)
    return list(csv.reader(io.StringIO(stream.getvalue())))


def test_csv_writes_an_explore_result_as_header_and_one_line_per_bucket() -> None:
    result = {
        "data": [
            {"bucket": "North", "count": 3, "percentage": 60.0},
            {"bucket": "South", "count": 2, "percentage": 40.0},
        ],
        "range": {"column": "Region", "type": "TEXT", "min": None, "max": None},
    }
    assert _csv(result) == [
        ["bucket", "count", "percentage"],
        ["North", "3", "60.0"],
        ["South", "2", "40.0"],
    ]


def test_csv_quotes_commas_and_blanks_and_unions_columns_across_rows() -> None:
    rows = _csv([{"a": "x, y", "b": None}, {"a": "z", "c": 1}])
    assert rows == [["a", "b", "c"], ["x, y", "", ""], ["z", "", "1"]]


@pytest.mark.parametrize(
    "data", [[], {"data": []}, {"count": 3}, "text", None, [1, 2], {"data": [{"a": 1}, 5]}]
)
def test_csv_of_a_result_without_rows_fails_loud(data: Any) -> None:
    with pytest.raises(CliError) as caught:
        _csv(data)
    assert caught.value.code == CODE_INVALID_ARGUMENTS
