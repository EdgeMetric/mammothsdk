"""Real-code tests for the JSON-to-typed argument coercer.

These call the real coercer against real View-method signatures and assert it
produces the actual SDK dataclasses and enums (not raw dicts/strings), which is
exactly what the transform payload builders require. No mocks.
"""

from __future__ import annotations

from mammoth.models.pipeline import (
    BulkReplaceMapping,
    FillDirection,
    JoinKeySpec,
    JoinType,
)
from mammoth.view import View

from mammoth_cli.services.coerce import coerce_arguments


def test_bulk_replace_mapping_becomes_dataclass_list() -> None:
    """A list of dicts coerces to a list of BulkReplaceMapping."""
    coerced = coerce_arguments(
        View.bulk_replace,
        {"columns": ["Item"], "mapping": [{"search": ["a", "b"], "replace": "c"}]},
    )
    assert coerced["mapping"] == [BulkReplaceMapping(search=["a", "b"], replace="c")]
    assert isinstance(coerced["mapping"][0], BulkReplaceMapping)


def test_join_enum_and_key_specs_are_typed() -> None:
    """join coerces the enum string and the on/select union members."""
    coerced = coerce_arguments(
        View.join,
        {
            "foreign_view": 42,
            "join_type": "LEFT",
            "on": [{"left": "A", "right": "B"}],
            "select": ["Category"],
        },
    )
    assert coerced["join_type"] is JoinType.LEFT
    assert coerced["on"] == [JoinKeySpec(left="A", right="B")]
    assert coerced["foreign_view"] == 42  # int member of `int | View` is left alone
    assert coerced["select"] == ["Category"]


def test_fill_missing_direction_enum() -> None:
    """A plain direction string coerces to the FillDirection enum."""
    coerced = coerce_arguments(View.fill_missing, {"column": "A", "direction": "FIRST_VALUE"})
    assert coerced["direction"] is FillDirection.FIRST_VALUE


def test_condition_is_left_for_the_compiler() -> None:
    """The condition kwarg is passed through untouched for compile_condition."""
    spec = {"column": "A", "operator": "equals", "value": 1}
    coerced = coerce_arguments(View.filter_rows, {"condition": spec})
    assert coerced["condition"] == spec


def test_view_import_is_real() -> None:
    """Guard: the coercer is exercised against the real View class."""
    assert hasattr(View, "bulk_replace")
