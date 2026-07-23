"""Unit tests for JSON-to-typed-argument coercion.

Exercises :func:`mammoth_cli.services.coerce.coerce_arguments` against real
bound SDK ``View`` methods and real SDK types, so the tests fail if coercion
ever crashes on or silently mangles a legitimate JSON-shaped argument.
"""

from __future__ import annotations

from mammoth.condition import Condition
from mammoth.models.pipeline import SetValue, SortDirection
from mammoth.view import View

from mammoth_cli.services.coerce import coerce_arguments


def test_union_str_or_enum_keeps_non_enum_string_and_coerces_valid_direction() -> None:
    """A column literally named like text that isn't a direction stays a string.

    ``View.limit_rows`` types its ``order_by`` elements as ``str |
    SortDirection``. A column name such as "Sales" is not a valid
    ``SortDirection`` member and must be coerced through unchanged as a plain
    string, while a valid direction string ("ASC") must become the enum
    member -- not raise ``ValueError`` from a failed blind enum construction.
    """
    result = coerce_arguments(
        View.limit_rows,
        {"n": 10, "order_by": [["Sales", "ASC"]]},
    )

    column, direction = result["order_by"][0]
    assert column == "Sales"
    assert isinstance(column, str)
    assert direction is SortDirection.ASC


def test_dataclass_condition_field_is_compiled_not_left_as_raw_dict() -> None:
    """A nested ``SetValue.condition`` dict becomes a real compiled Condition.

    ``SetValue.condition`` is typed ``Condition | CompoundCondition |
    NotCondition | None``, a forward reference resolvable only via the SDK
    type namespace. Coercion must both resolve that annotation and route the
    dict spec through ``compile_condition`` rather than passing it through
    raw.
    """
    result = coerce_arguments(
        View.set_values,
        {
            "values": [
                {
                    "value": "High",
                    "condition": {"column": "Sales", "operator": "GTE", "value": 10000},
                }
            ]
        },
    )

    set_value = result["values"][0]
    assert isinstance(set_value, SetValue)
    assert isinstance(set_value.condition, Condition)
    assert set_value.condition.column == "Sales"
    assert set_value.condition.operator == "GTE"
    assert set_value.condition.value == 10000
