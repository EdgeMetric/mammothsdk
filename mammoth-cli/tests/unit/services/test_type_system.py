"""Focused classification tests for OpenAPI request-body fallback."""

from __future__ import annotations

import typing
from typing import Any

import pytest
from mammoth import condition as _condition_module
from mammoth.view import View

from mammoth_cli.services.type_system import (
    TypeValidationError,
    is_opaque_mapping,
    json_schema,
    sample_value,
    validate_value,
)


def test_only_any_valued_mappings_are_opaque() -> None:
    assert is_opaque_mapping(dict[str, Any])
    assert is_opaque_mapping(dict[Any, Any])
    assert is_opaque_mapping(dict[str, Any] | None)
    assert not is_opaque_mapping(dict[str, str])
    assert not is_opaque_mapping(str)
    assert not is_opaque_mapping(str | None)


# --- resource references (review finding #7) -------------------------------
#
# ``join`` and friends annotate a dataview parameter as ``int | View``: in JSON
# it can only be expressed as a positive resource id. Before the fix, a union
# was validated member-by-member, so the bare ``int`` branch accepted a negative
# id like ``foreign_view=-1``; the server would then reject it. These tests pin
# that a resource reference (``View`` alone or in a union) must be a positive id.


@pytest.mark.parametrize("annotation", [View, int | View, View | None, int | View | None])
def test_resource_reference_rejects_non_positive_id(annotation: Any) -> None:
    with pytest.raises(TypeValidationError):
        validate_value(-1, annotation, "foreign_view")
    with pytest.raises(TypeValidationError):
        validate_value(0, annotation, "foreign_view")


@pytest.mark.parametrize("annotation", [View, int | View, View | None])
def test_resource_reference_accepts_positive_id(annotation: Any) -> None:
    assert validate_value(5, annotation, "foreign_view") == 5
    # A stringified id is coerced; a float that is integral is accepted.
    assert validate_value("7", annotation, "foreign_view") == 7
    assert validate_value(3.0, annotation, "foreign_view") == 3


def test_resource_reference_rejects_bool_and_non_numeric() -> None:
    with pytest.raises(TypeValidationError):
        validate_value(True, int | View, "foreign_view")
    with pytest.raises(TypeValidationError):
        validate_value("not-a-number", int | View, "foreign_view")


def test_resource_reference_schema_and_sample_are_positive_int() -> None:
    schema = json_schema(int | View)
    assert schema["type"] == "integer"
    assert schema["minimum"] == 1
    assert sample_value(int | View) == 1


def test_binary_io_is_constrained_to_a_path_string() -> None:
    # A ``BinaryIO`` upload parameter cannot be a live file object in JSON; it is
    # advertised and sampled as a path string, not an unconstrained document.
    schema = json_schema(typing.BinaryIO)
    assert schema["type"] == "string"
    assert schema["format"] == "path"
    assert sample_value(typing.BinaryIO) == "example.csv"


def test_plain_int_still_allows_any_integer() -> None:
    # Regression guard: the resource-reference rule must not tighten a plain
    # ``int`` field (which legitimately allows any integer, e.g. an offset).
    assert validate_value(-5, int, "offset") == -5


def test_condition_annotation_unaffected() -> None:
    # The resource-reference branch must not intercept condition annotations.
    schema = json_schema(_condition_module.Condition)
    assert schema and schema.get("type") != "integer"
