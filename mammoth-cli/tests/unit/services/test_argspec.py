"""Unit tests for the type/enum/default enrichment added to argspec.FieldSpec.

These resolve real ``sdk_symbol`` values against the real SDK (and one
CLI-internal helper) and assert the derived field metadata — the addition
schema discovery (R7) and ``--input`` type coercion (R6) both depend on.
No mocks: the point is that the metadata tracks the live signatures.
"""

from __future__ import annotations

from mammoth_cli.services.argspec import arg_spec, render_type_name, unwrap_optional

_TEXT_TRANSFORM = "mammoth._mixins._text_ops.TextOpsMixin.text_transform"
_BULK_REPLACE = "mammoth._mixins._text_ops.TextOpsMixin.bulk_replace"
_PROJECTS_CREATE = "mammoth.api.projects.ProjectsAPI.create"
_SKILL_INSTALL = "mammoth_cli.skills.installer.install"


def _field(symbol: str, name: str):
    spec = arg_spec(symbol)
    assert spec is not None
    return next(field for field in spec.fields if field.name == name)


def test_enum_field_exposes_its_member_values() -> None:
    """An ``Optional[TextCase]`` field reports TextCase's real member values."""
    field = _field(_TEXT_TRANSFORM, "case")
    assert field.type_name == "TextCase"
    assert field.enum_values == ["UPPER", "LOWER", "TITLE"]


def test_non_enum_field_has_no_enum_values() -> None:
    field = _field(_TEXT_TRANSFORM, "trim")
    assert field.enum_values is None


def test_scalar_field_type_names() -> None:
    """Plain scalar annotations render as their builtin type name."""
    assert _field(_PROJECTS_CREATE, "name").type_name == "str"
    assert _field(_PROJECTS_CREATE, "workspace_id").type_name == "int"


def test_list_of_dataclass_field_exposes_the_structured_type_name() -> None:
    """``list[BulkReplaceMapping]`` renders with its element type, not opaquely."""
    field = _field(_BULK_REPLACE, "mapping")
    assert field.type_name == "list[BulkReplaceMapping]"


def test_optional_field_default_is_reported() -> None:
    field = _field(_PROJECTS_CREATE, "color")
    assert field.required is False
    assert field.has_default is True
    assert field.default_value is None


def test_bool_field_default_is_reported() -> None:
    """A concrete (non-None) default renders as its real JSON-safe value."""
    field = _field(_SKILL_INSTALL, "force")
    assert field.type_name == "bool"
    assert field.has_default is True
    assert field.default_value is False


def test_required_field_has_no_default() -> None:
    field = _field(_PROJECTS_CREATE, "name")
    assert field.required is True
    assert field.has_default is False
    assert field.default_value is None


def test_unwrap_optional_removes_the_none_member() -> None:
    field = _field(_TEXT_TRANSFORM, "case")
    assert unwrap_optional(field.annotation) is not None
    assert render_type_name(unwrap_optional(field.annotation)) == "TextCase"


def test_unwrap_optional_passes_through_non_optional() -> None:
    assert unwrap_optional(int) is int
    assert unwrap_optional(None) is None
