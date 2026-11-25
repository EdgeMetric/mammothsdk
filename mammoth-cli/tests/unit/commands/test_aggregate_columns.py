"""``view data aggregate`` takes either spelling of a column (mammothsdk#438)."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.view.aggregate import AggregateSource, aggregate_on, with_known_columns
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.read_queries import ReadContext

_COLUMNS = {"engaged_visitors": "column_a1", "landing page": "column_b2"}


def test_spaces_internal_names_and_display_names_all_resolve() -> None:
    document = {
        "aggregations": [{"column": "engaged visitors", "function": "SUM"}],
        "group_by": ["column_b2", {"column": "Landing_Page"}],
    }
    out = with_known_columns(document, _COLUMNS)
    assert out["aggregations"][0]["column"] == "engaged_visitors"
    assert out["group_by"] == ["landing page", {"column": "landing page"}]


def test_an_unknown_column_is_named_with_the_valid_ones() -> None:
    with pytest.raises(CliError) as excinfo:
        with_known_columns({"metric": {"column": "visits", "function": "SUM"}}, _COLUMNS)
    assert excinfo.value.code == "unknown_column"
    assert excinfo.value.details["valid_columns"] == ["engaged_visitors", "landing page"]


def test_no_column_map_leaves_the_document_alone() -> None:
    document = {"metric": {"column": "anything", "function": "COUNT"}}
    assert with_known_columns(document, {}) is document


def test_aggregate_on_refuses_an_unknown_column_before_any_read() -> None:
    # Through the real handler path: dropping the with_known_columns call in aggregate_on
    # lets the name through to the backend as a bare "Job failed".
    reads = ReadContext(None, 1, 7, 180, dict(_COLUMNS), {"engaged_visitors": "NUMBER"}, None, None)
    source = AggregateSource(reads, {}, {})
    with pytest.raises(CliError) as excinfo:
        aggregate_on(source, "unused", {"metric": {"column": "visits", "function": "SUM"}})
    assert excinfo.value.code == "unknown_column"
