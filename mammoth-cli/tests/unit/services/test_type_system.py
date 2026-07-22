"""Focused classification tests for OpenAPI request-body fallback."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.type_system import is_opaque_mapping


def test_only_any_valued_mappings_are_opaque() -> None:
    assert is_opaque_mapping(dict[str, Any])
    assert is_opaque_mapping(dict[Any, Any])
    assert is_opaque_mapping(dict[str, Any] | None)
    assert not is_opaque_mapping(dict[str, str])
    assert not is_opaque_mapping(str)
    assert not is_opaque_mapping(str | None)
